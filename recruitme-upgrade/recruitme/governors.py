"""Independent, persistent runtime, resource, provider-health and progress controls.

No method in this module creates spend or changes monetary budgets.
"""
import datetime
import hashlib
import json
import shutil
import time
from pathlib import Path


class StopRun(Exception):
    code = 'GUARD_STOP'


class ProviderLimitReached(StopRun):
    code = 'PROVIDER_LIMIT_REACHED'


class CodedStop(StopRun):
    def __str__(self):
        return self.code + ': ' + super().__str__()


class BudgetLimitReached(CodedStop):
    code = 'BUDGET_LIMIT_REACHED'


class LocalRequestLimitReached(CodedStop):
    code = 'LOCAL_REQUEST_LIMIT_REACHED'


class RuntimeLimitReached(CodedStop):
    code = 'RUNTIME_LIMIT_REACHED'


def stop_code(reason, state='STOPPED'):
    if state == 'COMPLETE':
        return 'NORMAL_COMPLETION'
    if isinstance(reason, StopRun) and reason.code != 'GUARD_STOP':
        return reason.code
    prefix = str(reason).split(':', 1)[0]
    if prefix in ('BUDGET_LIMIT_REACHED', 'LOCAL_REQUEST_LIMIT_REACHED',
                  'PROVIDER_LIMIT_REACHED', 'RUNTIME_LIMIT_REACHED',
                  'CANDIDATE_TARGET_REACHED', 'NO_ELIGIBLE_PROVIDER'):
        return prefix
    return 'GUARD_STOP' if isinstance(reason, (str, StopRun)) else 'FAILURE'


