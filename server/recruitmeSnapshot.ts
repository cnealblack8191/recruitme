import fs from "node:fs";
import path from "node:path";
import { z } from "zod";

const publicUrl = z
  .string()
  .max(2000)
  .refine(s => {
    try {
      const u = new URL(s);
      return (
        ["https:", "http:"].includes(u.protocol) && !u.username && !u.password
      );
    } catch {
      return false;
    }
  });
const sourceLink = z.object({ label: z.string().max(1000), url: publicUrl });
const candidateSchema = z.object({
  id: z.string().max(200),
  runId: z.string().max(100),
  name: z.string().max(200),
  sourceUrl: publicUrl,
  classification: z.string().max(100),
  grade: z.enum(["A", "B", "C", "D"]).nullable(),
  verified: z.boolean(),
  fieldEvidence: z.string().max(3000),
  recruitingEvidence: z.string().max(3000),
  signalDate: z.string().nullable(),
  signalEvidence: z.string().max(3000),
  location: z.string().max(300),
  currentRole: z.string().max(600).nullable().optional(),
  yearsExperience: z.number().min(0).max(80).nullable().optional(),
  qualificationScore: z.number().min(0).max(100).nullable().optional(),
  confidence: z.string().max(200).nullable().optional(),
  qualificationReason: z.string().max(3000).nullable().optional(),
  evidenceLinks: z.array(sourceLink).max(50).optional(),
  contactRoutes: z.array(sourceLink).max(20).optional(),
  reviewDecision: z.enum(["A", "B", "FIT_POOL", "REJECT"]).nullable().optional(),
  reviewer: z.string().max(120).nullable().optional(),
});
export const snapshotSchema = z.object({
  generatedAt: z.string().datetime({ offset: true }),
  pocSpend: z.number().nonnegative(),
  candidateSnapshotIncluded: z.boolean().optional(),
  candidatesTruncated: z.boolean().optional(),
  credits: z
    .array(
      z.object({
        id: z.string().max(80),
        remaining: z.number().nonnegative().nullable(),
        limit: z.number().nonnegative().nullable(),
        unit: z.enum(["credits", "searches", "USD"]),
        basis: z.enum(["provider", "local", "unavailable"]),
        checkedAt: z.string().datetime({ offset: true }).nullable(),
        renewsAt: z.string().max(50).nullable(),
        note: z.string().max(500),
      })
    )
    .max(20)
    .default([]),
  runs: z
    .array(
      z.object({
        id: z.string().max(100),
        status: z.string().max(100),
        createdAt: z.string(),
        spend: z.number().nonnegative(),
        cap: z.number().nonnegative().optional(),
        reserved: z.number().nonnegative().optional(),
        providerSpend: z
          .array(z.object({ id: z.string(), spend: z.number().nonnegative() }))
          .optional(),
        pages: z.number().nonnegative(),
        verified: z.number().nonnegative(),
        stopReason: z.string().max(500),
      })
    )
    .max(100),
  candidates: z.array(candidateSchema).max(1000),
  providers: z
    .array(
      z.object({
        id: z.string().max(80),
        enabled: z.boolean(),
        approved: z.boolean(),
        spend: z.number().nonnegative(),
        health: z.string().max(100),
        credentialReady: z.boolean().optional(),
        unitCost: z.number().nonnegative().nullable().optional(),
        runLimit: z.number().nonnegative().optional(),
      })
    )
    .max(50),
});
export function readSnapshot() {
  const filename = path.join(
    process.env.RECRUITME_WEB_STATE_DIR || path.resolve(".recruitme-web"),
    "worker-snapshot.json"
  );
  try {
    if (!fs.existsSync(filename) || fs.statSync(filename).size > 8_000_000)
      return null;
    const snapshot = snapshotSchema.parse(
      JSON.parse(fs.readFileSync(filename, "utf8"))
    );
    const age = Date.now() - Date.parse(snapshot.generatedAt);
    return { ...snapshot, stale: age > 300_000 || age < -60_000 };
  } catch {
    return null;
  }
}
