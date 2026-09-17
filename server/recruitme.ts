import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { adminProcedure, router } from "./_core/trpc";
import {
  initialProfile,
  jobProfileSchema,
  type JobProfile,
} from "../shared/recruitme";
import { sourceCatalog } from "../shared/recruitmeSources";
import {
  reviewReceiptSchema,
  reviewSubmissionSchema,
} from "../shared/recruitmeReview";
import { readSnapshot, snapshotSchema } from "./recruitmeSnapshot";
import { applicantSubmission } from "./recruitmeApplicants";

// One server process owns this small POC store. Worker budgets remain authoritative
// on EC2; these editable profile preferences can never change its ledger.
const storeSchema = z.object({
  profiles: z.array(jobProfileSchema),
  audit: z.array(
    z.object({
      at: z.string(),
      actor: z.number(),
      action: z.string(),
      profileId: z.string(),
    })
  ),
  statuses: z
    .record(
      z.string(),
      z.enum([
        "New",
        "Review",
        "Qualified",
        "Contacted",
        "Interview",
        "Rejected",
        "Hired",
      ])
    )
    .default({}),
  workflowAudit: z
    .array(
      z.object({
        at: z.string(),
        actor: z.number(),
        key: z.string(),
        status: z.string(),
      })
    )
    .default([]),
  /** Highest portal candidate id already forwarded to the worker as an applicant. */
  applicantWatermark: z.number().int().nonnegative().default(0),
  reviewAudit: z
    .array(
      z.object({
        at: z.string(),
        actor: z.number(),
        identityKey: z.string(),
        decision: z.string(),
        accepted: z.boolean(),
        candidateId: z.string().nullable(),
        classification: z.string().nullable(),
      })
    )
    .default([]),
});

function location() {
  return process.env.RECRUITME_WEB_STATE_DIR || path.resolve(".recruitme-web");
}

function getBridgeConfig() {
  return {
    enabled:
      process.env.RECRUITME_BRIDGE_ENABLED === "1" ||
      process.env.RECRUITME_BRIDGE_ENABLED?.toLowerCase() === "true",
    launchCommand: parseCommand(process.env.RECRUITME_BRIDGE_LAUNCH_CMD),
    stopCommand: parseCommand(process.env.RECRUITME_BRIDGE_STOP_CMD),
    statusCommand: parseCommand(process.env.RECRUITME_BRIDGE_STATUS_CMD),
    connectCommand: parseCommand(process.env.RECRUITME_BRIDGE_CONNECT_CMD),
    reviewCommand: parseCommand(process.env.RECRUITME_BRIDGE_REVIEW_CMD),
    snapshotCommand: parseCommand(process.env.RECRUITME_BRIDGE_SNAPSHOT_CMD),
    allowedProfileIds: new Set(
      (process.env.RECRUITME_BRIDGE_ALLOWED_PROFILE_IDS || "")
        .split(",")
        .map(v => v.trim())
        .filter(Boolean)
    ),
  };
}

function parseCommand(raw?: string) {
  if (!raw) return undefined;
  try {
    const value = JSON.parse(raw);
    if (Array.isArray(value) && value.length >= 1) {
      return { command: String(value[0]), args: value.slice(1).map(String) };
    }
  } catch {
    return { command: raw, args: [] };
  }
  return undefined;
}

function extractLastJsonLine(stdout: string) {
  const lines = stdout
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .reverse();
  for (const line of lines) {
    try {
      return JSON.parse(line);
    } catch {
      // keep looking for JSON in the next candidate line
    }
  }
  return null;
}

