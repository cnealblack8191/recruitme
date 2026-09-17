import { useState } from "react";
import { ArrowUpRight, Search, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from "@/components/ui/dialog";
import {
  candidateKey,
  filterCandidates,
  safeLink,
  signalFreshness,
  workflowStatuses,
  type Candidate,
  type WorkflowStatus,
  type Workspace,
} from "./recruitme-model";

export function EvidenceLink({
  label,
  url,
  contact = false,
}: {
  label: string;
  url: string;
  contact?: boolean;
}) {
  const href = safeLink(url, contact);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {label}
      <ArrowUpRight size={14} aria-hidden="true" />
    </a>
  ) : (
    <span>{label} · Link unavailable</span>
  );
}

export function CandidateDetail({
  candidate: c,
  run,
}: {
  candidate: Candidate;
  run?: Workspace["runs"][number];
}) {
  return (
    <>
      <dl className="rm-facts">
        <div>
          <dt>Most recent role</dt>
          <dd>{c.currentRole || "Not provided"}</dd>
        </div>
        <div>
          <dt>Location</dt>
          <dd>{c.location || "Unconfirmed"}</dd>
        </div>
        <div>
          <dt>Years of experience</dt>
          <dd>{c.yearsExperience ?? "Not provided"}</dd>
        </div>
        <div>
          <dt>Qualification score</dt>
          <dd>
            {c.qualificationScore ?? "Not provided"}
            {c.grade && <small>Recorded grade {c.grade}</small>}
          </dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{c.confidence || "Not provided"}</dd>
        </div>
        <div>
          <dt>Evidence verification</dt>
          <dd>
            {c.verified ? "Required claims human-verified" : "Needs review"}
          </dd>
        </div>
      </dl>
      <section className="rm-rationale">
        <span className="rm-evidence-label">WHY THIS PERSON WAS SURFACED</span>
        <h3>Qualification rationale</h3>
        <p>
          {c.qualificationReason ||
            c.classification ||
            "No qualification summary was provided. Review the recorded evidence below."}
        </p>
        <p className="rm-muted">
          A grade is a research assessment. Confirm the experience and original
          signal before making a recruiting decision.
        </p>
      </section>
      <div className="rm-evidence-columns">
        <section>
          <span className="rm-evidence-label">01 · ROLE FIT</span>
          <h3>Electrical & construction</h3>
          <p>
            {c.fieldEvidence ||
              "Electrical or construction experience has not been established."}
          </p>
        </section>
        <section>
          <span className="rm-evidence-label">02 · CAREER CONTEXT</span>
          <h3>Recruiting & HR experience</h3>
          <p>
            {c.recruitingEvidence ||
              "Recruiting or HR experience has not been established."}
          </p>
        </section>
      </div>
      <section className="rm-signal-detail">
        <span className="rm-evidence-label">03 · JOB-CHANGE SIGNAL</span>
        <h3>Availability & intent</h3>
        <p>
          {c.signalEvidence ||
            "No personal job-change signal has been established."}
        </p>
        <div>
          {c.signalDate || "Original date not provided"} ·{" "}
          {signalFreshness(c.signalDate)}
        </div>
      </section>
      <div className="rm-evidence-columns rm-space">
        <section className="rm-detail-links">
          <h3>Sources & evidence</h3>
          <EvidenceLink
            label="Open original research source"
            url={c.sourceUrl}
          />
          <small>{c.sourceUrl}</small>
          {c.evidenceLinks?.map((link, i) => (
            <EvidenceLink key={i} {...link} />
          ))}
        </section>
        <section className="rm-detail-links">
          <h3>Contact routes</h3>
          {c.contactRoutes?.length ? (
            c.contactRoutes.map((link, i) => (
              <EvidenceLink key={i} {...link} contact />
            ))
          ) : (
            <p>
              No contact route supplied. Review the source for publicly
              available contact information.
            </p>
          )}
        </section>
      </div>
      <section className="rm-candidate-provenance">
        <h3>Discovery & search cost</h3>
        <strong>Run: {c.runId || "Not provided"}</strong>
        {run ? (
          <>
            <span>
              {run.status} · {new Date(run.createdAt).toLocaleString()}
            </span>
            <span>
              ${run.spend.toFixed(3)} committed for this run
              {run.cap != null
                ? ` / $${run.cap.toFixed(2)} budget`
                : " · Budget not supplied"}
            </span>
            {run.reserved != null && (
              <small>
                ${run.reserved.toFixed(3)} pending / unconfirmed, included in
                committed spend.
              </small>
            )}
            <small>Run-level cost; not a per-candidate charge.</small>
          </>
        ) : (
          <p>Search history for this record has not synchronized.</p>
        )}
      </section>
    </>
  );
}

