import { z } from "zod";

/** Controlled vocabularies shared with the worker's recruitme/review.py. */
export const reviewDecisions = ["A", "B", "FIT_POOL", "REJECT"] as const;
export const signalPolarities = [
  "POSITIVE_SEEKING",
  "NEGATIVE_NOT_SEEKING",
  "AMBIGUOUS",
] as const;
export const dateBases = [
  "post_timestamp",
  "resume_updated",
  "application",
  "stated_in_text",
  "unknown",
] as const;
export const identityConfidences = [
  "confirmed",
  "probable",
  "namesake_risk",
] as const;
export const reviewChannels = [
  "discovery",
  "indeed_smart_sourcing",
  "linkedin_recruiter",
  "employ_georgia",
  "ziprecruiter",
  "postjobfree",
  "craigslist",
  "candidate_portal",
  "referral",
  "other",
] as const;
export const sourceTypes = [
  "first_party",
  "official_record",
  "professional_profile",
  "secondary",
  "search_snippet",
] as const;

const publicUrl = z
  .string()
  .trim()
  .max(2000)
  .refine(value => {
    try {
      const url = new URL(value);
      return (
        ["https:", "http:"].includes(url.protocol) &&
        !url.username &&
        !url.password
      );
    } catch {
      return false;
    }
  }, "Must be a public http(s) URL");
const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Use an ISO date (YYYY-MM-DD)");

export const reviewSubmissionSchema = z
  .object({
    identity_key: z.string().trim().min(1).max(400),
    name: z.string().trim().min(1).max(200),
    source_url: publicUrl,
    source_type: z.enum(sourceTypes).default("professional_profile"),
    channel: z.enum(reviewChannels).default("discovery"),
    role: z.string().trim().min(1).max(300),
    location: z.string().trim().min(1).max(300),
    years_experience: z.number().min(0).max(80).nullable().default(null),
    field_experience_confirmed: z.boolean().nullable().default(null),
    statement_excerpt: z.string().trim().min(1).max(3000),
    statement_date: isoDate.nullable().default(null),
    date_basis: z.enum(dateBases),
    signal_polarity: z.enum(signalPolarities),
    signal_source_url: publicUrl.nullable().default(null),
    identity_confidence: z.enum(identityConfidences),
    contradictions_checked: z.literal(true),
    contact_url: publicUrl.nullable().default(null),
    decision: z.enum(reviewDecisions),
    /** Set server-side from the authenticated staff identity; client values are replaced. */
    reviewer: z.string().max(120).optional(),
    notes: z.string().max(2000).default(""),
    run_id: z.string().max(100).nullable().default(null),
    excerpts: z
      .object({
        name: z.string().max(3000).optional(),
        role: z.string().max(3000).optional(),
        location: z.string().max(3000).optional(),
        years_experience: z.string().max(3000).optional(),
        field_experience: z.string().max(3000).optional(),
      })
      .default({}),
    policy: z
      .object({
        maximum_signal_age_days: z.number().int().min(1).max(365).optional(),
        role_kind: z
          .enum(["commercial_electrician", "electrical_recruiter"])
          .optional(),
        years_maximum_is_gate: z.boolean().optional(),
      })
      .optional(),
  })
  .refine(
    value => value.date_basis === "unknown" || Boolean(value.statement_date),
    { message: "Statement date is required unless the date basis is unknown", path: ["statement_date"] }
  );
export type ReviewSubmission = z.infer<typeof reviewSubmissionSchema>;
export type ReviewSubmissionInput = z.input<typeof reviewSubmissionSchema>;

export const reviewReceiptSchema = z.object({
  accepted: z.boolean(),
  candidateId: z.string().max(200).optional(),
  runId: z.string().max(100).optional(),
  originRunId: z.string().max(100).nullable().optional(),
  classification: z.string().max(100).optional(),
  score: z.number().min(0).max(100).optional(),
  blockers: z.array(z.string().max(500)).max(20).optional(),
  decision: z.enum(reviewDecisions).optional(),
  errors: z.array(z.string().max(500)).max(20).optional(),
});
export type ReviewReceipt = z.infer<typeof reviewReceiptSchema>;

export const emptyReviewDraft: ReviewSubmissionInput = {
  identity_key: "",
  name: "",
  source_url: "",
  source_type: "professional_profile",
  channel: "discovery",
  role: "",
  location: "",
  years_experience: null,
  field_experience_confirmed: null,
  statement_excerpt: "",
  statement_date: null,
  date_basis: "post_timestamp",
  signal_polarity: "POSITIVE_SEEKING",
  signal_source_url: null,
  identity_confidence: "confirmed",
  contradictions_checked: true,
  contact_url: null,
  decision: "B",
  notes: "",
  run_id: null,
  excerpts: {},
};
