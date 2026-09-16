# Commercial electrical candidate qualification

Implemented on `codex/candidate-scoring`. No merge, deployment, provider calls, discovery edits, frontend edits, or changes to budget/security configuration are included.

## Architecture and integration boundary

The Python worker stores discoveries separately from reviewed candidate identities in SQLite. `data.import_candidate` is the existing reviewed-import/channel-import entry point; it now evaluates all accumulated evidence rather than scoring the newest flat facts. `data.report` reassesses every stored candidate on read and sorts qualified candidates first, then provisional, then research-only, with descending score/confidence and stable candidate-ID ties. Discoveries remain unverified pages until the existing identity-review/import process creates a candidate. This change deliberately does not convert search packets into people.

`qualification.assess_candidate(facts, evidence, contacts, as_of=...)` is a pure, deterministic evaluator. Flat facts are accepted for call compatibility but never awarded points without evidence. `data.score_candidate` retains its `(score, reasons)` tuple API, with optional evidence/contacts/date inputs. Use the structured assessment for new integrations.

Each reported candidate adds `qualification`: version, assessment date, classification, score, raw score, confidence, components, claims, signal age, blockers, cap explanation and human-review/outreach flags. Existing scalar score/confidence/contactability columns are refreshed during import; reported copies are refreshed on read without mutating historical evidence. Reported JSON notes also receive the current assessment; stored notes retain their import-time assessment.

The web snapshot currently has a separate narrow candidate schema and can discard these new fields. The integration agent must pass through `qualification` in the snapshot producer/schema and consume its classifications, reasons and knowledge labels. Do not substitute discovery `review_priority`, grade hints, or legacy A/B counts for the new qualification result. Existing recruiter/HR discovery profiles and direct `governors.record_qualification` callers keep their own contracts; this module evaluates commercial electrical trade leads. The reviewed-import path now rejects incoming A/B assessments unless this assessment is FULLY_QUALIFIED, before any candidate changes commit. It never automatically writes A/B progress or promotes discovery grades.

## Scoring policy (100 possible points)

| Component | Maximum | Rule |
| --- | ---: | --- |
| Commercial trade fit | 25 | Electrical field role AND commercial construction experience; electrical engineer/recruiter titles alone do not qualify. |
| Relevant experience | 15 | 3–10 years: full; 2–<3 or >10–12: 60%; other valid 0–80 values: 25%. Booleans, strings, negative/nonfinite values are invalid. Years must represent relevant trade work, not age or total unrelated employment. |
| Metro Atlanta | 15 | Explicit supported metro locality plus Georgia/GA, or an explicit Metro/Greater Atlanta designation. Georgia alone and ambiguous city names get zero. |
| Job-change interest | 20 | Verified, person-attributed positive interest within 90 days: full; older attributable statements: 25% with no full qualification. Layoff, relocation, resume presence, or project completion alone are insufficient. |
| Signal freshness | 10 | Original statement age 0–30 days: full; 31–90: 60%; older/unknown/invalid/future: zero. |
| Contact route | 5 | Public professional profile, professional email, or business phone with usable format, source URL, non-UNKNOWN status, and observation within 180 days. No inferred email patterns, private numbers, or outreach. |
| Source quality | 10 | Mean best reliability across identity, role, commercial experience, years, location, interest. First-party/official: 1; professional profile: .8; secondary: .5; search snippet: .25; unspecified: 0. Repetition adds nothing. |

For evidence-based fit components, VERIFIED_FACT gets full eligible points, REASONABLE_INFERENCE gets half, UNKNOWN gets zero. Interest/freshness additionally require explicit verified attribution and original-date review. Contact availability is labeled an inference: source existence does not confirm delivery, permission to contact, or willingness.

FULLY_QUALIFIED requires verified identity and all five substantive claims; commercial field fit; 3–10 relevant years; established metro location; a positive attributed verified signal within 90 days; a current contact route; and no unresolved conflicts. Any failed gate caps the final score at 69, regardless of raw points. PROVISIONAL means recent verified interest with other gaps. RESEARCH_ONLY means no sufficient recent verified interest. These are recruiting research assessments, not hiring decisions; human review remains required.

Confidence is a separate evidence-support index: mean reliability multiplied by knowledge strength (verified 1, inferred .5, unknown 0) across the six claims, scaled to 100. Without sufficient recent verified interest it is capped at 49. It is not a calibrated probability or an additional score component.

