import type { ReviewSubmissionInput } from "../shared/recruitmeReview";

/** The portal registration fields the intake needs; nothing private leaves the portal. */
export type PortalApplicantRow = {
  id: number;
  fullName: string;
  email?: string | null;
  resumeUrl?: string | null;
  createdAt: Date | string;
};

export type Opening = { role: string; title?: string; runId?: string | null };

/**
 * Pure mapping from a Candidate Portal registration to a review-form submission.
 * The worker (recruitme/applicants.py, review.py) validates it again and marks the
 * seeking signal verified by the portal timestamp; other claims stay inferred.
 */
export function applicantSubmission(
  row: PortalApplicantRow,
  opening: Opening,
  portalBaseUrl: string
): ReviewSubmissionInput {
  const created =
    row.createdAt instanceof Date ? row.createdAt : new Date(row.createdAt);
  if (Number.isNaN(created.getTime()))
    throw new Error("Applicant createdAt is not a valid timestamp");
  const day = created.toISOString().slice(0, 10);
  const base = portalBaseUrl.replace(/\/$/, "");
  const notes = [
    `Applied through the ECI Candidate Portal at ${created.toISOString()}.`,
  ];
  if (row.email) notes.push("Applicant supplied an email address (held in the portal, not exported).");
  if (row.resumeUrl) notes.push("Résumé uploaded to the portal.");
  return {
    identity_key: `portal:${row.id}`,
    name: row.fullName.trim(),
    source_url: `${base}/admin/results#candidate-${row.id}`,
    source_type: "first_party_submission",
    channel: "candidate_portal",
    role: opening.role,
    location: "Not stated on application",
    years_experience: null,
    field_experience_confirmed: null,
    statement_excerpt: `Applied for ${opening.title ?? opening.role} through the ECI Candidate Portal on ${day}.`,
    statement_date: day,
    date_basis: "application",
    signal_polarity: "POSITIVE_SEEKING",
    signal_source_url: null,
    identity_confidence: "probable",
    contradictions_checked: true,
    contact_url: null,
    decision: "APPLICANT",
    notes: notes.join(" "),
    run_id: opening.runId ?? null,
    excerpts: {
      name: `Applicant entered name: ${row.fullName.trim()}`,
      role: `Applied for: ${opening.role}`,
      location: "The portal registration does not collect a location",
    },
  };
}
