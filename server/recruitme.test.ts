import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import process from "node:process";
import { randomUUID } from "node:crypto";
import { recruitmeRouter } from "./recruitme";
import { initialProfile } from "../shared/recruitme";
import type { TrpcContext } from "./_core/context";

let dir: string;
const old = process.env.RECRUITME_WEB_STATE_DIR;
const oldBridgeEnabled = process.env.RECRUITME_BRIDGE_ENABLED;
const oldLaunchCmd = process.env.RECRUITME_BRIDGE_LAUNCH_CMD;
const oldStatusCmd = process.env.RECRUITME_BRIDGE_STATUS_CMD;
const oldStopCmd = process.env.RECRUITME_BRIDGE_STOP_CMD;

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "recruitme-web-"));
  process.env.RECRUITME_WEB_STATE_DIR = dir;
  delete process.env.RECRUITME_BRIDGE_ENABLED;
  delete process.env.RECRUITME_BRIDGE_LAUNCH_CMD;
  delete process.env.RECRUITME_BRIDGE_STATUS_CMD;
  delete process.env.RECRUITME_BRIDGE_STOP_CMD;
});

afterEach(() => {
  fs.rmSync(dir, { recursive: true, force: true });
  if (old === undefined) delete process.env.RECRUITME_WEB_STATE_DIR;
  else process.env.RECRUITME_WEB_STATE_DIR = old;
  if (oldBridgeEnabled === undefined)
    delete process.env.RECRUITME_BRIDGE_ENABLED;
  else process.env.RECRUITME_BRIDGE_ENABLED = oldBridgeEnabled;
  if (oldLaunchCmd === undefined)
    delete process.env.RECRUITME_BRIDGE_LAUNCH_CMD;
  else process.env.RECRUITME_BRIDGE_LAUNCH_CMD = oldLaunchCmd;
  if (oldStatusCmd === undefined)
    delete process.env.RECRUITME_BRIDGE_STATUS_CMD;
  else process.env.RECRUITME_BRIDGE_STATUS_CMD = oldStatusCmd;
  if (oldStopCmd === undefined) delete process.env.RECRUITME_BRIDGE_STOP_CMD;
  else process.env.RECRUITME_BRIDGE_STOP_CMD = oldStopCmd;
});

function caller(role?: "admin" | "user") {
  return recruitmeRouter.createCaller({
    user: role ? { id: 1, role } : null,
    req: {},
    res: {},
  } as TrpcContext);
}

function writeFreshSnapshot() {
  const snapshot = {
    generatedAt: new Date().toISOString(),
    pocSpend: 0,
    runs: [],
    candidates: [],
    providers: [],
  };
  fs.writeFileSync(
    path.join(dir, "worker-snapshot.json"),
    JSON.stringify(snapshot)
  );
}

function writeSnapshotBridgeCommand(stdout: object) {
  const payloadPath = path.join(dir, `bridge-${randomUUID()}.cjs`);
  fs.writeFileSync(
    payloadPath,
    `process.stdin.on('data',()=>{});\nconsole.log(JSON.stringify(${JSON.stringify(stdout)}));`,
    { mode: 0o700 }
  );
  return payloadPath;
}

const fixtureProfile = {
  ...initialProfile,
  title: "Accountants",
  roles: "accountant",
  fitTerms: "general ledger",
};