function runBridgeCommand(
  kind: "launch" | "stop" | "status" | "activate_apollo" | "review",
  payload: unknown
) {
  const cfg = getBridgeConfig();
  const command =
    kind === "activate_apollo"
      ? cfg.connectCommand
      : kind === "review"
        ? cfg.reviewCommand
        : kind === "launch"
          ? cfg.launchCommand
          : kind === "stop"
            ? cfg.stopCommand
            : cfg.statusCommand;
  if (!cfg.enabled || !command) {
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message:
        "RecruitMe control bridge is not enabled. Set RECRUITME_BRIDGE_ENABLED and the required RECRUITME_BRIDGE_*_CMD values.",
    });
  }
  const validated =
    kind === "launch"
      ? launchPayloadSchema.parse(payload)
      : kind === "stop"
        ? stopPayloadSchema.parse(payload)
        : kind === "activate_apollo"
          ? z.object({ action: z.literal("activate_apollo") }).parse(payload)
          : kind === "review"
            ? reviewPayloadSchema.parse(payload)
            : statusPayloadSchema.parse(payload);

  const result = spawnSync(command.command, command.args, {
    input: JSON.stringify(validated),
    encoding: "utf8",
    cwd: location(),
    timeout: 120_000,
    env: {
      ...process.env,
      RECRUITME_WEB_STATE_DIR: location(),
      RECRUITME_REQUEST_JSON: JSON.stringify(validated),
    },
  });

  if (result.error) {
    throw new TRPCError({
      code: "INTERNAL_SERVER_ERROR",
      message: `${kind} command failed or timed out. Refresh worker status before retrying a launch.`,
    });
  }
  if (result.status !== 0) {
    throw new TRPCError({
      code: "BAD_REQUEST",
      message: `${kind} command exited with ${result.status}. Refresh worker status before retrying a launch.`,
    });
  }

  const output = extractLastJsonLine(result.stdout || "");
  if (!output) {
    throw new TRPCError({
      code: "BAD_REQUEST",
      message: `${kind} bridge returned non-JSON output.`,
    });
  }
  return output;
}

function bridgeConnectionSummary() {
  const snapshot = readSnapshot();
  const cfg = getBridgeConfig();
  if (!cfg.enabled) {
    return {
      ready: false,
      label: "Control bridge disabled",
      detail:
        "Set RECRUITME_BRIDGE_ENABLED=true and RECRUITME_BRIDGE_*_CMD before enabling live launches.",
    };
  }
  if (!cfg.launchCommand || !cfg.statusCommand || !cfg.stopCommand) {
    return {
      ready: false,
      label: "Control bridge incomplete",
      detail:
        "Configure launch, status, and stop commands before enabling a controlled search.",
    };
  }
  if (!snapshot) {
    return {
      ready: false,
      label: "Worker snapshot missing",
      detail:
        "No worker snapshot was found yet. Sync the snapshot file before launch.",
    };
  }
  if (snapshot.stale) {
    return {
      ready: false,
      label: "Worker snapshot stale",
      detail: `Last snapshot was ${snapshot.generatedAt}. Refresh before new launches.`,
    };
  }
  return {
    ready: true,
    label: "Control bridge ready",
    detail: `Connected to worker snapshot at ${snapshot.generatedAt}.`,
  };
}

function enforceProfileAllowlist(profile: JobProfile) {
  const cfg = getBridgeConfig();
  if (cfg.allowedProfileIds.size === 0) return;
  if (!cfg.allowedProfileIds.has(profile.id)) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "This profile is not in RECRUITME_BRIDGE_ALLOWED_PROFILE_IDS.",
    });
  }
}

function readStore() {
  const filename = path.join(location(), "profiles.json");
  if (!fs.existsSync(filename))
    return storeSchema.parse({ profiles: [initialProfile], audit: [] });
  return storeSchema.parse(JSON.parse(fs.readFileSync(filename, "utf8")));
}

export function saveProfile(profile: JobProfile, actor: number) {
  const store = readStore();
  const existing = store.profiles.find(p => p.id === profile.id);
  if (
    (existing && existing.revision !== profile.revision) ||
    (!existing && profile.revision !== 0)
  ) {
    throw new TRPCError({
      code: "CONFLICT",
      message: "This profile changed. Refresh before saving.",
    });
  }
  const saved = { ...profile, revision: profile.revision + 1 };
  store.profiles = [...store.profiles.filter(p => p.id !== saved.id), saved];
  store.audit.push({
    at: new Date().toISOString(),
    actor,
    action: "PROFILE_SAVED",
    profileId: saved.id,
  });
  fs.mkdirSync(location(), { recursive: true, mode: 0o700 });
  const temp = path.join(location(), `${randomUUID()}.tmp`);
  fs.writeFileSync(temp, JSON.stringify(store), { mode: 0o600, flag: "wx" });
  fs.renameSync(temp, path.join(location(), "profiles.json"));
  return saved;
}

