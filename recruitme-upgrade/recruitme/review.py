"""Reviewer submissions become reviewed imports. One shape for every feeder.

A submission is the flat form a recruiter fills in Central after finding a
person on Indeed, LinkedIn Recruiter, Employ Georgia or in the discovery list.
It is converted here into the evidence records `data.import_candidate` expects,
with per-evidence human attestations. Identity confidence gates verification:
only a `confirmed` identity lets claims become VERIFIED_FACT. A/B decisions
still have to clear the full qualification gates; nothing here bypasses them.
"""
import datetime
import re
from urllib.parse import urlsplit
from .budget import StopRun
from .qualification import POLARITIES, QUALITY, normalize_policy, public_url

VERSION = 'review-form-2026-09-17'
DECISIONS = ('A', 'B', 'FIT_POOL', 'REJECT', 'APPLICANT')
DATE_BASES = ('post_timestamp', 'resume_updated', 'application', 'stated_in_text', 'unknown')
IDENTITY = ('confirmed', 'probable', 'namesake_risk')
SOURCE_TYPES = tuple(k for k in QUALITY if k != 'unknown')
CHANNELS = ('discovery', 'indeed_smart_sourcing', 'linkedin_recruiter', 'employ_georgia', 'ziprecruiter',
            'postjobfree', 'craigslist', 'candidate_portal', 'referral', 'other')
TEXT_LIMIT = 3000


def _text(value, field, limit=TEXT_LIMIT, required=True):
    if value is None or (isinstance(value, str) and not value.strip()):
        if required: raise StopRun(f'{field} is required')
        return None
    if not isinstance(value, str) or len(value) > limit: raise StopRun(f'{field} must be text up to {limit} characters')
    return value.strip()


def _enum(value, field, allowed):
    if value not in allowed: raise StopRun(f'{field} must be one of: ' + ', '.join(allowed))
    return value


def _date(value, field):
    try:
        return datetime.date.fromisoformat(str(value)[:10]).isoformat()
    except (ValueError, TypeError):
        raise StopRun(f'{field} must be an ISO date') from None


def build_record(submission, *, now=None):
    """Convert one review-form submission into a reviewed-import record."""
    if not isinstance(submission, dict): raise StopRun('Submission must be an object')
    today = (now or datetime.datetime.now(datetime.timezone.utc)).date()
    s = submission
    identity_key = _text(s.get('identity_key'), 'identity_key', 400)
    name = _text(s.get('name'), 'name', 200)
    source_url = _text(s.get('source_url'), 'source_url', 2000)
    if not public_url(source_url): raise StopRun('source_url must be a public http(s) URL')
    source_type = _enum(s.get('source_type', 'professional_profile'), 'source_type', SOURCE_TYPES)
    identity = _enum(s.get('identity_confidence'), 'identity_confidence', IDENTITY)
    polarity = _enum(s.get('signal_polarity'), 'signal_polarity', POLARITIES)
    basis = _enum(s.get('date_basis'), 'date_basis', DATE_BASES)
    decision = _enum(s.get('decision'), 'decision', DECISIONS)
    channel = _enum(s.get('channel', 'discovery'), 'channel', CHANNELS)
    reviewer = _text(s.get('reviewer'), 'reviewer', 120)
    if s.get('contradictions_checked') is not True: raise StopRun('contradictions_checked must be confirmed')
    statement = _text(s.get('statement_excerpt'), 'statement_excerpt')
    statement_date = _date(s['statement_date'], 'statement_date') if s.get('statement_date') else None
    if basis != 'unknown' and not statement_date: raise StopRun('statement_date is required unless date_basis is unknown')
    if statement_date and statement_date > today.isoformat(): raise StopRun('statement_date cannot be in the future')
    signal_url = _text(s.get('signal_source_url'), 'signal_source_url', 2000, required=False) or source_url
    if not public_url(signal_url): raise StopRun('signal_source_url must be a public http(s) URL')
    location = _text(s.get('location'), 'location', 300)
    role = _text(s.get('role'), 'role', 300)
    years = s.get('years_experience')
    if years is not None and (type(years) not in (int, float) or not 0 <= years <= 80): raise StopRun('years_experience must be 0-80')
    field_flag = s.get('field_experience_confirmed')
    if field_flag not in (True, False, None): raise StopRun('field_experience_confirmed must be true, false or omitted')
    excerpts = s.get('excerpts') or {}
    if not isinstance(excerpts, dict): raise StopRun('excerpts must be an object')

    verified = identity == 'confirmed'
    retrieved = today.isoformat()
    group = (urlsplit(source_url).hostname or 'source').lower()

    def evidence(field, value, excerpt, url=source_url, **extra):
        row = dict(field=field, value=value, status='CLAIMED', source_url=url, excerpt=excerpt[:TEXT_LIMIT],
                   retrieved_at=retrieved, independence_group=group, source_type=source_type,
                   knowledge_status='VERIFIED_FACT' if verified else 'REASONABLE_INFERENCE',
                   human_verified=verified, subject_confirmed=verified, identity_confidence=identity)
        row.update(extra)
        return row

    facts = {'name': name, 'role': role, 'location': location, 'availability_signal': statement}
    rows = [evidence('name', name, _text(excerpts.get('name'), 'excerpts.name', required=False) or f'Name shown on source: {name}'),
            evidence('role', role, _text(excerpts.get('role'), 'excerpts.role', required=False) or f'Role shown on source: {role}'),
            evidence('location', location, _text(excerpts.get('location'), 'excerpts.location', required=False) or f'Location shown on source: {location}')]
    if years is not None:
        facts['years_experience'] = years
        rows.append(evidence('years_experience', years, _text(excerpts.get('years_experience'), 'excerpts.years_experience', required=False) or f'Relevant years recorded by reviewer: {years:g}'))
    if field_flag is not None:
        facts['commercial_experience'] = field_flag
        rows.append(evidence('commercial_experience', field_flag, _text(excerpts.get('field_experience'), 'excerpts.field_experience', required=False)
                             or ('Reviewer confirmed hands-on commercial/industrial electrical field work' if field_flag else 'Reviewer found no commercial/industrial electrical field work')))
    rows.append(evidence('availability_signal', statement, statement, url=signal_url, signal_polarity=polarity, date_basis=basis,
                         original_date=statement_date, original_date_verified=bool(statement_date) and basis != 'unknown'))
    contacts = []
    contact = _text(s.get('contact_url'), 'contact_url', 2000, required=False)
    if contact:
        if not public_url(contact): raise StopRun('contact_url must be a public http(s) URL')
        contacts.append(dict(route_type='professional_profile', value=contact, source_url=contact, retrieved_at=retrieved,
                             public_professional=True, status='CLAIMED'))
    record = dict(identity_key=identity_key, reviewed_by_human=True, facts=facts, evidence=rows, contacts=contacts,
                  notes=_text(s.get('notes'), 'notes', 2000, required=False) or '',
                  review=dict(decision=decision, reviewer=reviewer, reviewed_at=retrieved, identity_confidence=identity,
                              channel=channel, form_version=VERSION))
    if decision in ('A', 'B'):
        record['assessment'] = dict(classification=decision, reviewed=True, identified_person=verified,
                                    trade_fit=bool(field_flag), geographic_fit=True,
                                    signal_subject_confirmed=verified, signal_date_verified=bool(statement_date) and basis != 'unknown',
                                    contradictions_checked=True, recruiting_signal=statement if polarity == 'POSITIVE_SEEKING' else None,
                                    source_urls=sorted({source_url, signal_url}), signal_date=statement_date)
    return record


