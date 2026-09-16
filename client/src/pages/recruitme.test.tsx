import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import RecruitMeCandidates, {
  CandidateDetail,
  EvidenceLink,
} from "./RecruitMeCandidates";
import {
  candidateKey,
  filterCandidates,
  safeLink,
  signalFreshness,
  type Candidate,
  type Workspace,
} from "./recruitme-model";

const candidate: Candidate = {
  id: "person-1",
  runId: "run-1",
  name: "Jordan Example",
  location: "Atlanta",
  sourceUrl: "https://example.com/evidence",
  classification: "Electrical field and recruiting experience",
  grade: "B",
  verified: false,
  fieldEvidence: "Commercial electrical construction",
  recruitingEvidence: "Recruits electricians",
  signalDate: null,
  signalEvidence: "",
};
describe("RecruitMe evidence presentation", () => {
  it("keeps missing scores, confidence, years, role and contacts explicit", () => {
    const html = renderToStaticMarkup(
      <CandidateDetail candidate={candidate} />
    );
    expect(html).toContain("Not provided");
    expect(html).toContain("Recorded grade B");
    expect(html).not.toContain("Score 80");
    expect(html).toContain("Needs review");
    expect(html).toContain("No contact route supplied");
    expect(html).toContain("Commercial electrical construction");
    expect(html).toContain(
      "Search history for this record has not synchronized"
    );
  });
  it("renders supplied enrichment including zero years and score without inventing scale", () => {
    const html = renderToStaticMarkup(
      <CandidateDetail
        candidate={{
          ...candidate,
          currentRole: "Apprentice",
          qualificationScore: 0,
          yearsExperience: 0,
          confidence: "Low",
          qualificationReason: "Relevant apprenticeship",
          contactRoutes: [
            { label: "Email Jordan", url: "mailto:jordan@example.com" },
          ],
        }}
      />
    );
    expect(html).toContain("Apprentice");
    expect(html).toContain("<dd>0</dd>");
    expect(html).toContain("Relevant apprenticeship");
    expect(html).toContain("mailto:jordan@example.com");
  });
  it("shows run budget with reservations included, not an invented candidate cost", () => {
    const html = renderToStaticMarkup(
      <CandidateDetail
        candidate={candidate}
        run={{
          id: "run-1",
          createdAt: "2026-09-13T12:00:00Z",
          status: "completed",
          spend: 2,
          cap: 5,
          reserved: 0.5,
          pages: 10,
          verified: 1,
          stopReason: "",
        }}
      />
    );
    expect(html).toContain("$2.000 committed");
    expect(html).toContain("$5.00 budget");
    expect(html).toContain("$0.500 pending");
    expect(html).toContain("not a per-candidate charge");
  });
  it("escapes research text and blocks unsafe evidence links", () => {
    const html = renderToStaticMarkup(
      <CandidateDetail
        candidate={{
          ...candidate,
          fieldEvidence: "<script>alert(1)</script>",
          sourceUrl: "javascript:alert(1)",
        }}
      />
    );
    expect(html).not.toContain("<script>");
    expect(html).toContain("Link unavailable");
    expect(
      renderToStaticMarkup(
        <EvidenceLink label="Source" url="https://example.com" />
      )
    ).toContain('rel="noopener noreferrer"');
  });
  it("distinguishes loading, errors and empty results", () => {
    const props = { statuses: {}, onStatusChange: () => {}, refresh: () => {} };
    const loading = renderToStaticMarkup(
      <RecruitMeCandidates {...props} loading error={false} />
    );
    expect(loading).toContain("Loading candidate evidence");
    expect(loading).not.toContain("Your candidate workspace is ready");
    const error = renderToStaticMarkup(
      <RecruitMeCandidates {...props} loading={false} error />
    );
    expect(error).toContain("could not refresh");
    expect(error).not.toContain("Your candidate workspace is ready");
    const empty = renderToStaticMarkup(
      <RecruitMeCandidates {...props} loading={false} error={false} />
    );
    expect(empty).toContain("Your candidate workspace is ready");
  });
  it("renders pipeline counts using session changes", () => {
    const html = renderToStaticMarkup(
      <RecruitMeCandidates
        data={{ candidates: [candidate], runs: [] } as unknown as Workspace}
        statuses={{ [candidateKey(candidate)]: "Interview" }}
        onStatusChange={() => {}}
        loading={false}
        error={false}
        refresh={() => {}}
      />
    );
    expect(html).toContain("Interview<b>1</b>");
    expect(html).toContain("New<b>0</b>");
    expect(html).toContain("saved for each candidate and run");
  });
});
describe("RecruitMe filtering and freshness", () => {
  it("combines experience keywords, workflow and discovery run", () => {
    const overrides = { [candidateKey(candidate)]: "Qualified" as const };
    expect(
      filterCandidates(
        [candidate],
        " atlanta electrical ",
        "Qualified",
        "run-1",
        overrides
      )
    ).toEqual([candidate]);
    expect(filterCandidates([candidate], "", "New", "", overrides)).toEqual([]);
    expect(filterCandidates([candidate], "", "", "another-run", {})).toEqual(
      []
    );
    expect(filterCandidates([candidate], "", "New", "", {})).toEqual([
      candidate,
    ]);
  });
  it("isolates repeated candidate IDs between discovery runs", () => {
    expect(candidateKey(candidate)).not.toBe(
      candidateKey({ ...candidate, runId: "run-2" })
    );
  });
  it("marks undated, invalid, future, fresh and old signals explicitly", () => {
    const now = Date.parse("2026-09-13T12:00:00Z");
    expect(signalFreshness(null, now)).toBe("Date unconfirmed");
    expect(signalFreshness("invalid", now)).toBe("Date unconfirmed");
    expect(signalFreshness("2026-09-14", now)).toBe("Future date · verify");
    expect(signalFreshness("2026-08-14T12:00:00Z", now)).toBe(
      "30 days ago · Within 30 days"
    );
    expect(signalFreshness("2026-08-13T12:00:00Z", now)).toBe(
      "31 days ago · Older than 30 days"
    );
  });
  it("restricts contacts and source URLs to usable protocols", () => {
    for (const url of [
      "javascript:alert(1)",
      "data:text/html,test",
      "https://user:pass@example.com",
      "/relative",
    ])
      expect(safeLink(url)).toBeUndefined();
    expect(safeLink("mailto:a@example.com")).toBeUndefined();
    expect(safeLink("tel:+15555550123", true)).toBe("tel:+15555550123");
    expect(
      safeLink("mailto:a@example.com%0d%0abcc:b@example.com", true)
    ).toBeUndefined();
  });
});
