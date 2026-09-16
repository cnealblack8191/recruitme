"""Deterministic fail-closed accounting. USD stored as integer microdollars.

Reservations survive crashes. Unknown results retain their full reservation.
No model or retrieved text may supply configuration, prices, or reconciliation.
"""
import json
import sqlite3
import time
import uuid
import datetime
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation


from .governors import (Governance, StopRun, ProviderLimitReached,
                        BudgetLimitReached, LocalRequestLimitReached, RuntimeLimitReached, stop_code)


def money(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0 or d * 1000000 != (d * 1000000).to_integral_value():
            raise ValueError()
        return int(d * 1000000)
    except (InvalidOperation, ValueError, TypeError):
        raise StopRun('Invalid monetary amount') from None


class Ledger(Governance):
    def __init__(self, path, config, state_root=None):
        self.config = config
        self.state_root = state_root
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS runs(
          id TEXT PRIMARY KEY, cap INTEGER NOT NULL, created REAL NOT NULL,
          deadline REAL NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS operations(
          id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
          timestamp REAL NOT NULL, provider TEXT NOT NULL, operation TEXT NOT NULL,
          logical_id TEXT NOT NULL, attempt INTEGER NOT NULL,
          reserved INTEGER NOT NULL, actual INTEGER, request_id TEXT,
          state TEXT NOT NULL, cumulative_at_reserve INTEGER NOT NULL,
          cumulative_at_reconcile INTEGER,
          UNIQUE(run_id,provider,operation,logical_id,attempt));
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY, timestamp REAL NOT NULL, run_id TEXT,
          event TEXT NOT NULL, detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(
          id TEXT PRIMARY KEY, cap INTEGER NOT NULL, high_value_after INTEGER NOT NULL,
            deadline REAL NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS research_windows(
            id TEXT PRIMARY KEY, created REAL NOT NULL, deadline REAL NOT NULL);
        ''')
        if 'session_id' not in [r[1] for r in self.db.execute('PRAGMA table_info(runs)')]:
            self.db.execute('ALTER TABLE runs ADD COLUMN session_id TEXT REFERENCES sessions(id)')
        self.initialize_governance()

    def session_total(self, session_id):
        return self.db.execute('SELECT COALESCE(SUM(COALESCE(o.actual,o.reserved)),0) FROM operations o JOIN runs r ON r.id=o.run_id WHERE r.session_id=?',
                               (session_id,)).fetchone()[0]

    def session_for(self, run):
        if run['session_id'] is None:
            return None
        return self.db.execute('SELECT * FROM sessions WHERE id=?',(run['session_id'],)).fetchone()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def event(self, run_id, event, detail):
        self.db.execute('INSERT INTO audit(timestamp,run_id,event,detail) VALUES(?,?,?,?)',
                        (time.time(), run_id, event, detail))

    def total(self, run_id=None, provider=None):
        where, args = [], []
        if run_id is not None:
            where.append('run_id=?'); args.append(run_id)
        if provider is not None:
            where.append('provider=?'); args.append(provider)
        return self.db.execute('SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM operations' +
                               (' WHERE ' + ' AND '.join(where) if where else ''), args).fetchone()[0]

    def initialize_budget(self):
        session = self.config.get('session')
        if not session:
            return None
        sid = session['id']
        limit = min(money(session['limit_usd']), money('25'))
        threshold = min(money(session['high_value_only_after_usd']), money('20'), limit)
        budget_expires_at = datetime.datetime.fromisoformat(session['ends_at']).timestamp()
        self.db.execute('INSERT OR IGNORE INTO sessions VALUES(?,?,?,?,?)',
                        (sid,limit,threshold,budget_expires_at,time.time()))
        persisted = self.db.execute('SELECT * FROM sessions WHERE id=?',(sid,)).fetchone()
        self.db.execute('UPDATE sessions SET cap=?,high_value_after=? WHERE id=?',
                        (min(limit,persisted['cap']),min(threshold,persisted['high_value_after']),sid))
        if time.time() >= persisted['deadline']:
            raise RuntimeLimitReached('Budget window expired; no automatic renewal')
        return sid

    def create_run(self, run_id, cap=None, resume=False):
        cap = money(cap if cap is not None else self.config['default_run_limit_usd'])
        if cap > min(money(self.config['default_run_limit_usd']), money(self.config['poc_limit_usd']), money('100')):
            raise BudgetLimitReached('Run cap exceeds configured ceilings')
        with self.transaction():
            existing = self.db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
            if existing:
                if not resume:
                    raise StopRun('Run ID already exists; explicit resume required')
                self.check_runtime(existing)
                if cap != existing['cap']:
                    raise StopRun('Resume cannot change run budget')
                if existing['status'] == 'COMPLETE':
                    return
                self.db.execute("UPDATE runs SET status='RUNNING' WHERE id=?",(run_id,))
                self.check(run_id)
                self.event(run_id,'RESUME','Original runtime, budget, requests and evidence preserved')
                return
            runtime = self.initialize_runtime(self.config.get('research_window_id') or run_id)
            sid = self.initialize_budget()
            self.db.execute('INSERT INTO runs(id,cap,created,deadline,status,session_id) VALUES(?,?,?,?,?,?)',
                            (run_id,cap,time.time(),runtime['session_deadline'],'RUNNING',sid))
            self.db.execute('INSERT INTO runtime_bindings VALUES(?,?)',(run_id,runtime['id']))
            self.event(run_id,'START','Independent persistent governors bound')

    def stop(self, run_id, reason, state='STOPPED'):
        self.db.execute('UPDATE runs SET status=? WHERE id=?', (state, run_id))
        self.event(run_id, state, str(reason))
        self.event(run_id, 'RUN_TERMINATION', json.dumps({
            'code': stop_code(reason, state), 'reason': str(reason), 'status': state}))

    def check(self, run_id, *, reserved_operation=None):
        # Only a live reservation may dispatch at an exact cap. This never
        # subtracts spend or creates headroom for another operation.
        dispatch = reserved_operation is not None
        if dispatch:
            op = self.db.execute('SELECT * FROM operations WHERE id=? AND run_id=?', (reserved_operation,run_id)).fetchone()
            if not op or op['state']!='RESERVED':raise StopRun('Invalid dispatch reservation')
            if self.db.execute('SELECT 1 FROM audit WHERE event=? AND detail=?',('NETWORK_DISPATCH',reserved_operation)).fetchone():
                raise StopRun('Reservation already dispatched; no retry')
            p=self.config['providers'].get(op['provider'],{})
            if not p.get('enabled') or money(p.get('operations',{}).get(op['operation']))!=op['reserved']:
                raise StopRun('Provider changed after reservation')
            if op['reserved'] and (not p.get('approved') or not self.config.get('paid_enabled')):raise StopRun('Paid provider disabled')
            if self.provider_limited(op['provider']):raise ProviderLimitReached('PROVIDER_LIMIT_REACHED')
            if self.total(provider=op['provider'])>money(p['poc_limit_usd']) or self.total(run_id,op['provider'])>money(p['run_limit_usd']):raise BudgetLimitReached('Provider budget exceeded')
            for sql,args,limit in [('SELECT COUNT(*) FROM operations WHERE provider=?',(op['provider'],),p['poc_query_limit']),('SELECT COUNT(*) FROM operations WHERE provider=? AND run_id=?',(op['provider'],run_id),p['run_query_limit'])]:
                if self.db.execute(sql,args).fetchone()[0]>limit:raise LocalRequestLimitReached('Application provider request limit exceeded')
        if self.db.execute("SELECT 1 FROM audit WHERE event='PRICE_BREACH' LIMIT 1").fetchone():
            raise StopRun('Price breach freeze requires operator investigation')
        run = self.db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if not run or run['status'] != 'RUNNING':
            raise StopRun('Run missing, stopped, or expired')
        self.check_runtime(run)
        self.check_resources(run_id)
        self.check_candidate_stop(run_id)
        def exhausted(value,cap):return value>cap if dispatch else value>=cap
        free_only = run['cap'] == 0 and not self.config.get('paid_enabled')
        if exhausted(self.total(),min(money(self.config['poc_limit_usd']), money('100'))) or (not free_only and exhausted(self.total(run_id),run['cap'])) or (free_only and self.total(run_id) > 0):
            raise BudgetLimitReached('Budget exhausted')
        session=self.session_for(run)
        if session and time.time()>=session['deadline']:
            raise RuntimeLimitReached('Session budget window expired')
        if session and exhausted(self.session_total(session['id']),session['cap']):
            raise BudgetLimitReached('Session budget exhausted')
        if dispatch and session and op['reserved'] and self.session_total(session['id'])>session['high_value_after'] and p.get('operation_purposes',{}).get(op['operation'])!='high_value':
            raise BudgetLimitReached('Final $5 restricted to high-value research')
        return run

    def dispatch(self, run_id, operation_id):
        with self.transaction():
            run=self.check(run_id,reserved_operation=operation_id)
            self.event(run_id,'NETWORK_DISPATCH',operation_id)
            return run

    def reserve(self, run_id, provider, operation, logical_id):
        try:
            with self.transaction():
                run = self.check(run_id)
                if self.provider_limited(provider):
                    raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: '+provider)
                p = self.config['providers'].get(provider)
                if not p or not p.get('enabled') or operation not in p.get('operations', {}):
                    raise StopRun('Disabled or unpriced provider operation')
                for field in ('poc_query_limit', 'run_query_limit', 'max_attempts'):
                    if type(p.get(field)) is not int or p[field] < 0:
                        raise StopRun('Invalid application request ceiling: '+field)
                # Serialize duplicate detection with reservation, including crashes
                # between cache lookup and dispatch. Never resend a search receipt.
                if operation == 'search':
                    runtime = self.runtime_for(run_id)
                    prior = self.db.execute('SELECT 1 FROM operations o JOIN runtime_bindings b ON b.run_id=o.run_id WHERE b.runtime_id=? AND o.provider=? AND o.operation=? AND o.logical_id=? LIMIT 1',
                        (runtime['id'], provider, operation, logical_id)).fetchone()
                    if prior:
                        raise LocalRequestLimitReached('Duplicate search blocked; use durable receipt or operator review')
                cost = money(p['operations'][operation])
                if provider == 'brave':
                    # A rolling 31-day ceiling cannot reset before a monthly
                    # credit period. Count reservations and uncertain requests.
                    used = self.db.execute('SELECT COALESCE(SUM(MAX(reserved,COALESCE(actual,0))),0) FROM operations WHERE provider=? AND timestamp>=?',
                        (provider,time.time()-31*86400)).fetchone()[0]
                    if used + cost > money('5'):
                        raise BudgetLimitReached('Brave local $5 rolling allowance exhausted')
                if cost > 0 and (not self.config.get('paid_enabled', False) or not p.get('approved', False)):
                    raise StopRun('Paid operations disabled')
                session=self.session_for(run)
                if session:
                    committed=self.session_total(session['id'])
                    if committed+cost>session['cap']:
                        raise BudgetLimitReached('Session $25 hard limit exceeded')
                    purpose=p.get('operation_purposes',{}).get(operation,'standard')
                    if cost>0 and committed+cost>session['high_value_after'] and purpose!='high_value':
                        raise BudgetLimitReached('Final $5 reserved for high-value operations; optional enrichment disabled')
                # Even zero-cost operations cannot continue after global/run exhaustion.
                if self.total() + cost > min(money(self.config['poc_limit_usd']), money('100')):
                    raise BudgetLimitReached('POC budget exceeded')
                if self.total(run_id) + cost > run['cap']:
                    raise BudgetLimitReached('Run budget exceeded')
                if self.total(provider=provider) + cost > money(p['poc_limit_usd']):
                    raise BudgetLimitReached('Provider POC budget exceeded')
                if self.total(run_id, provider) + cost > money(p['run_limit_usd']):
                    raise BudgetLimitReached('Provider run budget exceeded')
                for sql, args, limit in [
                    ('SELECT COUNT(*) FROM operations WHERE provider=?', (provider,), p['poc_query_limit']),
                    ('SELECT COUNT(*) FROM operations WHERE provider=? AND run_id=?', (provider,run_id), p['run_query_limit'])]:
                    if self.db.execute(sql,args).fetchone()[0] >= limit:
                        raise LocalRequestLimitReached('Application provider request limit exhausted')
                attempt = self.db.execute('SELECT COUNT(*) FROM operations WHERE run_id=? AND provider=? AND operation=? AND logical_id=?',
                                          (run_id,provider,operation,logical_id)).fetchone()[0] + 1
                if operation == 'search':
                    runtime=self.runtime_for(run_id)
                    attempt=self.db.execute('SELECT COUNT(*) FROM operations o JOIN runtime_bindings b ON b.run_id=o.run_id WHERE b.runtime_id=? AND o.provider=? AND o.operation=? AND o.logical_id=?',
                                            (runtime['id'],provider,operation,logical_id)).fetchone()[0]+1
                if attempt > min(p['max_attempts'], 2):
                    raise LocalRequestLimitReached('Application attempt limit exhausted')
                op_id = str(uuid.uuid4())
                self.db.execute('INSERT INTO operations(id,run_id,timestamp,provider,operation,logical_id,attempt,reserved,state,cumulative_at_reserve) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                (op_id,run_id,time.time(),provider,operation,logical_id,attempt,cost,'RESERVED',self.total()+cost))
                return op_id
        except ProviderLimitReached:
            raise
        except StopRun as e:
            self.stop(run_id, e)
            raise

    def reconcile(self, op_id, actual=None, request_id=None):
        with self.transaction():
            op = self.db.execute('SELECT * FROM operations WHERE id=?', (op_id,)).fetchone()
            if not op or op['state'] != 'RESERVED':
                raise StopRun('Operation cannot be reconciled twice')
            value = None if actual is None else money(actual)
            if value is not None and value > op['reserved']:
                # Preserve actual liability and freeze ALL active runs. Never hide overspend.
                self.db.execute("UPDATE runs SET status='STOPPED' WHERE status='RUNNING'")
                self.event(op['run_id'], 'PRICE_BREACH', 'Actual charge exceeded reserved maximum')
            self.db.execute('UPDATE operations SET actual=?,request_id=?,state=? WHERE id=?',
                            (value, request_id, 'UNKNOWN' if value is None else 'RECONCILED', op_id))
            self.db.execute('UPDATE operations SET cumulative_at_reconcile=? WHERE id=?', (self.total(),op_id))

    def summary(self):
        return {'committed_usd': str(Decimal(self.total())/1000000),
                'terminations':[dict(r, **json.loads(r['detail'])) for r in self.db.execute("SELECT run_id,timestamp,detail FROM audit WHERE event='RUN_TERMINATION' AND id IN (SELECT MAX(id) FROM audit WHERE event='RUN_TERMINATION' GROUP BY run_id)")],
                'sessions':[dict(s,committed_usd=str(Decimal(self.session_total(s['id']))/1000000)) for s in self.db.execute('SELECT * FROM sessions')],
                'operations': self.db.execute('SELECT COUNT(*) FROM operations').fetchone()[0],
                'runs': [dict(r) for r in self.db.execute('SELECT * FROM runs')]}
