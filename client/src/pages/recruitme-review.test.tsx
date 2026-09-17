import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import RecruitMeReview from "./RecruitMeReview";
import RecruitMeCandidates from "./RecruitMeCandidates";
import {
  emptyReviewDraft,
  reviewSubmissionSchema,
} from "@shared/recruitmeReview";
import type { Candidate } from "./recruitme-model";

const noop = () => {};

describe("RecruitMe review form", () => {
  it("exposes every controlled field and disables storing when the bridge is off", () => {
    const html = renderToStaticMarkup(
      <RecruitMeReview
        draft={emptyReviewDraft}
        onChange={noop}
        onSubmit={noop}
        onReset={noop}
        enabled={false}
      />
    );
    for (const label of [
      "own statement, verbatim",
      "Date the person made the statement",
      "How you know that date",
      "What the statement means",
      "Identity confidence",
      "Your decision",
      "contradict this one",
    ])
      expect(html).toContain(label);
    expect(html).toContain("Fit pool");
    expect(html).toContain("not enabled on this server");
    expect(html).toMatch(/<button[^>]*disabled[^>]*>Store reviewed candidate/);
  });
  it("shows gate failures from the worker without pretending the record was stored", () => {
    const html = renderToStaticMarkup(
      <RecruitMeReview
        draft={emptyReviewDraft}
        onChange={noop}
        onSubmit={noop}
        onReset={noop}
        enabled
        receipt={{
          accepted: false,
          decision: "A",
          errors: ["No sufficient verified job-change signal within 30 days"],
        }}
      />
    );
    expect(html).toContain("Not stored");
    expect(html).toContain("within 30 days");
    expect(html).toContain("Change the decision to Fit pool");
    const stored = renderToStaticMarkup(
      <RecruitMeReview
        draft={emptyReviewDraft}
        onChange={noop}
        onSubmit={noop}
        onReset={noop}
        enabled
        receipt={{ accepted: true, classification: "PROVISIONAL", score: 62, blockers: ["Relevant experience outside target or unknown"] }}
      />
    );
    expect(stored).toContain("Stored as PROVISIONAL · score 62");
    expect(stored).toContain("Open gates: Relevant experience");
  });
  it("requires a statement date unless the basis is unknown and drops spoofed reviewer names", () => {
    const base = {
      ...emptyReviewDraft,
      identity_key: "k",
      name: "Jane Doe",
      source_url: "https://example.org/jane",
      role: "Electrician",
      location: "Chamblee, GA",
      statement_excerpt: "open to work",
      identity_confidence: "confirmed" as const,
    };
    expect(reviewSubmissionSchema.safeParse(base).success).toBe(false);
    expect(
      reviewSubmissionSchema.safeParse({ ...base, date_basis: "unknown" }).success
    ).toBe(true);
    const parsed = reviewSubmissionSchema.parse({
      ...base,
      statement_date: "2026-09-10",
      reviewer: "someone",
    });
    expect(parsed.reviewer).toBe("someone");
    expect(parsed.channel).toBe("discovery");
  });
  it("offers a review action on discovery records and labels stored decisions", () => {
    const candidate: Candidate = {
      id: "p1",
      runId: "run-1",
      name: "Jordan Example",
      location: "Atlanta",
      sourceUrl: "https://example.com/evidence",
      classification: "RESEARCH_ONLY",
      grade: null,
      verified: false,
      fieldEvidence: "",
      recruitingEvidence: "",
      signalDate: null,
      signalEvidence: "",
      reviewDecision: "FIT_POOL",
    };
    const html = renderToStaticMarkup(
      <RecruitMeCandidates
        data={{ candidates: [candidate], runs: [] } as never}
        statuses={{}}
        onStatusChange={noop}
        onReview={noop}
        loading={false}
        error={false}
        refresh={noop}
      />
    );
    expect(html).toContain("Reviewed · FIT POOL");
  });
});
