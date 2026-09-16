import type { inferRouterOutputs } from "@trpc/server";
import type { recruitmeRouter } from "../../../server/recruitme";

export type Workspace = inferRouterOutputs<typeof recruitmeRouter>["workspace"];
export const workflowStatuses = [
  "New",
  "Review",
  "Qualified",
  "Contacted",
  "Interview",
  "Rejected",
  "Hired",
] as const;
export type WorkflowStatus = (typeof workflowStatuses)[number];
/** Optional presentation contract. Values must come from the backend, never inferred from a grade. */
export type Candidate = Workspace["candidates"][number] & {
  currentRole?: string | null;
  yearsExperience?: number | null;
  qualificationScore?: number | null;
  confidence?: string | null;
  qualificationReason?: string | null;
  status?: WorkflowStatus;
  evidenceLinks?: { label: string; url: string }[];
  contactRoutes?: { label: string; url: string }[];
};
export function safeLink(value: string, contact = false): string | undefined {
  try {
    const url = new URL(value);
    if (url.username || url.password) return;
    if (url.protocol === "https:" || url.protocol === "http:") return url.href;
    if (
      contact &&
      ["mailto:", "tel:"].includes(url.protocol) &&
      !/[\r\n]|%0[ad]/i.test(value)
    )
      return url.href;
  } catch {
    /* Unusable evidence stays visible as text. */
  }
}
export function signalFreshness(value: string | null, now = Date.now()) {
  if (!value) return "Date unconfirmed";
  const date = Date.parse(value);
  if (!Number.isFinite(date)) return "Date unconfirmed";
  const days = Math.floor((now - date) / 86400000);
  if (days < 0) return "Future date · verify";
  return `${days === 0 ? "Today" : `${days} days ago`} · ${days <= 30 ? "Within 30 days" : "Older than 30 days"}`;
}
export function candidateKey(candidate: Candidate) {
  return JSON.stringify([candidate.runId, candidate.id]);
}
export function filterCandidates(
  candidates: Candidate[],
  query: string,
  status: string,
  runId: string,
  overrides: Record<string, WorkflowStatus>
) {
  const words = query.toLowerCase().trim().split(/\s+/);
  return candidates.filter(c => {
    const text = [
      c.name,
      c.location,
      c.currentRole,
      c.yearsExperience == null ? "" : `${c.yearsExperience} years`,
      c.fieldEvidence,
      c.recruitingEvidence,
    ]
      .join(" ")
      .toLowerCase();
    return (
      words.every(word => text.includes(word)) &&
      (!status ||
        (overrides[candidateKey(c)] ?? c.status ?? "New") === status) &&
      (!runId || c.runId === runId)
    );
  });
}