def policy_from_submission(submission, fallback=None):
    """Optional per-submission policy (localities, window, role kind) or the caller's fallback."""
    policy = submission.get('policy') if isinstance(submission, dict) else None
    if not policy:
        return fallback
    if not isinstance(policy, dict): raise StopRun('policy must be an object')
    try:
        return normalize_policy({**(fallback or {}), **policy})
    except ValueError as error:
        raise StopRun('Invalid policy: ' + str(error)) from None


def import_submission(ledger, submission, *, profile=None, now=None):
    """Store one reviewed submission in the worker ledger. No provider spend.

    Every submission gets its own zero-budget run so the audit trail and runtime
    bindings exist; the candidate is also associated with the discovery run the
    reviewer was looking at, when that run is known. A/B decisions that fail the
    qualification gates roll back and are reported, never stored.
    """
    import json, uuid
    from . import data
    from .qualification import policy_from_profile
    record = build_record(submission, now=now)
    review_run = 'review-' + uuid.uuid4().hex[:12]
    ledger.create_run(review_run, '0')
    ledger.bind_manifest(review_run, {'mode': 'reviewed_import', 'form_version': VERSION, 'identity_key': record['identity_key']})
    data.initialize(ledger.db)
    policy = policy_from_submission(submission, policy_from_profile(profile))
    origin = submission.get('run_id') if isinstance(submission.get('run_id'), str) else None
    try:
        cid = data.import_candidate(ledger.db, record, run_id=review_run, policy=policy)
        if origin and ledger.db.execute('SELECT 1 FROM runs WHERE id=?', (origin,)).fetchone():
            ledger.db.execute('INSERT OR IGNORE INTO candidate_runs VALUES(?,?)', (cid, origin))
        if record.get('assessment'):
            ledger.record_qualification(review_run, record['identity_key'], record['assessment'], policy=policy)
        assessment = data.candidate_assessment(ledger.db, cid)
        ledger.event(review_run, 'REVIEW_IMPORTED', json.dumps({'candidate_id': cid, 'decision': record['review']['decision'],
                                                                'reviewer': record['review']['reviewer'], 'classification': assessment['classification']}))
        ledger.stop(review_run, 'Reviewed submission stored', 'COMPLETE')
        return dict(accepted=True, candidateId=cid, runId=review_run, originRunId=origin,
                    classification=assessment['classification'], score=assessment['score'],
                    blockers=assessment['blockers'], decision=record['review']['decision'])
    except StopRun as error:
        ledger.stop(review_run, error)
        return dict(accepted=False, runId=review_run, decision=record['review']['decision'], errors=[str(error)])
