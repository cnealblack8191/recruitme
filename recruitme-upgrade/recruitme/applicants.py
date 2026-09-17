"""Candidate Portal applications become reviewed imports with a verified seeking signal.

An application is the strongest availability evidence the product sees: the person
identified themselves, asked for this job, and ECI's own server recorded when. That
one fact is verified by the system. Everything the applicant typed (name, role,
years, location) stays an inference until a recruiter confirms it in the review form,
so an applicant lands as PROVISIONAL, never as a silent A/B.
"""
import datetime
from .budget import StopRun
from .qualification import public_url
from .review import build_record

VERSION = 'portal-intake-2026-09-17'


def applicant_submission(application, *, opening, portal_base_url):
    """Map one portal registration to a review-form submission (channel candidate_portal)."""
    if not isinstance(application, dict): raise StopRun('Application must be an object')
    if not isinstance(opening, dict) or not opening.get('role'): raise StopRun('Opening role is required')
    ident = application.get('id')
    if type(ident) is not int or ident <= 0: raise StopRun('Application id must be a positive integer')
    name = application.get('full_name')
    if not isinstance(name, str) or not name.strip(): raise StopRun('Applicant name is required')
    submitted = application.get('created_at')
    try:
        stamp = datetime.datetime.fromisoformat(str(submitted).replace('Z', '+00:00'))
    except (ValueError, TypeError):
        raise StopRun('Application timestamp must be ISO 8601') from None
    base = str(portal_base_url or '').rstrip('/')
    source = f'{base}/admin/results#candidate-{ident}'
    if not public_url(source): raise StopRun('Portal base URL must be a public http(s) URL')
    day = stamp.date().isoformat()
    notes = [f'Applied through the ECI Candidate Portal at {stamp.isoformat()}.']
    if application.get('email'): notes.append('Applicant supplied an email address (held in the portal, not exported).')
    if application.get('resume_url'): notes.append('Résumé uploaded to the portal.')
    location = application.get('location') if isinstance(application.get('location'), str) and application.get('location').strip() else 'Not stated on application'
    years = application.get('years_experience') if type(application.get('years_experience')) in (int, float) else None
    return dict(identity_key=f'portal:{ident}', name=name.strip(), source_url=source, source_type='first_party_submission',
                channel='candidate_portal', role=str(opening['role']), location=location, years_experience=years,
                field_experience_confirmed=None,
                statement_excerpt=f'Applied for {opening.get("title") or opening["role"]} through the ECI Candidate Portal on {day}.',
                statement_date=day, date_basis='application', signal_polarity='POSITIVE_SEEKING', signal_source_url=None,
                identity_confidence='probable', contradictions_checked=True, contact_url=None, decision='APPLICANT',
                reviewer='candidate-portal', notes=' '.join(notes), run_id=opening.get('run_id'),
                excerpts={'name': f'Applicant entered name: {name.strip()}', 'role': f'Applied for: {opening["role"]}',
                          'location': 'Location as stated on the application' if location != 'Not stated on application' else 'The portal registration does not collect a location'})


def applicant_record(application, *, opening, portal_base_url, now=None):
    """Reviewed-import record: seeking signal verified by the portal timestamp, other claims inferred."""
    submission = applicant_submission(application, opening=opening, portal_base_url=portal_base_url)
    record = build_record(submission, now=now)
    for e in record['evidence']:
        if e['field'] == 'availability_signal':
            e.update(knowledge_status='VERIFIED_FACT', system_recorded=True, subject_confirmed=True,
                     original_date_verified=True, human_verified=False)
    record['review']['form_version'] = VERSION
    return record