const launchPayloadSchema = z.object({
  action: z.literal("launch"),
  profileId: z.string().uuid(),
  profile: jobProfileSchema,
  workspaceDir: z.string(),
  requestedAt: z.string(),
});
const stopPayloadSchema = z.object({
  action: z.literal("stop"),
  runId: z.string().min(1),
  workspaceDir: z.string(),
  requestedAt: z.string(),
});
const statusPayloadSchema = z.object({
  action: z.literal("status"),
  workspaceDir: z.string(),
  requestedAt: z.string(),
});
const reviewPayloadSchema = z.object({
  action: z.literal("review"),
  submission: reviewSubmissionSchema,
  workspaceDir: z.string(),
  requestedAt: z.string(),
});

function writeStore(store: z.infer<typeof storeSchema>) {
  fs.mkdirSync(location(), { recursive: true, mode: 0o700 });
  const temp = path.join(location(), `${randomUUID()}.tmp`);
  fs.writeFileSync(temp, JSON.stringify(store), { mode: 0o600, flag: "wx" });
  fs.renameSync(temp, path.join(location(), "profiles.json"));
}
const bridgeLaunchOutputSchema = z.object({
  accepted: z.literal(true),
  runId: z.string().min(1),
  status: z.string().max(100),
  message: z.string().max(500).optional(),
  profileId: z.string().uuid().optional(),
});
const bridgeStopOutputSchema = z.object({
  accepted: z.boolean(),
  runId: z.string().min(1),
  status: z.string().max(100).optional(),
  message: z.string().max(500).optional(),
});
const bridgeStatusOutputSchema = z.object({
  online: z.boolean(),
  status: z.string().max(120),
  activeRunId: z.string().nullable(),
  startedAt: z.string().nullable(),
  running: z.boolean(),
  detail: z.string().max(600).optional(),
  lastUpdated: z.string().nullable(),
  meter: snapshotSchema.optional(),
});