describe("RecruitMe staff workspace", () => {
  it("synchronizes new candidate evidence from status and removes absent rows on a complete refresh", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const meter = {
      generatedAt: new Date().toISOString(),
      pocSpend: 1.25,
      runs: [],
      providers: [],
      candidateSnapshotIncluded: true,
      candidates: [
        {
          id: "new",
          runId: "controlled",
          name: "Synthetic",
          sourceUrl: "https://example.org/person",
          classification: "RESEARCH_ONLY",
          grade: null,
          verified: false,
          fieldEvidence: "Commercial electrician",
          recruitingEvidence: "",
          signalDate: null,
          signalEvidence: "",
          location: "Atlanta, GA",
          qualificationScore: 32,
          evidenceLinks: [
            { label: "INFERRED · source", url: "https://example.org/person" },
          ],
        },
      ],
    };
    const result = {
      online: true,
      status: "RUNNING",
      activeRunId: "controlled",
      startedAt: null,
      running: true,
      lastUpdated: meter.generatedAt,
      meter,
    };
    process.env.RECRUITME_BRIDGE_STATUS_CMD = JSON.stringify([
      process.execPath,
      writeSnapshotBridgeCommand(result),
    ]);
    await caller("admin").status();
    expect((await caller("admin").workspace()).candidates[0]).toMatchObject({
      id: "new",
      qualificationScore: 32,
      evidenceLinks: meter.candidates[0].evidenceLinks,
    });
    process.env.RECRUITME_BRIDGE_STATUS_CMD = JSON.stringify([
      process.execPath,
      writeSnapshotBridgeCommand({
        ...result,
        meter: { ...meter, candidates: [] },
      }),
    ]);
    await caller("admin").status();
    expect((await caller("admin").workspace()).candidates).toEqual([]);
  });
  it("persists workflow status with authorization and conflict protection without verifying evidence", async () => {
    const candidate = {
      id: "candidate-1",
      runId: "run-1",
      name: "Synthetic",
      sourceUrl: "https://example.org/person",
      classification: "RESEARCH_ONLY",
      grade: null,
      verified: false,
      fieldEvidence: "",
      recruitingEvidence: "",
      signalDate: null,
      signalEvidence: "",
      location: "",
    };
    fs.writeFileSync(
      path.join(dir, "worker-snapshot.json"),
      JSON.stringify({
        generatedAt: new Date().toISOString(),
        pocSpend: 0,
        runs: [],
        candidates: [candidate],
        providers: [],
      })
    );
    const input = {
      key: JSON.stringify(["run-1", "candidate-1"]),
      status: "Qualified" as const,
      expectedStatus: "New" as const,
    };
    await expect(
      caller("user").setCandidateStatus(input)
    ).rejects.toMatchObject({ code: "FORBIDDEN" });
    await caller("admin").setCandidateStatus(input);
    const workspace = await caller("admin").workspace();
    expect(workspace.statuses[input.key]).toBe("Qualified");
    expect(workspace.workflowAudit[0]).toMatchObject({
      actor: 1,
      status: "Qualified",
    });
    expect(workspace.candidates[0].verified).toBe(false);
    await expect(
      caller("admin").setCandidateStatus({ ...input, status: "Rejected" })
    ).rejects.toMatchObject({ code: "CONFLICT" });
    await expect(
      caller("admin").setCandidateStatus({ ...input, key: "missing" })
    ).rejects.toMatchObject({ code: "NOT_FOUND" });
    await caller("admin").saveProfile(initialProfile);
    expect((await caller("admin").workspace()).statuses[input.key]).toBe(
      "Qualified"
    );
  });
  it("does not expose child-process secrets in launch errors", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const script = path.join(dir, "failed-bridge.cjs");
    fs.writeFileSync(
      script,
      "console.error('SYNTHETIC_SECRET_MUST_NOT_LEAK'); process.exit(1);"
    );
    process.env.RECRUITME_BRIDGE_LAUNCH_CMD = JSON.stringify([
      process.execPath,
      script,
    ]);
    process.env.RECRUITME_BRIDGE_STATUS_CMD = JSON.stringify([
      process.execPath,
      script,
    ]);
    process.env.RECRUITME_BRIDGE_STOP_CMD = JSON.stringify([
      process.execPath,
      script,
    ]);
    writeFreshSnapshot();
    await expect(
      caller("admin").launch({ profileId: initialProfile.id })
    ).rejects.toMatchObject({
      message:
        "launch command exited with 1. Refresh worker status before retrying a launch.",
    });
  });
  it("denies anonymous and non-admin access", async () => {
    for (const role of [undefined, "user"] as const) {
      await expect(caller(role).workspace()).rejects.toMatchObject({
        code: "FORBIDDEN",
      });
      await expect(
        caller(role).saveProfile(initialProfile)
      ).rejects.toMatchObject({ code: "FORBIDDEN" });
    }
  });

  it("persists profiles and attribution across requests", async () => {
    const saved = await caller("admin").saveProfile(fixtureProfile);
    const state = await caller("admin").workspace();
    expect(state.profiles[0].title).toBe("Accountants");
    expect(saved.revision).toBe(1);
    expect(state.audit[0].actor).toBe(1);
  });

  it("rejects stale edits without losing saved changes", async () => {
    await caller("admin").saveProfile(initialProfile);
    await expect(
      caller("admin").saveProfile(initialProfile)
    ).rejects.toMatchObject({ code: "CONFLICT" });
    expect((await caller("admin").workspace()).audit).toHaveLength(1);
  });

  it("rejects caps over five dollars and runtime over 30 minutes", async () => {
    for (const patch of [{ runCap: 5.01 }, { durationMinutes: 31 }]) {
      await expect(
        caller("admin").saveProfile({ ...initialProfile, ...patch })
      ).rejects.toMatchObject({ code: "BAD_REQUEST" });
    }
  });

  it("persists a zero-dollar search and provider allocations", async () => {
    const saved = await caller("admin").saveProfile({
      ...initialProfile,
      runCap: 0,
      searchProviders: [{ id: "exa_free", budget: 0 }],
    });
    expect(saved.runCap).toBe(0);
    expect(
      (await caller("admin").workspace()).profiles[0].searchProviders
    ).toEqual([{ id: "exa_free", budget: 0 }]);
    await expect(
      caller("admin").saveProfile({
        ...saved,
        searchProviders: [{ id: "tavily", budget: 6 }],
      })
    ).rejects.toMatchObject({ code: "BAD_REQUEST" });
  });

  it("refreshes stale metering from worker status", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const meter = {
      generatedAt: new Date().toISOString(),
      pocSpend: 0.01,
      candidates: [],
      providers: [],
      runs: [
        {
          id: "budget-test",
          status: "RUNNING",
          createdAt: new Date().toISOString(),
          spend: 0.01,
          cap: 0.5,
          reserved: 0.008,
          providerSpend: [{ id: "tavily", spend: 0.01 }],
          pages: 1,
          verified: 0,
          stopReason: "",
        },
      ],
    };
    const command = writeSnapshotBridgeCommand({
      online: true,
      status: "RUNNING",
      activeRunId: "budget-test",
      startedAt: null,
      running: true,
      lastUpdated: meter.generatedAt,
      meter,
    });
    process.env.RECRUITME_BRIDGE_STATUS_CMD = JSON.stringify([
      process.execPath,
      command,
    ]);
    await caller("admin").status();
    expect((await caller("admin").workspace()).runs[0]).toMatchObject({
      spend: 0.01,
      cap: 0.5,
      reserved: 0.008,
    });
  });

  it("fails closed on launch without presenting false live balances", async () => {
    await expect(
      caller("admin").launch({ profileId: initialProfile.id })
    ).rejects.toMatchObject({ code: "PRECONDITION_FAILED" });
    const state = await caller("admin").workspace();
    expect(state.connection.ready).toBe(false);
    expect(state.budgets.pocSpend).toBeNull();
  });

  it("accepts launch when a valid bridge command returns JSON", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const launchPath = writeSnapshotBridgeCommand({
      accepted: true,
      runId: "run-0001",
      status: "QUEUED",
    });
    const statusPath = writeSnapshotBridgeCommand({
      online: true,
      status: "IDLE",
      activeRunId: null,
      startedAt: null,
      running: false,
      detail: "noop",
      lastUpdated: new Date().toISOString(),
    });
    process.env.RECRUITME_BRIDGE_LAUNCH_CMD = JSON.stringify([
      process.execPath,
      launchPath,
    ]);
    process.env.RECRUITME_BRIDGE_STATUS_CMD = JSON.stringify([
      process.execPath,
      statusPath,
    ]);
    process.env.RECRUITME_BRIDGE_STOP_CMD = JSON.stringify([
      process.execPath,
      statusPath,
    ]);
    writeFreshSnapshot();
    const result = await caller("admin").launch({
      profileId: initialProfile.id,
    });
    expect(result).toMatchObject({
      action: "launch",
      runId: "run-0001",
      status: "QUEUED",
      accepted: true,
      profileId: initialProfile.id,
    });
  });

  it("requires status command for status checks", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    process.env.RECRUITME_BRIDGE_LAUNCH_CMD = JSON.stringify([
      process.execPath,
      "unused.cjs",
    ]);
    const result = await caller("admin").status();
    expect(result).toMatchObject({
      action: "status",
      online: false,
      status: "DISABLED",
      running: false,
      activeRunId: null,
    });
  });

  it("allows emergency stop without a snapshot or launch command", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const command = writeSnapshotBridgeCommand({
      accepted: true,
      runId: "run-1",
      status: "STOPPING",
    });
    process.env.RECRUITME_BRIDGE_STOP_CMD = JSON.stringify([
      process.execPath,
      command,
    ]);
    await expect(
      caller("admin").stop({ runId: "run-1" })
    ).resolves.toMatchObject({ accepted: true });
    await expect(caller("user").stop({ runId: "run-1" })).rejects.toMatchObject(
      { code: "FORBIDDEN" }
    );
  });

  it("refuses launch without an emergency stop command", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const command = writeSnapshotBridgeCommand({
      accepted: true,
      runId: "run-1",
      status: "QUEUED",
    });
    process.env.RECRUITME_BRIDGE_STATUS_CMD =
      process.env.RECRUITME_BRIDGE_LAUNCH_CMD = JSON.stringify([
        process.execPath,
        command,
      ]);
    writeFreshSnapshot();
    await expect(
      caller("admin").launch({ profileId: initialProfile.id })
    ).rejects.toMatchObject({ code: "PRECONDITION_FAILED" });
  });
});

