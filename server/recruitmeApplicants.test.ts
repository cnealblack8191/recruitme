import { describe, expect, it } from "vitest";
import { applicantSubmission } from "./recruitmeApplicants";
import { reviewSubmissionSchema } from "../shared/recruitmeReview";

describe("Candidate Portal applicant intake", () => {
  it("maps a registration to a verified-signal applicant submission without private data", () => {
    const s = applicantSubmission(
      { id: 42, fullName: " Sam Applicant ", email: "sam@example.org", resumeUrl: "https://s3/x.pdf", createdAt: new Date("2026-09-16T14:05:00Z") },
      { role: "Commercial electrician", title: "Commercial Electrician — Doraville", runId: "web-abc" },
      "https://hire.ecinc.us/"
    );
    expect(s).toMatchObject({
      identity_key: "portal:42",
      name: "Sam Applicant",
      source_url: "https://hire.ecinc.us/admin/results#candidate-42",
      source_type: "first_party_submission",
      channel: "candidate_portal",
      date_basis: "application",
      statement_date: "2026-09-16",
      signal_polarity: "POSITIVE_SEEKING",
      identity_confidence: "probable",
      decision: "APPLICANT",
      run_id: "web-abc",
    });
    expect(JSON.stringify(s)).not.toContain("sam@example.org");
    expect(reviewSubmissionSchema.safeParse(s).success).toBe(true);
    expect(() =>
      applicantSubmission({ id: 1, fullName: "x", createdAt: "nope" }, { role: "Electrician" }, "https://hire.ecinc.us")
    ).toThrow();
  });
});