export const recruitmeRouter = router({
  setCandidateStatus: adminProcedure
    .input(
      z.object({
        key: z.string().max(400),
        status: z.enum([
          "New",
          "Review",
          "Qualified",
          "Contacted",
          "Interview",
          "Rejected",
          "Hired",
        ]),
        expectedStatus: z.enum([
          "New",
          "Review",
          "Qualified",
          "Contacted",
          "Interview",
          "Rejected",
          "Hired",
        ]),
      })
    )
    .mutation(({ input, ctx }) => {
      const candidate = readSnapshot()?.candidates.find(
        c => JSON.stringify([c.runId, c.id]) === input.key
      );
      if (!candidate)
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Candidate is no longer in the synchronized workspace.",
        });
      const store = readStore();
      if ((store.statuses[input.key] ?? "New") !== input.expectedStatus)
        throw new TRPCError({
          code: "CONFLICT",
          message: "Candidate status changed. Refresh before saving.",
        });
      store.statuses[input.key] = input.status;
      store.workflowAudit.push({
        at: new Date().toISOString(),
        actor: ctx.user.id,
        key: input.key,
        status: input.status,
      });
      fs.mkdirSync(location(), { recursive: true, mode: 0o700 });
      const temp = path.join(location(), `${randomUUID()}.tmp`);
      fs.writeFileSync(temp, JSON.stringify(store), {
        mode: 0o600,
        flag: "wx",
      });
      fs.renameSync(temp, path.join(location(), "profiles.json"));
      return { key: input.key, status: input.status };
    }),
  connectApollo: adminProcedure
    .input(z.object({ apiKey: z.string().min(8).max(512).regex(/^\S+$/) }))
    .mutation(({ input }) => {
      const cfg = getBridgeConfig();
      if (!cfg.enabled || !cfg.connectCommand)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: "Apollo connection setup is not enabled on this server.",
        });
      fs.mkdirSync(location(), { recursive: true, mode: 0o700 });
      const temp = path.join(location(), `${randomUUID()}.credential.tmp`);
      try {
        fs.writeFileSync(
          temp,
          JSON.stringify({
            Name: "/recruitme/providers/apollo/api-key",
            Value: input.apiKey,
            Type: "SecureString",
            Overwrite: true,
          }),
          { mode: 0o600, flag: "wx" }
        );
        const result = spawnSync(
          "aws",
          [
            "ssm",
            "put-parameter",
            "--region",
            process.env.RECRUITME_AWS_REGION || "us-east-2",
            "--cli-input-json",
            `file://${temp}`,
            "--output",
            "json",
            "--no-cli-pager",
          ],
          { encoding: "utf8", timeout: 30000 }
        );
        if (result.error || result.status !== 0)
          throw new TRPCError({
            code: "INTERNAL_SERVER_ERROR",
            message:
              "Could not store the encrypted Apollo credential. Check server permissions.",
          });
      } finally {
        if (fs.existsSync(temp)) fs.unlinkSync(temp);
      }
      const result = z
        .object({ connected: z.literal(true), provider: z.literal("apollo") })
        .parse(
          runBridgeCommand("activate_apollo", { action: "activate_apollo" })
        );
      return result;
    }),
  submitReview: adminProcedure
    .input(reviewSubmissionSchema)
    .mutation(({ input, ctx }) => {
      const cfg = getBridgeConfig();
      if (!cfg.enabled || !cfg.reviewCommand)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message:
            "Reviewed-candidate import is not enabled on this server. Set RECRUITME_BRIDGE_REVIEW_CMD.",
        });
      // The submission is stored by the worker under its own evidence and
      // qualification rules; the reviewer's identity travels with it for audit.
      const payload = reviewPayloadSchema.parse({
        action: "review",
        submission: { ...input, reviewer: `staff-${ctx.user.id}` },
        workspaceDir: location(),
        requestedAt: new Date().toISOString(),
      });
      const receipt = reviewReceiptSchema.parse(
        runBridgeCommand("review", payload)
      );
      const store = readStore();
      store.reviewAudit.push({
        at: new Date().toISOString(),
        actor: ctx.user.id,
        identityKey: input.identity_key,
        decision: input.decision,
        accepted: receipt.accepted,
        candidateId: receipt.candidateId ?? null,
        classification: receipt.classification ?? null,
      });
      writeStore(store);
      return receipt;
    }),
  importApplicants: adminProcedure
    .input(
      z.object({
        role: z.string().trim().min(2).max(300),
        title: z.string().trim().max(200).optional(),
        runId: z.string().max(100).nullable().default(null),
        limit: z.number().int().min(1).max(50).default(25),
      })
    )
    .mutation(async ({ input, ctx }) => {
      const cfg = getBridgeConfig();
      if (!cfg.enabled || !cfg.reviewCommand)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message:
            "Reviewed-candidate import is not enabled on this server. Set RECRUITME_BRIDGE_REVIEW_CMD.",
        });
      const base = process.env.RECRUITME_PORTAL_BASE_URL;
      if (!base)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: "Set RECRUITME_PORTAL_BASE_URL to the public Candidate Portal address.",
        });
      const { listCandidatesAfter } = await import("./db");
      const store = readStore();
      const rows = await listCandidatesAfter(store.applicantWatermark, input.limit);
      if (rows === null)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: "Candidate Portal database is not available on this server.",
        });
      const results: { candidatePortalId: number; accepted: boolean; classification: string | null; errors: string[] }[] = [];
      let watermark = store.applicantWatermark;
      for (const row of rows) {
        const submission = reviewSubmissionSchema.parse({
          ...applicantSubmission(row, { role: input.role, title: input.title, runId: input.runId }, base),
          reviewer: `portal-intake-by-staff-${ctx.user.id}`,
        });
        const payload = reviewPayloadSchema.parse({
          action: "review",
          submission,
          workspaceDir: location(),
          requestedAt: new Date().toISOString(),
        });
        const receipt = reviewReceiptSchema.parse(runBridgeCommand("review", payload));
        results.push({
          candidatePortalId: row.id,
          accepted: receipt.accepted,
          classification: receipt.classification ?? null,
          errors: receipt.errors ?? [],
        });
        store.reviewAudit.push({
          at: new Date().toISOString(),
          actor: ctx.user.id,
          identityKey: submission.identity_key,
          decision: "APPLICANT",
          accepted: receipt.accepted,
          candidateId: receipt.candidateId ?? null,
          classification: receipt.classification ?? null,
        });
        // Advance past stored rows only; a rejected row is retried on the next import.
        if (receipt.accepted) watermark = Math.max(watermark, row.id);
        else break;
      }
      store.applicantWatermark = watermark;
      writeStore(store);
      return { imported: results.filter(r => r.accepted).length, results, watermark };
    }),
  workspace: adminProcedure.query(() => {
    const snapshot = readSnapshot();
    const connection = bridgeConnectionSummary();
    return {
      ...readStore(),
      connection: {
        ...connection,
        bridge: {
          enabled: getBridgeConfig().enabled,
          apolloSetupReady:
            getBridgeConfig().enabled &&
            Boolean(getBridgeConfig().connectCommand),
          reviewReady:
            getBridgeConfig().enabled &&
            Boolean(getBridgeConfig().reviewCommand),
          snapshotPath: path.join(location(), "worker-snapshot.json"),
        },
      },
      budgets: {
        sessionCeiling: 25,
        pocCeiling: 100,
        enrichmentCutoff: 20,
        sessionSpend: null,
        pocSpend: snapshot?.pocSpend ?? null,
      },
      runs: snapshot?.runs ?? [],
      candidates: snapshot?.candidates ?? [],
      snapshotAt: snapshot?.generatedAt ?? null,
      candidatesTruncated: snapshot?.candidatesTruncated ?? false,
      credits: snapshot?.credits ?? [],
      sources: sourceCatalog.map(s => ({
        ...s,
        worker: snapshot?.providers.find(p => p.id === s.id) ?? null,
      })),
    };
  }),
  saveProfile: adminProcedure
    .input(jobProfileSchema)
    .mutation(({ input, ctx }) => saveProfile(input, ctx.user.id)),
  launch: adminProcedure
    .input(z.object({ profileId: z.string().uuid() }))
    .mutation(({ input }) => {
      const state = readStore();
      const profile = state.profiles.find(p => p.id === input.profileId);
      if (!profile)
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Profile not found.",
        });
      enforceProfileAllowlist(profile);
      const connection = bridgeConnectionSummary();
      if (!connection.ready)
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: connection.label + ": " + connection.detail,
        });
      const payload = launchPayloadSchema.parse({
        action: "launch",
        profileId: profile.id,
        profile,
        workspaceDir: location(),
        requestedAt: new Date().toISOString(),
      });
      const output = bridgeLaunchOutputSchema.parse(
        runBridgeCommand("launch", payload)
      );
      return { action: "launch", ...output, profileId: profile.id };
    }),
  stop: adminProcedure
    .input(z.object({ runId: z.string().min(1) }))
    .mutation(({ input }) => {
      // A stale or missing snapshot must never prevent an operator from stopping work.
      const payload = stopPayloadSchema.parse({
        action: "stop",
        runId: input.runId,
        workspaceDir: location(),
        requestedAt: new Date().toISOString(),
      });
      const output = bridgeStopOutputSchema.parse(
        runBridgeCommand("stop", payload)
      );
      return { action: "stop", ...output };
    }),
  status: adminProcedure.query(() => {
    const connection = bridgeConnectionSummary();
    const cfg = getBridgeConfig();
    if (!cfg.enabled || !cfg.statusCommand) {
      return {
        action: "status",
        connection,
        online: false,
        status: "DISABLED",
        activeRunId: null,
        running: false,
        startedAt: null,
        lastUpdated: null,
      };
    }
    const payload = statusPayloadSchema.parse({
      action: "status",
      workspaceDir: location(),
      requestedAt: new Date().toISOString(),
    });
    const output = bridgeStatusOutputSchema.parse(
      runBridgeCommand("status", payload)
    );
    if (output.meter) {
      const previous = readSnapshot();
      const currentIds = new Set(output.meter.runs.map(run => run.id));
      const meter = {
        ...output.meter,
        candidates: output.meter.candidateSnapshotIncluded
          ? output.meter.candidates
          : (previous?.candidates ?? []),
        candidatesTruncated: output.meter.candidateSnapshotIncluded
          ? output.meter.candidatesTruncated
          : previous?.candidatesTruncated,
        runs: [
          ...output.meter.runs,
          ...(previous?.runs ?? []).filter(run => !currentIds.has(run.id)),
        ].slice(0, 100),
      };
      fs.mkdirSync(location(), { recursive: true, mode: 0o700 });
      const temp = path.join(location(), `${randomUUID()}.tmp`);
      fs.writeFileSync(temp, JSON.stringify(meter), {
        mode: 0o600,
        flag: "wx",
      });
      fs.renameSync(temp, path.join(location(), "worker-snapshot.json"));
    }
    return {
      action: "status",
      online: output.online,
      status: output.status,
      activeRunId: output.activeRunId,
      startedAt: output.startedAt,
      running: output.running,
      detail: output.detail,
      lastUpdated: output.lastUpdated,
      connection,
    };
  }),
});