export default function RecruitMeCandidates({
  data,
  statuses,
  onStatusChange,
  onReview,
  saving = false,
  loading,
  error,
  refresh,
}: {
  data?: Workspace;
  statuses: Record<string, WorkflowStatus>;
  onStatusChange: (key: string, status: WorkflowStatus) => void;
  /** Prefill the review form from this discovery record. */
  onReview?: (candidate: Candidate) => void;
  saving?: boolean;
  loading: boolean;
  error: boolean;
  refresh: () => void;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [runId, setRunId] = useState("");
  const candidates = filterCandidates(
    data?.candidates ?? [],
    query,
    status,
    runId,
    statuses
  );
  const reset = () => {
    setQuery("");
    setStatus("");
    setRunId("");
  };
  return (
    <section className="rm-panel">
      <div className="rm-panel-heading">
        <div>
          <h2>Candidate workspace</h2>
          <p className="rm-muted">
            Review the person, the signal, and the supporting evidence.
          </p>
        </div>
        <Button variant="outline" onClick={refresh}>
          Refresh
        </Button>
      </div>
      <div className="rm-pipeline" aria-label="Recruiting workflow">
        {workflowStatuses.map(s => (
          <button
            key={s}
            aria-pressed={status === s}
            onClick={() => setStatus(status === s ? "" : s)}
          >
            {s}
            <b>
              {
                (data?.candidates ?? []).filter(
                  c =>
                    (statuses[candidateKey(c)] ??
                      (c as Candidate).status ??
                      "New") === s
                ).length
              }
            </b>
          </button>
        ))}
      </div>
      <div className="rm-candidate-toolbar">
        <label>
          <span>Search candidates</span>
          <Input
            placeholder="Name, role, location, or experience"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </label>
        <label>
          <span>Discovery run</span>
          <select value={runId} onChange={e => setRunId(e.target.value)}>
            <option value="">All search runs</option>
            {Array.from(new Set(data?.candidates.map(c => c.runId))).map(id => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
        <Button variant="ghost" onClick={reset}>
          Clear filters
        </Button>
      </div>
      <p className="rm-muted rm-space" role="status">
        {loading
          ? "Loading candidate evidence…"
          : `${candidates.length} of ${data?.candidates.length ?? 0} candidates`}
        {status && ` · ${status}`}
        {data?.snapshotAt &&
          ` · Snapshot ${new Date(data.snapshotAt).toLocaleString()}`}
      </p>
      <p className="rm-session-note">
        Workflow changes are saved for each candidate and run. Recruiting status
        does not change evidence verification or qualification scores.
      </p>
      {data?.candidatesTruncated && (
        <p role="status">
          This snapshot contains a limited candidate list. Review the full
          worker evidence report for additional records.
        </p>
      )}
      {error && (
        <p role="alert">
          Candidate data could not refresh. Displayed records may be out of
          date.
        </p>
      )}
      <div className="rm-candidate-list">
        {candidates.map(c => (
          <Dialog key={candidateKey(c)}>
            <DialogTrigger asChild>
              <button
                className="rm-candidate-row"
                aria-label={`Review ${c.name}`}
              >
                <span className="rm-candidate-avatar" aria-hidden="true">
                  {c.name
                    .split(/\s+/)
                    .filter(Boolean)
                    .slice(0, 2)
                    .map(n => n[0])
                    .join("")}
                </span>
                <span className="rm-candidate-summary">
                  <strong>{c.name || "Unnamed candidate"}</strong>
                  <span>
                    {c.currentRole || "Role not provided"} ·{" "}
                    {c.location || "Location unconfirmed"}
                  </span>
                  <small>
                    {c.fieldEvidence ||
                      "Electrical / construction experience unconfirmed"}
                  </small>
                  <span>
                    {c.yearsExperience == null
                      ? "Years not provided"
                      : `${c.yearsExperience} years`}{" "}
                    · Confidence: {c.confidence || "Not provided"}
                  </span>
                </span>
                <span className="rm-candidate-meta">
                  {c.reviewDecision && (
                    <span className="rm-tag">Reviewed · {c.reviewDecision.replace("_", " ")}</span>
                  )}
                  <span
                    className={`rm-candidate-badge ${c.verified ? "verified" : "unverified"}`}
                  >
                    {c.qualificationScore != null
                      ? `Score ${c.qualificationScore}`
                      : c.grade
                        ? `Grade ${c.grade}`
                        : "Not scored"}{" "}
                    · {c.verified ? "Verified" : "Needs review"}
                  </span>
                  <small>{signalFreshness(c.signalDate)}</small>
                  <span className="rm-tag">
                    {statuses[candidateKey(c)] ?? c.status ?? "New"}
                  </span>
                </span>
                <ArrowUpRight size={17} aria-hidden="true" />
              </button>
            </DialogTrigger>
            <DialogContent className="rm-candidate-dialog">
              <header className="rm-candidate-detail-header">
                <span className="rm-eyebrow">CANDIDATE REVIEW</span>
                <DialogTitle>{c.name || "Unnamed candidate"}</DialogTitle>
                <DialogDescription>
                  {c.currentRole || "Most recent role not provided"} ·{" "}
                  {c.location || "Location unconfirmed"}
                </DialogDescription>
                <label className="rm-status-control">
                  Recruiting status
                  <select
                    disabled={saving}
                    value={statuses[candidateKey(c)] ?? c.status ?? "New"}
                    onChange={e =>
                      onStatusChange(
                        candidateKey(c),
                        e.target.value as WorkflowStatus
                      )
                    }
                  >
                    {workflowStatuses.map(s => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                  <small>
                    {saving ? "Saving…" : "Saved for this candidate and run"}
                  </small>
                </label>
              </header>
              <div className="rm-candidate-detail-body">
                <CandidateDetail
                  candidate={c}
                  run={data?.runs.find(r => r.id === c.runId)}
                />
              </div>
              <footer className="rm-candidate-detail-footer">
                <span>
                  Evidence is shown as recorded. Missing information stays
                  unconfirmed.
                </span>
                {onReview && (
                  <DialogClose asChild>
                    <Button onClick={() => onReview(c)}>
                      Record my review
                    </Button>
                  </DialogClose>
                )}
                <DialogClose asChild>
                  <Button variant="outline">Back to candidates</Button>
                </DialogClose>
              </footer>
            </DialogContent>
          </Dialog>
        ))}
      </div>
      {!loading && !error && !candidates.length && (
        <div className="rm-empty">
          {data?.candidates.length ? (
            <Search aria-hidden="true" />
          ) : (
            <Users aria-hidden="true" />
          )}
          <h2>
            {data?.candidates.length
              ? "No matching candidates"
              : "Your candidate workspace is ready"}
          </h2>
          <p>
            {data?.candidates.length
              ? "Try another name, experience keyword, status, or search run."
              : "Candidates will appear here when research evidence is synchronized. Start with a saved job profile and review its search results."}
          </p>
          {!!data?.candidates.length && (
            <Button variant="outline" onClick={reset}>
              Clear filters
            </Button>
          )}
        </div>
      )}
    </section>
  );
}