class Governance:
    def initialize_governance(self):
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS runtime_sessions(
          id TEXT PRIMARY KEY, created REAL NOT NULL, session_deadline REAL NOT NULL,
          status TEXT NOT NULL DEFAULT 'ACTIVE');
        CREATE TRIGGER IF NOT EXISTS immutable_runtime_deadline
        BEFORE UPDATE OF created,session_deadline ON runtime_sessions
        WHEN NEW.created!=OLD.created OR NEW.session_deadline!=OLD.session_deadline
        BEGIN SELECT RAISE(ABORT,'Immutable runtime session deadline'); END;
        CREATE TABLE IF NOT EXISTS runtime_bindings(
          run_id TEXT PRIMARY KEY REFERENCES runs(id), runtime_id TEXT NOT NULL REFERENCES runtime_sessions(id));
        CREATE TRIGGER IF NOT EXISTS immutable_runtime_binding
        BEFORE UPDATE ON runtime_bindings BEGIN SELECT RAISE(ABORT,'Immutable runtime binding'); END;
        CREATE TABLE IF NOT EXISTS provider_health(
          provider TEXT PRIMARY KEY, status TEXT NOT NULL, first_observed_at REAL NOT NULL,
          first_operation_id TEXT);
        CREATE TABLE IF NOT EXISTS operation_outcomes(
          operation_id TEXT PRIMARY KEY REFERENCES operations(id), observed_at REAL NOT NULL,
          status TEXT NOT NULL, response_json TEXT, response_sha256 TEXT);
        CREATE TABLE IF NOT EXISTS resource_observations(
          id INTEGER PRIMARY KEY, run_id TEXT, observed_at REAL NOT NULL,
          disk_free_bytes INTEGER, state_bytes INTEGER, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candidate_stop_rules(
          runtime_id TEXT PRIMARY KEY REFERENCES runtime_sessions(id), target INTEGER NOT NULL CHECK(target BETWEEN 1 AND 10));
        CREATE TABLE IF NOT EXISTS qualified_progress(
          runtime_id TEXT NOT NULL REFERENCES runtime_sessions(id), identity_key TEXT NOT NULL,
          classification TEXT NOT NULL, evidence_json TEXT NOT NULL,
          PRIMARY KEY(runtime_id,identity_key));
        CREATE TABLE IF NOT EXISTS job_manifests(
          run_id TEXT PRIMARY KEY REFERENCES runs(id), manifest_sha256 TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS governor_migrations(id TEXT PRIMARY KEY, applied_at REAL NOT NULL);
        ''')
        # One-time restoration from the original independently persisted Run #3 window.
        # Monetary history and raw evidence are never changed by this migration.
        with self.transaction():
            if not self.db.execute("SELECT 1 FROM governor_migrations WHERE id='independent-v1'").fetchone():
                for w in self.db.execute('SELECT * FROM research_windows').fetchall():
                    self.db.execute('INSERT OR IGNORE INTO runtime_sessions(id,created,session_deadline) VALUES(?,?,?)',
                                    (w['id'],w['created'],w['deadline']))
                    if w['id']=='deep-search-run3':
                        for r in self.db.execute("SELECT * FROM runs WHERE id LIKE 'run3-%'").fetchall():
                            self.db.execute('INSERT OR IGNORE INTO runtime_bindings VALUES(?,?)',(r['id'],w['id']))
                            if r['deadline']>w['deadline']:
                                self.event(r['id'],'DEADLINE_COLLISION_REPAIRED',json.dumps({'previous_batch_deadline':r['deadline'],'original_shared_deadline':w['deadline']}))
                                self.db.execute('UPDATE runs SET deadline=? WHERE id=?',(w['deadline'],r['id']))
                for e in self.db.execute("SELECT * FROM audit WHERE event='PROVIDER_RATE_LIMIT' ORDER BY timestamp").fetchall():
                    self.db.execute('INSERT OR IGNORE INTO provider_health VALUES(?,?,?,NULL)',(e['detail'],'PROVIDER_LIMIT_REACHED',e['timestamp']))
                self.db.execute('INSERT INTO governor_migrations VALUES(?,?)',('independent-v1',time.time()))
        self.db.executescript('''
        CREATE TRIGGER IF NOT EXISTS immutable_batch_deadline BEFORE UPDATE OF created,deadline ON runs
        WHEN NEW.created!=OLD.created OR NEW.deadline!=OLD.deadline
        BEGIN SELECT RAISE(ABORT,'Immutable batch deadline'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_budget_expiry BEFORE UPDATE OF deadline,created ON sessions
        WHEN NEW.deadline!=OLD.deadline OR NEW.created!=OLD.created
        BEGIN SELECT RAISE(ABORT,'Immutable budget window expiry'); END;
        CREATE TRIGGER IF NOT EXISTS no_budget_increase BEFORE UPDATE OF cap,high_value_after ON sessions
        WHEN NEW.cap>OLD.cap OR NEW.high_value_after>OLD.high_value_after
        BEGIN SELECT RAISE(ABORT,'Budget cannot increase'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_run_budget BEFORE UPDATE OF cap,session_id ON runs
        WHEN NEW.cap!=OLD.cap OR NEW.session_id IS NOT OLD.session_id
        BEGIN SELECT RAISE(ABORT,'Immutable run budget binding'); END;
        ''')

    def initialize_runtime(self, runtime_id):
        """Called only for an explicit new job; existing identity never renews."""
        now=time.time()
        duration=min(1800,int(self.config['max_run_seconds']))
        if duration<=0: raise StopRun('Invalid runtime duration')
        self.db.execute('INSERT OR IGNORE INTO runtime_sessions(id,created,session_deadline) VALUES(?,?,?)',
                        (runtime_id,now,now+duration))
        runtime=self.db.execute('SELECT * FROM runtime_sessions WHERE id=?',(runtime_id,)).fetchone()
        if runtime['status']!='ACTIVE' or now>=runtime['session_deadline']:
            raise RuntimeLimitReached('Original session deadline expired or runtime closed')
        target=int(self.config.get('candidate_stop_target',10))
        if not 1<=target<=10: raise StopRun('Invalid candidate stopping target')
        self.db.execute('INSERT OR IGNORE INTO candidate_stop_rules VALUES(?,?)',(runtime_id,target))
        return runtime

    def runtime_for(self, run_id):
        return self.db.execute('SELECT s.* FROM runtime_sessions s JOIN runtime_bindings b ON b.runtime_id=s.id WHERE b.run_id=?',(run_id,)).fetchone()

    def check_runtime(self, run):
        runtime=self.runtime_for(run['id'])
        if time.time()>=run['deadline'] or (runtime and (runtime['status']!='ACTIVE' or time.time()>=runtime['session_deadline'])):
            raise RuntimeLimitReached('Original runtime deadline reached')

    def check_candidate_stop(self, run_id):
        runtime=self.runtime_for(run_id)
        if not runtime:return
        target=self.db.execute('SELECT target FROM candidate_stop_rules WHERE runtime_id=?',(runtime['id'],)).fetchone()
        count=self.db.execute("SELECT COUNT(*) FROM qualified_progress WHERE runtime_id=? AND classification IN ('A','B')",(runtime['id'],)).fetchone()[0]
        if target and count>=target[0]:raise StopRun('CANDIDATE_TARGET_REACHED')

    def record_qualification(self, run_id, identity_key, assessment):
        runtime=self.runtime_for(run_id)
        if not runtime or not identity_key:raise StopRun('Qualification requires runtime and stable identity')
        classification=assessment.get('classification')
        if classification not in ('A','B','C','PASSIVE_RESEARCH_POOL','REJECT'):raise StopRun('Invalid qualification category')
        if classification in ('A','B'):
            if not all(assessment.get(k) is True for k in ('signal_subject_confirmed','signal_date_verified','contradictions_checked')):
                raise StopRun('A/B requires attributed signal, verified signal date and contradiction review')
            if not all(assessment.get(k) is True for k in ('reviewed','trade_fit','identified_person','geographic_fit')):
                raise StopRun('A/B requires reviewed identity, trade and geographic evidence')
            if not assessment.get('recruiting_signal') or not assessment.get('source_urls') or not assessment.get('signal_date'):
                raise StopRun('A/B requires dated recruiting evidence')
            try:age=(datetime.datetime.now(datetime.timezone.utc).date()-datetime.date.fromisoformat(assessment['signal_date'])).days
            except ValueError:raise StopRun('Invalid recruiting-signal date') from None
            if age<0 or age>365 or (age>180 and not assessment.get('compelling_freshness_evidence')):
                raise StopRun('Recruiting signal insufficiently current for A/B')
        self.db.execute('INSERT INTO qualified_progress VALUES(?,?,?,?) ON CONFLICT(runtime_id,identity_key) DO UPDATE SET classification=excluded.classification,evidence_json=excluded.evidence_json',
                        (runtime['id'],identity_key,classification,json.dumps(assessment)))

    def check_resources(self, run_id):
        if self.state_root is None:return
        try:
            free=shutil.disk_usage(self.state_root).free
            size=sum(p.stat().st_size for p in Path(self.state_root).rglob('*') if p.is_file())
        except OSError:raise StopRun('RESOURCE_MEASUREMENT_FAILED') from None
        status='OK'
        if free<max(2147483648,int(self.config['minimum_disk_free_bytes'])):status='DISK_LIMIT_REACHED'
        elif size>min(1073741824,int(self.config.get('maximum_state_bytes',1073741824))):status='STATE_STORAGE_LIMIT_REACHED'
        self.db.execute('INSERT INTO resource_observations(run_id,observed_at,disk_free_bytes,state_bytes,status) VALUES(?,?,?,?,?)',
                        (run_id,time.time(),free,size,status))
        if status!='OK':raise StopRun(status)

    def provider_limited(self, provider):
        return bool(self.db.execute("SELECT 1 FROM provider_health WHERE provider=? AND status='PROVIDER_LIMIT_REACHED'",(provider,)).fetchone())

    def save_outcome(self, operation_id, status, response=None, observed_at=None):
        """Durable receipt independent of billing reconciliation (crash safe)."""
        if status not in ('SUCCESS','ERROR','UNKNOWN','PROVIDER_LIMIT_REACHED'):
            raise StopRun('Invalid provider outcome')
        stamp=time.time() if observed_at is None else observed_at
        encoded=None if response is None else json.dumps(response,sort_keys=True,ensure_ascii=True)
        digest=None if encoded is None else hashlib.sha256(encoded.encode()).hexdigest()
        with self.transaction():
            self.db.execute('INSERT OR IGNORE INTO operation_outcomes VALUES(?,?,?,?,?)',(operation_id,stamp,status,encoded,digest))
            op=self.db.execute('SELECT * FROM operations WHERE id=?',(operation_id,)).fetchone()
            if status=='PROVIDER_LIMIT_REACHED':
                self.db.execute('INSERT INTO provider_health VALUES(?,?,?,?) ON CONFLICT(provider) DO UPDATE SET status=excluded.status,first_observed_at=MIN(provider_health.first_observed_at,excluded.first_observed_at),first_operation_id=CASE WHEN excluded.first_observed_at<provider_health.first_observed_at OR provider_health.first_operation_id IS NULL THEN excluded.first_operation_id ELSE provider_health.first_operation_id END',
                                (op['provider'],status,stamp,operation_id))
                self.event(op['run_id'],status,json.dumps({'provider':op['provider'],'operation_id':operation_id,'operation':op['operation'],'observed_at':stamp}))

    def cached_search(self, run_id, provider, logical_id):
        runtime=self.runtime_for(run_id)
        if not runtime:return None
        row=self.db.execute("SELECT x.*,o.state AS billing_state FROM operation_outcomes x JOIN operations o ON o.id=x.operation_id JOIN runtime_bindings b ON b.run_id=o.run_id WHERE b.runtime_id=? AND o.provider=? AND o.operation='search' AND o.logical_id=? AND x.status='SUCCESS' ORDER BY x.observed_at LIMIT 1",
                            (runtime['id'],provider,logical_id)).fetchone()
        if row:
            # A receipt without reconciliation remains reserved, but never needs resending.
            return dict(response=json.loads(row['response_json']),observed_at=row['observed_at'],operation_id=row['operation_id'])
        uncertain=self.db.execute("SELECT 1 FROM operations o JOIN runtime_bindings b ON b.run_id=o.run_id WHERE b.runtime_id=? AND o.provider=? AND o.operation='search' AND o.logical_id=? AND o.state IN ('RESERVED','UNKNOWN') LIMIT 1",(runtime['id'],provider,logical_id)).fetchone()
        if uncertain:raise StopRun('UNCERTAIN_REQUEST_REQUIRES_REVIEW; no automatic duplicate')
        return None

    def bind_manifest(self, run_id, job):
        content=dict(job);content.pop('resume',None)
        digest=hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()
        self.db.execute('INSERT OR IGNORE INTO job_manifests VALUES(?,?)',(run_id,digest))
        if self.db.execute('SELECT manifest_sha256 FROM job_manifests WHERE run_id=?',(run_id,)).fetchone()[0]!=digest:
            raise StopRun('Resume job differs from original manifest')
