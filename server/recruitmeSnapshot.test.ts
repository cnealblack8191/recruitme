import { beforeEach, afterEach, it, expect } from "vitest";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { readSnapshot, snapshotSchema } from "./recruitmeSnapshot";
let dir: string;
const old = process.env.RECRUITME_WEB_STATE_DIR;
beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "rm-snapshot-"));
  process.env.RECRUITME_WEB_STATE_DIR = dir;
});
afterEach(() => {
  fs.rmSync(dir, { recursive: true, force: true });
  if (old === undefined) delete process.env.RECRUITME_WEB_STATE_DIR;
  else process.env.RECRUITME_WEB_STATE_DIR = old;
});
const fixture = {
  generatedAt: "2026-09-11T17:33:00Z",
  pocSpend: 13.929,
  runs: [],
  candidates: [],
  providers: [],
};
it("accepts the UTC offset emitted by the Python worker", () => {
  expect(
    snapshotSchema.parse({
      ...fixture,
      generatedAt: "2026-09-13T00:47:22.713901+00:00",
    })
  ).toHaveProperty("pocSpend", 13.929);
});
it("rejects malformed snapshots without inventing a balance", () => {
  fs.writeFileSync(path.join(dir, "worker-snapshot.json"), "{bad");
  expect(readSnapshot()).toBeNull();
});
it("marks historical results stale and strips unrecognized fields", () => {
  fs.writeFileSync(
    path.join(dir, "worker-snapshot.json"),
    JSON.stringify({ ...fixture, secret: "must-not-leave-server" })
  );
  expect(readSnapshot()).toMatchObject({ pocSpend: 13.929, stale: true });
  expect(readSnapshot()).not.toHaveProperty("secret");
});
it("rejects executable source URLs", () => {
  expect(() =>
    snapshotSchema.parse({
      ...fixture,
      candidates: [
        {
          id: "x",
          runId: "r",
          name: "Test",
          sourceUrl: "javascript:alert(1)",
          classification: "Research",
          grade: null,
          verified: false,
          fieldEvidence: "",
          recruitingEvidence: "",
          signalDate: null,
          signalEvidence: "",
          location: "",
        },
      ],
    })
  ).toThrow();
});
it("preserves qualification and evidence contracts while stripping unknown data", () => {
  const candidate = {
    id: "x",
    runId: "r",
    name: "Synthetic",
    sourceUrl: "https://example.org/person",
    classification: "FULLY_QUALIFIED",
    grade: null,
    verified: true,
    fieldEvidence: "Commercial electrician",
    recruitingEvidence: "",
    signalDate: null,
    signalEvidence: "",
    location: "Atlanta, GA",
    currentRole: "Electrician",
    yearsExperience: 6,
    qualificationScore: 100,
    confidence: "100/100 evidence support",
    qualificationReason: "Human-reviewed evidence",
    evidenceLinks: [
      { label: "VERIFIED_FACT · role", url: "https://example.org/person" },
    ],
    contactRoutes: [
      {
        label: "INFERRED · professional route",
        url: "https://example.org/person",
      },
    ],
    secret: "excluded",
  };
  const row = snapshotSchema.parse({ ...fixture, candidates: [candidate] })
    .candidates[0];
  expect(row).toMatchObject({
    qualificationScore: 100,
    yearsExperience: 6,
    evidenceLinks: candidate.evidenceLinks,
    contactRoutes: candidate.contactRoutes,
  });
  expect(row).not.toHaveProperty("secret");
  expect(() =>
    snapshotSchema.parse({
      ...fixture,
      candidates: [{ ...candidate, qualificationScore: 101 }],
    })
  ).toThrow();
  expect(() =>
    snapshotSchema.parse({
      ...fixture,
      candidates: [
        {
          ...candidate,
          contactRoutes: [{ label: "unsafe", url: "javascript:alert(1)" }],
        },
      ],
    })
  ).toThrow();
});
