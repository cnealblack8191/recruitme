"""Allowlisted dashboard rows. Discovery hints never become verified facts."""
import hashlib
import math
import datetime as dt
from .qualification import public_url, date


def discovery_rows(run_id, packets):
    rows = []
    seen = set()
    from .discovery import page_key
    for packet in packets:
        url = packet.get('source_url', '')
        if not packet.get('name_hint') or not public_url(url):
            continue
        key = page_key(url)
        if key in seen:
            continue
        seen.add(key)
        evidence = packet.get('discovery_evidence', {})
        observations = packet.get('observations', [])
        links = []
        for observation in observations:
            source = observation.get('source_url', url)
            if public_url(source):
                links.append({'label': 'INFERRED · ' + str(observation.get('retrieved_at', 'Unknown retrieval date'))[:60] + ' · ' + str(observation.get('provider', 'Unknown provider'))[:80] + ' · ' + str(observation.get('query', 'Source observation'))[:400], 'url': source})
        contacts = []
        for route in evidence.get('contact_routes', []):
            value = route.get('value', '')
            # Export source pages only: reviewing a page does not verify delivery or ownership.
            if public_url(value):
                contacts.append({'label': 'Unverified professional source route', 'url': value})
        rows.append(dict(id=hashlib.sha256(key.encode()).hexdigest(), runId=run_id,
            name=str(packet['name_hint'])[:200], sourceUrl=url[:2000],
            classification='RESEARCH_ONLY', grade=None, verified=False,
            fieldEvidence=str(packet.get('electrical_field_excerpt') or packet.get('text') or '')[:3000],
            recruitingEvidence=str(packet.get('recruiting_hr_excerpt') or '')[:3000],
            signalDate=None, signalEvidence=str(packet.get('signal_excerpt') or '')[:3000],
            location=', '.join(evidence.get('local_place_mentions', []))[:300],
            qualificationScore=None, confidence='UNKNOWN',
            qualificationReason='Discovery hints are INFERRED. Identity, relevant years, and original signal date require review.',
            evidenceLinks=links[:50], contactRoutes=contacts[:20]))
    return rows


def reviewed_rows(db, run_id):
    from .data import candidate_assessment
    # Never attribute historical candidates to a run merely because they share a database.
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='candidate_runs'").fetchone():
        return []
    rows = []
    for member in db.execute('SELECT candidate_id FROM candidate_runs WHERE run_id=?', (run_id,)):
        cid = member['candidate_id']
        q = candidate_assessment(db, cid)
        claims = q['claims']
        evidence = [dict(e) for e in db.execute('SELECT * FROM evidence WHERE candidate_id=? ORDER BY id', (cid,))]
        links = [{'label': claims.get(e['field'], {}).get('knowledge_status', 'UNKNOWN') + ' · ' + e['field'] + ': ' + e['excerpt'][:400],
                  'url': e['source_url']} for e in evidence if public_url(e['source_url'])]
        if not links:
            continue
        contacts = [{'label': 'INFERRED · reviewed public professional route', 'url': c['value']}
                    for c in db.execute('SELECT * FROM contacts WHERE candidate_id=?', (cid,))
                    if c['route_type'] == 'professional_profile' and public_url(c['value'])
                    and date(c['retrieved_at']) and 0 <= (date(q['assessed_as_of']) - date(c['retrieved_at'])).days <= 180]
        value = lambda field: claims[field]['value']
        years = value('years_experience')
        rows.append(dict(id=cid, runId=run_id, name=str(value('name') or 'Identity requires review')[:200],
            sourceUrl=links[0]['url'], classification=q['classification'], grade=None,
            verified=q['classification'] == 'FULLY_QUALIFIED',
            fieldEvidence='\n'.join(e['excerpt'] for e in evidence if e['field'] in ('role', 'commercial_experience', 'years_experience'))[:3000],
            recruitingEvidence='', location=str(value('location') or '')[:300], currentRole=str(value('role') or '')[:600],
            yearsExperience=years if type(years) in (int, float) and math.isfinite(years) else None,
            qualificationScore=q['score'], confidence=str(q['confidence_score']) + '/100 evidence support',
            qualificationReason='; '.join(q['blockers']) or 'All required claims have human verification; recruiter review remains required.',
            signalDate=(date(q['assessed_as_of']) - dt.timedelta(days=q['signal_age_days'])).isoformat() if q['signal_age_days'] is not None else None,
            signalEvidence='\n'.join(e['excerpt'] for e in evidence if e['field'] == 'availability_signal')[:3000],
            evidenceLinks=links[:50], contactRoutes=contacts[:20]))
    return sorted(rows, key=lambda row: (-row['qualificationScore'], row['id']))
