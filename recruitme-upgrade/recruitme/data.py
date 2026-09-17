"""Evidence-first storage and transparent, non-decisional qualification."""
import hashlib
import json
import re
from urllib.parse import urlsplit, urlunsplit
from .budget import StopRun
from .qualification import assess_candidate, ranking_key, normalize_policy

FIELDS = {'name','location','current_employer','previous_employer','role','years_experience',
          'commercial_experience','specialties','availability_signal','signal_date'}
STATUSES = {'CLAIMED','CORROBORATED','UNKNOWN'}


def canonical_url(url):
    u = urlsplit(url)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:
        raise StopRun('Invalid public source URL')
    # Apollo search returns partial records without public profile URLs. Their
    # provenance fragments identify different people, not sections of a page.
    fragment = u.fragment if (u.scheme == 'https' and u.netloc.lower() == 'api.apollo.io'
        and u.path == '/api/v1/mixed_people/api_search'
        and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', u.fragment)) else ''
    return urlunsplit((u.scheme.lower(),u.netloc.lower(),u.path or '/',u.query,fragment))


def initialize(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS discoveries(
      id TEXT PRIMARY KEY, run_id TEXT NOT NULL, query TEXT NOT NULL, source_url TEXT,
      title TEXT, excerpt TEXT, retrieved_at TEXT NOT NULL, raw_evidence_path TEXT NOT NULL,
      stage TEXT NOT NULL DEFAULT 'DISCOVERY', requires_review INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS candidates(
      id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT, current_employer TEXT,
      previous_employer TEXT, role TEXT, years_experience REAL, commercial_experience TEXT,
      specialties TEXT, availability_signal TEXT, signal_date TEXT, profile_url TEXT,
      contactability TEXT NOT NULL DEFAULT 'UNKNOWN', qualification_score REAL DEFAULT 0,
      confidence_score REAL DEFAULT 0, notes TEXT, human_review_required INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS evidence(
      id INTEGER PRIMARY KEY, candidate_id TEXT NOT NULL REFERENCES candidates(id),
      field TEXT NOT NULL, value TEXT, source_url TEXT NOT NULL, excerpt TEXT NOT NULL,
      retrieved_at TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('CLAIMED','CORROBORATED','UNKNOWN')),
      independence_group TEXT NOT NULL, UNIQUE(candidate_id,field,source_url,excerpt));
    CREATE TABLE IF NOT EXISTS contacts(
      id INTEGER PRIMARY KEY, candidate_id TEXT NOT NULL REFERENCES candidates(id),
      route_type TEXT NOT NULL CHECK(route_type IN ('public_professional_email','public_business_phone','professional_profile')),
      value TEXT NOT NULL, source_url TEXT NOT NULL, retrieved_at TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('CLAIMED','CORROBORATED','UNKNOWN')),
      UNIQUE(candidate_id,route_type,value));
    CREATE TABLE IF NOT EXISTS qualification_annotations(
      evidence_id INTEGER PRIMARY KEY REFERENCES evidence(id), metadata_json TEXT NOT NULL);
    ''')


def import_candidate(db, record, *, run_id=None, policy=None):
    """Only explicitly reviewed structured records can identify a research lead.

    Search hits are NOT automatically promoted to candidates or used to infer facts.
    Names alone never merge people: operator identity_key is mandatory.
    """
    if not (record.get('reviewed_by_human') is True or record.get('reviewed_by_agent') is True) or not record.get('identity_key'):
        raise StopRun('Candidate identity requires explicit review')
    reviewer = 'human' if record.get('reviewed_by_human') is True else 'agent_pending_human'
    facts = record.get('facts', {})
    if not set(facts).issubset(FIELDS) or not isinstance(facts.get('name'),str):
        raise StopRun('Unknown/sensitive candidate fields or missing name')
    evid = record.get('evidence', [])
    for field, value in facts.items():
        if value is not None and not any(e.get('field')==field and e.get('value')==value and e.get('status')!='UNKNOWN' for e in evid):
            raise StopRun('Every populated fact requires matching evidence')
    cid = hashlib.sha256(record['identity_key'].encode()).hexdigest()[:24]
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute('INSERT INTO candidates(id,name,notes) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING',
                   (cid,facts['name'],record.get('notes','')))
        if run_id is not None:
            db.execute('CREATE TABLE IF NOT EXISTS candidate_runs(candidate_id TEXT REFERENCES candidates(id), run_id TEXT REFERENCES runs(id), PRIMARY KEY(candidate_id,run_id))')
            db.execute('INSERT OR IGNORE INTO candidate_runs VALUES(?,?)', (cid, run_id))
        for e in evid:
            if e['field'] not in FIELDS or e['status'] not in STATUSES or not e.get('excerpt') or not e.get('retrieved_at') or not e.get('independence_group'):
                raise StopRun('Incomplete evidence')
            if e['status']=='CORROBORATED':
                independent = {x['independence_group'] for x in evid if x.get('field')==e['field'] and x.get('value')==e.get('value') and x.get('status')!='UNKNOWN'}
                if len(independent)<2:
                    raise StopRun('Corroboration requires two independent sources')
            db.execute('INSERT OR IGNORE INTO evidence(candidate_id,field,value,source_url,excerpt,retrieved_at,status,independence_group) VALUES(?,?,?,?,?,?,?,?)',
                       (cid,e['field'],json.dumps(e.get('value')),canonical_url(e['source_url']),e['excerpt'],e['retrieved_at'],e['status'],e['independence_group']))
            # Additional provenance is append-only. Agent review cannot attest facts.
            metadata = {k:e[k] for k in ('knowledge_status','source_type','subject_confirmed',
                        'original_date','original_date_verified','signal_polarity','date_basis','identity_confidence') if k in e}
            metadata['human_verified'] = record.get('reviewed_by_human') is True and e.get('human_verified') is True
            eid = db.execute('SELECT id,value FROM evidence WHERE candidate_id=? AND field=? AND source_url=? AND excerpt=?',
                             (cid,e['field'],canonical_url(e['source_url']),e['excerpt'])).fetchone()
            if eid['value'] != json.dumps(e.get('value')):
                raise StopRun('Same evidence excerpt cannot support a changed value; supply distinct evidence')
            if len(metadata) > 1:
                db.execute('INSERT OR IGNORE INTO qualification_annotations VALUES(?,?)', (eid['id'],json.dumps(metadata)))
        for field,value in facts.items():
            if field in FIELDS:
                db.execute('UPDATE candidates SET '+field+'=? WHERE id=?', (json.dumps(value) if isinstance(value,(dict,list)) else value,cid))
        for c in record.get('contacts',[]):
            if not c.get('public_professional') or c['route_type'] not in ('public_professional_email','public_business_phone','professional_profile') or c['status'] not in STATUSES:
                raise StopRun('Contact must be a public professional route')
            db.execute('INSERT OR IGNORE INTO contacts(candidate_id,route_type,value,source_url,retrieved_at,status) VALUES(?,?,?,?,?,?)',
                       (cid,c['route_type'],c['value'],canonical_url(c['source_url']),c['retrieved_at'],c['status']))
        # The run's policy travels with the candidate so re-assessment on read
        # applies the same localities and signal window the reviewer worked under.
        stored = stored_policy(db, cid)
        effective = normalize_policy(policy) if policy is not None else stored
        assessment = candidate_assessment(db, cid, policy=effective)
        if record.get('assessment', {}).get('classification') in ('A', 'B') and assessment['classification'] != 'FULLY_QUALIFIED':
            raise StopRun('A/B import requires full evidence-based commercial qualification: ' + '; '.join(assessment['blockers']))
        reasons = [c['reason'] for c in assessment['components'].values()]
        db.execute('UPDATE candidates SET qualification_score=?,confidence_score=?,contactability=?,notes=? WHERE id=?',
                   (assessment['score'],assessment['confidence_score'],'PUBLIC_ROUTE_FOUND' if assessment['components']['contact']['score'] else 'UNKNOWN',json.dumps({'scoring':reasons,'qualification':assessment,'reviewer':reviewer,'operator_notes':record.get('notes',''),'policy':effective}),cid))
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK'); raise
    return cid


def score_candidate(facts, evidence=(), contacts=(), *, as_of=None):
    """Compatibility tuple API; unsupported flat facts cannot earn evidence points."""
    result = assess_candidate(facts, evidence, contacts, as_of=as_of)
    return result['score'], [c['reason'] for c in result['components'].values()]


def stored_policy(db, cid):
    row = db.execute('SELECT notes FROM candidates WHERE id=?', (cid,)).fetchone()
    try:
        notes = json.loads(row['notes'] or '{}') if row else {}
        return normalize_policy(notes.get('policy')) if isinstance(notes, dict) and notes.get('policy') else None
    except (ValueError, TypeError):
        return None


def candidate_assessment(db, cid, *, as_of=None, policy=None):
    if policy is None: policy = stored_policy(db, cid)
    rows = []
    for row in db.execute('SELECT e.*,a.metadata_json FROM evidence e LEFT JOIN qualification_annotations a ON a.evidence_id=e.id WHERE candidate_id=? ORDER BY e.id', (cid,)):
        e = dict(row)
        e['value'] = json.loads(e['value']) if e['value'] is not None else None
        e.update(json.loads(e.pop('metadata_json') or '{}'))
        rows.append(e)
    return assess_candidate({}, rows, [dict(c) for c in db.execute('SELECT * FROM contacts WHERE candidate_id=?', (cid,))], as_of=as_of, policy=policy)


def report(db, run_id, *, as_of=None):
    # Re-evaluate on read so yesterday's score cannot hide today's stale signal.
    candidates = []
    for row in db.execute('SELECT * FROM candidates'):
        candidate = dict(row)
        q = candidate_assessment(db, candidate['id'], as_of=as_of)
        candidate.update(qualification=q, qualification_score=q['score'], confidence_score=q['confidence_score'],
                         contactability='PUBLIC_ROUTE_FOUND' if q['components']['contact']['score'] else 'UNKNOWN')
        try:
            notes = json.loads(candidate.get('notes') or '{}')
            if isinstance(notes, dict):
                notes['qualification'] = q
                candidate['notes'] = json.dumps(notes)
        except (ValueError, TypeError):
            pass  # Retain legacy free-text operator notes.
        candidates.append(candidate)
    candidates.sort(key=ranking_key)
    return {'run_id':run_id,'human_review_required':True,'outreach_enabled':False,
            'notice':'Discovery leads are not verified prospects. Scores support research review only; no hiring decision.',
            'candidates':candidates,
            'evidence':[dict(r) for r in db.execute('SELECT * FROM evidence')],
            'contacts':[dict(r) for r in db.execute('SELECT * FROM contacts')],
            'discovery':[dict(r) for r in db.execute("SELECT * FROM discoveries WHERE run_id=? AND stage!='PROVIDER_LIMIT_RESPONSE'",(run_id,))]}