## Evidence contract and additive persistence

Existing evidence statuses CLAIMED, CORROBORATED and UNKNOWN and their SQLite constraints remain unchanged. Neither CLAIMED nor CORROBORATED automatically establishes a verified fact. Legacy evidence defaults to inference, with unspecified source reliability zero. The extra table `qualification_annotations(evidence_id, metadata_json)` is created additively by the existing `data.initialize` call; no old rows are deleted or migrated in place.

Each evidence record can carry the following additional fields:

```json
{
  "knowledge_status": "VERIFIED_FACT",
  "human_verified": true,
  "source_type": "first_party",
  "subject_confirmed": true,
  "original_date": "2026-09-01",
  "original_date_verified": true
}
```

These accompany the existing field/value/source_url/excerpt/retrieved_at/status/independence_group fields. The last three fields are required on the availability_signal evidence itself to establish recent interest. A separate `signal_date` fact or retrieval/publication timestamp cannot supply that link. Original date must not exceed observation date; observation date must not exceed assessment date. Use ISO dates or ISO timestamps; operational assessment defaults to UTC today, while tests pin the date.

`human_verified` is persisted true only when the outer record explicitly has `reviewed_by_human=true` and the individual evidence has `human_verified=true`. The source must also be first-party, official or professional-profile quality. Agent-only review cannot establish a VERIFIED_FACT, even if it supplies that label. This is an attestation contract, not an automatic source-authenticity detector: the authorized reviewer is responsible for checking identity, the literal claim, relevant-year basis, subject attribution and dates. Upstream code must never set human attestations on an agent's behalf.

Evidence and annotations are append-only. Duplicate source/field/excerpt rows cannot inflate scores or silently change an existing value. Such changed values fail the import transaction. New contradictory values with distinct evidence remain visible and block qualification rather than selecting the newest convenient claim. Differently worded positive availability statements are not treated as conflicts; negative availability evidence blocks qualification even when undated or older. Resolving a genuine historical contradiction needs an explicit future reviewed resolution workflow; this implementation conservatively does not discard it. Existing annotation rows are not overwritten by re-imports; new review evidence needs a distinct excerpt/source record.

The metro locality list is conservative and not an exhaustive metro boundary/geocoder. Missing, ambiguous, unsupported localities and possible relocation remain review gaps. Legacy rows need enriched evidence before qualifying. No inferred values are copied into verified-fact labels.

## Files and validation

Implementation files: `recruitme/qualification.py` (new), `recruitme/data.py` (integration), `tests/test_qualification.py` (new), `tests/test_foundation.py` (two legacy numeric expectations updated and contact fixture date made current), this document.

Run from `recruitme-upgrade`:

```text
python -B -m unittest discover -s tests -v
```

Tests cover strong leads, boundary years, generic/nontrade roles, missing/ambiguous/outside locations, stale and undated signals, exact recency boundaries, unsupported weak intent, negative/hired updates, source reliability, agent verification spoofing, unknown/future/malformed evidence, invalid/private/expired contact routes, duplicate/order invariance, stable ranking, import rollback, additive initialization, historical contradictions, A/B bypass rejection, and score aging without evidence mutation. Existing budget, request-cap, concurrency, provider and security tests run alongside them. Linux locking, signal timers and deployed systemd sandbox checks require the Linux worker environment.

The first sandboxed suite attempt encountered Windows temp-directory permissions; the rerun with normal local filesystem access succeeded. Logs are `qualification-regression.log` (initial environment failures) and `qualification-regression-normal-access.log` (successful rerun). Final validation is recorded separately in `qualification-final-validation.log`.

Final validation: 255 tests executed, 250 passed, 5 Linux/systemd-only skips, zero failures. This includes 26 new qualification test methods with additional boundary subcases.

The pre-existing `recruitme-upgrade` directory was untracked in the shared checkout, alongside other agents' ongoing work. Another agent switched that checkout to `codex/codex/integration-qa` during validation. The five implementation/documentation files are therefore also preserved in the separate `worktrees/candidate-scoring` worktree on `codex/candidate-scoring`, with a scoped commit and no merge. Copies remain in the shared checkout for integration. Because the existing worker was untracked at branch creation, this scoped branch depends on the existing worker sources for standalone execution; validation ran against the complete shared worker. Integrate these five paths with that worker rather than treating this branch as a standalone worker installation. Do not blindly stage unrelated workspace files or transient test logs.