describe("RecruitMe reviewed-candidate import", () => {
  const submission = {
    identity_key: "https://www.linkedin.com/in/jane-doe",
    name: "Jane Doe",
    source_url: "https://www.linkedin.com/in/jane-doe",
    role: "Journeyman electrician",
    location: "Chamblee, GA",
    years_experience: 7,
    field_experience_confirmed: true,
    statement_excerpt: "#OpenToWork looking for my next commercial project",
    statement_date: "2026-09-10",
    date_basis: "post_timestamp" as const,
    signal_polarity: "POSITIVE_SEEKING" as const,
    identity_confidence: "confirmed" as const,
    contradictions_checked: true as const,
    decision: "A" as const,
    channel: "linkedin_recruiter" as const,
  };
  it("fails closed without a review bridge command", async () => {
    await expect(
      caller("admin").submitReview(submission)
    ).rejects.toMatchObject({ code: "PRECONDITION_FAILED" });
    await expect(caller("user").submitReview(submission)).rejects.toMatchObject(
      { code: "FORBIDDEN" }
    );
  });
  it("rejects incomplete submissions before contacting the worker", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    process.env.RECRUITME_BRIDGE_REVIEW_CMD = JSON.stringify([
      process.execPath,
      writeSnapshotBridgeCommand({ accepted: true, candidateId: "never" }),
    ]);
    for (const bad of [
      { statement_date: null },
      { contradictions_checked: false },
      { source_url: "javascript:alert(1)" },
      { decision: "C" },
      { signal_polarity: "yes" },
    ]) {
      await expect(
        caller("admin").submitReview({ ...submission, ...bad } as never)
      ).rejects.toMatchObject({ code: "BAD_REQUEST" });
    }
    expect((await caller("admin").workspace()).reviewAudit).toEqual([]);
    delete process.env.RECRUITME_BRIDGE_REVIEW_CMD;
  });
  it("stores the worker receipt and audits the reviewer, including gate failures", async () => {
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    const echo = path.join(dir, "review-echo.cjs");
    fs.writeFileSync(
      echo,
      `let raw='';process.stdin.on('data',d=>raw+=d);process.stdin.on('end',()=>{const p=JSON.parse(raw);const s=p.submission;
       if(p.action!=='review'||s.reviewer!=='staff-1'||s.decision!=='A'){console.log(JSON.stringify({accepted:false,errors:['bad payload '+JSON.stringify(p)]}));return;}
       console.log(JSON.stringify({accepted:true,candidateId:'cand-1',runId:'review-abc',classification:'FULLY_QUALIFIED',score:100,blockers:[],decision:'A'}));});`,
      { mode: 0o700 }
    );
    process.env.RECRUITME_BRIDGE_REVIEW_CMD = JSON.stringify([
      process.execPath,
      echo,
    ]);
    const receipt = await caller("admin").submitReview({
      ...submission,
      reviewer: "spoofed-reviewer",
    });
    expect(receipt).toMatchObject({
      accepted: true,
      candidateId: "cand-1",
      classification: "FULLY_QUALIFIED",
    });
    const rejected = path.join(dir, "review-reject.cjs");
    fs.writeFileSync(
      rejected,
      `process.stdin.on('data',()=>{});console.log(JSON.stringify({accepted:false,runId:'review-def',decision:'A',errors:['A/B import requires full evidence-based commercial qualification: No sufficient verified job-change signal within 30 days']}));`,
      { mode: 0o700 }
    );
    process.env.RECRUITME_BRIDGE_REVIEW_CMD = JSON.stringify([
      process.execPath,
      rejected,
    ]);
    const failed = await caller("admin").submitReview(submission);
    expect(failed.accepted).toBe(false);
    expect(failed.errors?.[0]).toContain("within 30 days");
    const audit = (await caller("admin").workspace()).reviewAudit;
    expect(audit).toHaveLength(2);
    expect(audit[0]).toMatchObject({
      actor: 1,
      decision: "A",
      accepted: true,
      candidateId: "cand-1",
    });
    expect(audit[1]).toMatchObject({ accepted: false, candidateId: null });
    expect((await caller("admin").workspace()).connection.bridge.reviewReady).toBe(true);
    delete process.env.RECRUITME_BRIDGE_REVIEW_CMD;
  });
});

