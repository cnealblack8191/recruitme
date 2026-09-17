import { ClipboardCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  dateBases,
  identityConfidences,
  reviewChannels,
  reviewDecisions,
  signalPolarities,
  sourceTypes,
  type ReviewReceipt,
  type ReviewSubmissionInput,
} from "@shared/recruitmeReview";

const labels = {
  decision: {
    A: "A · Verified seeker, strong fit",
    B: "B · Verified seeker, fit needs detail",
    FIT_POOL: "Fit pool · good fit, no verified seeking signal",
    REJECT: "Reject · not a fit or not this person",
  },
  polarity: {
    POSITIVE_SEEKING: "Wants work (positive)",
    NEGATIVE_NOT_SEEKING: "Not looking (negative)",
    AMBIGUOUS: "Ambiguous",
  },
  basis: {
    post_timestamp: "Post or update timestamp",
    resume_updated: "Résumé last-updated date",
    application: "Application submitted",
    stated_in_text: "Date stated in the text",
    unknown: "Unknown",
  },
  identity: {
    confirmed: "Confirmed same person",
    probable: "Probably the same person",
    namesake_risk: "Namesake risk",
  },
} as const;

/**
 * Presentational review form. The parent owns state and the mutation so this
 * renders without a tRPC provider. Every field maps to a controlled value the
 * worker validates again; the form never invents dates or verification.
 */