describe("RecruitMe applicant import", () => {
  it("fails closed without bridge, portal address or database", async () => {
    await expect(
      caller("admin").importApplicants({ role: "Commercial electrician" })
    ).rejects.toMatchObject({ code: "PRECONDITION_FAILED" });
    process.env.RECRUITME_BRIDGE_ENABLED = "true";
    process.env.RECRUITME_BRIDGE_REVIEW_CMD = JSON.stringify([process.execPath, writeSnapshotBridgeCommand({ accepted: true, candidateId: "x" })]);
    const oldBase = process.env.RECRUITME_PORTAL_BASE_URL;
    const oldDb = process.env.DATABASE_URL;
    delete process.env.RECRUITME_PORTAL_BASE_URL;
    await expect(
      caller("admin").importApplicants({ role: "Commercial electrician" })
    ).rejects.toMatchObject({ message: expect.stringContaining("RECRUITME_PORTAL_BASE_URL") });
    process.env.RECRUITME_PORTAL_BASE_URL = "https://hire.ecinc.us";
    delete process.env.DATABASE_URL;
    await expect(
      caller("admin").importApplicants({ role: "Commercial electrician" })
    ).rejects.toMatchObject({ message: expect.stringContaining("database is not available") });
    expect((await caller("admin").workspace()).applicantWatermark).toBe(0);
    if (oldBase === undefined) delete process.env.RECRUITME_PORTAL_BASE_URL; else process.env.RECRUITME_PORTAL_BASE_URL = oldBase;
    if (oldDb !== undefined) process.env.DATABASE_URL = oldDb;
    delete process.env.RECRUITME_BRIDGE_REVIEW_CMD;
  });
});