export default function RecruitMeReview({
  draft,
  onChange,
  onSubmit,
  onReset,
  enabled,
  submitting = false,
  receipt,
  errorMessage,
}: {
  draft: ReviewSubmissionInput;
  onChange: (next: ReviewSubmissionInput) => void;
  onSubmit: () => void;
  onReset: () => void;
  enabled: boolean;
  submitting?: boolean;
  receipt?: ReviewReceipt | null;
  errorMessage?: string | null;
}) {
  const set = <K extends keyof ReviewSubmissionInput>(
    key: K,
    value: ReviewSubmissionInput[K]
  ) => onChange({ ...draft, [key]: value });
  const text = (value: string) => (value.trim() ? value : null);
  return (
    <section className="rm-panel rm-review">
      <div className="rm-panel-heading">
        <div>
          <h2>Record a reviewed candidate</h2>
          <p className="rm-muted">
            For a person you found on Indeed, LinkedIn Recruiter, Employ Georgia
            or in the discovery list. Enter what the source literally says and
            the date the person said it. The worker applies the qualification
            gates; A/B is stored only when every gate passes.
          </p>
        </div>
        <ClipboardCheck aria-hidden="true" />
      </div>
      {!enabled && (
        <p role="status" className="rm-notice">
          Reviewed-candidate import is not enabled on this server. Set
          RECRUITME_BRIDGE_REVIEW_CMD to store reviews in the worker ledger.
        </p>
      )}
      <form
        onSubmit={e => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <div className="rm-form-grid">
          <label>
            Full name as shown on the source
            <Input
              required
              maxLength={200}
              value={draft.name}
              onChange={e => set("name", e.target.value)}
            />
          </label>
          <label>
            Identity key (profile URL or stable ID)
            <Input
              required
              maxLength={400}
              value={draft.identity_key}
              onChange={e => set("identity_key", e.target.value)}
            />
          </label>
          <label className="rm-wide">
            Source URL (public page you reviewed)
            <Input
              required
              type="url"
              maxLength={2000}
              value={draft.source_url}
              onChange={e => set("source_url", e.target.value)}
            />
          </label>
          <label>
            Source type
            <select
              value={draft.source_type}
              onChange={e =>
                set("source_type", e.target.value as typeof draft.source_type)
              }
            >
              {sourceTypes.map(v => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Where you found them
            <select
              value={draft.channel}
              onChange={e =>
                set("channel", e.target.value as typeof draft.channel)
              }
            >
              {reviewChannels.map(v => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Current or most recent role
            <Input
              required
              maxLength={300}
              value={draft.role}
              onChange={e => set("role", e.target.value)}
            />
          </label>
          <label>
            Location as shown (city, GA)
            <Input
              required
              maxLength={300}
              value={draft.location}
              onChange={e => set("location", e.target.value)}
            />
          </label>
          <label>
            Relevant years (leave blank if unknown)
            <Input
              type="number"
              min="0"
              max="80"
              step="0.5"
              value={draft.years_experience ?? ""}
              onChange={e =>
                set(
                  "years_experience",
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
            />
          </label>
          <label>
            Hands-on commercial/industrial electrical work confirmed?
            <select
              value={
                draft.field_experience_confirmed === null ||
                draft.field_experience_confirmed === undefined
                  ? ""
                  : String(draft.field_experience_confirmed)
              }
              onChange={e =>
                set(
                  "field_experience_confirmed",
                  e.target.value === "" ? null : e.target.value === "true"
                )
              }
            >
              <option value="">Not reviewed</option>
              <option value="true">Yes, confirmed from the source</option>
              <option value="false">No evidence found</option>
            </select>
          </label>
          <label className="rm-wide">
            The person&apos;s own statement, verbatim
            <textarea
              required
              maxLength={3000}
              value={draft.statement_excerpt}
              onChange={e => set("statement_excerpt", e.target.value)}
            />
          </label>
          <label>
            What the statement means
            <select
              value={draft.signal_polarity}
              onChange={e =>
                set(
                  "signal_polarity",
                  e.target.value as typeof draft.signal_polarity
                )
              }
            >
              {signalPolarities.map(v => (
                <option key={v} value={v}>
                  {labels.polarity[v]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Date the person made the statement
            <Input
              type="date"
              value={draft.statement_date ?? ""}
              onChange={e => set("statement_date", text(e.target.value))}
              required={draft.date_basis !== "unknown"}
            />
          </label>
          <label>
            How you know that date
            <select
              value={draft.date_basis}
              onChange={e =>
                set("date_basis", e.target.value as typeof draft.date_basis)
              }
            >
              {dateBases.map(v => (
                <option key={v} value={v}>
                  {labels.basis[v]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Statement URL (if different from the source)
            <Input
              type="url"
              maxLength={2000}
              value={draft.signal_source_url ?? ""}
              onChange={e => set("signal_source_url", text(e.target.value))}
            />
          </label>
          <label>
            Identity confidence
            <select
              value={draft.identity_confidence}
              onChange={e =>
                set(
                  "identity_confidence",
                  e.target.value as typeof draft.identity_confidence
                )
              }
            >
              {identityConfidences.map(v => (
                <option key={v} value={v}>
                  {labels.identity[v]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Public professional contact route (optional)
            <Input
              type="url"
              maxLength={2000}
              value={draft.contact_url ?? ""}
              onChange={e => set("contact_url", text(e.target.value))}
            />
          </label>
          <label>
            Your decision
            <select
              value={draft.decision}
              onChange={e =>
                set("decision", e.target.value as typeof draft.decision)
              }
            >
              {reviewDecisions.map(v => (
                <option key={v} value={v}>
                  {labels.decision[v]}
                </option>
              ))}
            </select>
          </label>
          <label className="rm-wide rm-check">
            <input
              type="checkbox"
              required
              checked={draft.contradictions_checked === true}
              onChange={e =>
                onChange({
                  ...draft,
                  contradictions_checked: e.target.checked
                    ? true
                    : (undefined as unknown as true),
                })
              }
            />
            &nbsp;I checked for later statements that contradict this one
            (hired, no longer looking) and for same-name people.
          </label>
          <label className="rm-wide">
            Notes for the file (optional)
            <textarea
              maxLength={2000}
              value={draft.notes ?? ""}
              onChange={e => set("notes", e.target.value)}
            />
          </label>
        </div>
        <div className="rm-actions">
          <Button type="submit" disabled={!enabled || submitting}>
            {submitting ? "Storing review…" : "Store reviewed candidate"}
          </Button>
          <Button type="button" variant="ghost" onClick={onReset}>
            Clear form
          </Button>
        </div>
      </form>
      {errorMessage && <p role="alert">{errorMessage}</p>}
      {receipt && (
        <div role="status" className="rm-notice">
          <span className="rm-dot" />
          <div>
            <strong>
              {receipt.accepted
                ? `Stored as ${receipt.classification ?? "reviewed"}${receipt.score != null ? ` · score ${receipt.score}` : ""}`
                : "Not stored"}
            </strong>
            {receipt.accepted && receipt.blockers?.length ? (
              <p>Open gates: {receipt.blockers.join("; ")}</p>
            ) : null}
            {!receipt.accepted && receipt.errors?.length ? (
              <p>{receipt.errors.join("; ")}</p>
            ) : null}
            {!receipt.accepted && receipt.decision && (
              <p>
                An A/B decision is stored only when every qualification gate
                passes. Change the decision to Fit pool to keep the record with
                its open gates listed.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
