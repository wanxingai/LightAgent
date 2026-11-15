"""Single-host transactional control store. No model code is loaded from records."""
from __future__ import annotations
from contextlib import contextmanager
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from .legacy_storage import LEGACY_IMMUTABLE_KINDS, read_control_limits


def uid():
    return uuid4().hex


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class StateConflict(RuntimeError):
    pass


class RecordBudgetExceeded(ValueError):
    """A durable inbox write must wait for the host to free record capacity."""


class ControlStore:
    immutable_kinds = frozenset()

    def __init__(self, root=None):
        self.root = Path(root or (Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local'/'state'))/'lightagent'/'service')).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_mode & 0o077:
            raise PermissionError('service directory must have mode 0700')
        self.path = self.root/'control.sqlite3'
        initialized = False
        if self.path.exists():
            with self.read_transaction() as db:
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0, 1):
                    raise StateConflict('unsupported persistent schema; preserve database before migration')
                schema = set(db.execute("SELECT type,name FROM sqlite_master WHERE name IN ('records','events','records_agent','events_agent')").fetchall())
                initialized = version == 1 and {('table','records'),('table','events'),
                    ('index','records_agent'),('index','events_agent')} <= {tuple(row) for row in schema}
        if not initialized:
            with self.transaction() as db:
                version = db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0, 1):
                    raise StateConflict('unsupported persistent schema; preserve database before migration')
                db.execute('CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,agent TEXT,revision INTEGER,body TEXT, PRIMARY KEY(kind,id))')
                db.execute('CREATE INDEX IF NOT EXISTS records_agent ON records(kind,agent)')
                db.execute('CREATE TABLE IF NOT EXISTS events(sequence INTEGER PRIMARY KEY AUTOINCREMENT,agent TEXT,type TEXT,body TEXT,created REAL)')
                db.execute('CREATE INDEX IF NOT EXISTS events_agent ON events(agent,sequence)')
                db.execute('PRAGMA user_version=1')
        os.chmod(self.path, 0o600)

    @contextmanager
    def read_transaction(self):
        """Read a consistent snapshot without reserving the only writer slot."""
        # SQLite may need to roll back a hot journal even for the first read.
        # Keep SQL query-only without forbidding the pager's crash recovery.
        db = sqlite3.connect(self.path.as_uri()+'?mode=rw', uri=True, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA busy_timeout=10000')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, kind, key, db=None):
        if db is None:
            with self.read_transaction() as db:
                return self.get(kind, key, db)
        row = db.execute('SELECT body,revision FROM records WHERE kind=? AND id=?', (kind,key)).fetchone()
        return {**json.loads(row['body']), 'revision': row['revision']} if row else None

    def list(self, kind, agent=None, db=None, limit=1000):
        if db is None:
            with self.read_transaction() as db:
                return self.list(kind, agent, db, limit)
        sql = 'SELECT body,revision FROM records WHERE kind=?'
        params = [kind]
        if agent is not None:
            sql += ' AND agent=?'
            params.append(agent)
        sql += ' ORDER BY rowid DESC LIMIT ?'
        params.append(min(max(int(limit),1),10000))
        return [{**json.loads(r['body']), 'revision':r['revision']} for r in db.execute(sql,params)]

    def page(self, kind, agent, *, cursor=None, limit=50, query=None):
        if query is not None:
            from ..extensions import legacy_export
            return legacy_export("research_page")(self, kind, agent, cursor=cursor, limit=limit, query=query)
        return self._page(kind, agent, cursor=cursor, limit=limit)

    def _page(self, kind, agent, *, cursor, limit, cursor_query='', row_filter=None):
        """Newest-first keyset pages; later inserts cannot shift older pages.

        Cursors describe a query boundary, not an authorization capability.
        Every query binds both kind and owner. Only trusted Python extensions
        supply SQL predicates; query text is passed as bound values.
        """
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError('page limit must be between 1 and 200')
        scope = hashlib.sha256(dumps([kind, agent, cursor_query]).encode()).hexdigest()
        boundary = None
        if cursor is not None:
            try:
                if not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024:
                    raise ValueError()
                boundary = json.loads(base64.b64decode(cursor.encode('ascii'), altchars=b'-_', validate=True))
                if (set(boundary) != {'v', 'scope', 'upper', 'before'} or boundary['v'] != 1
                        or boundary['scope'] != scope
                        or any(type(boundary[k]) is not int for k in ('upper', 'before'))
                        or not 0 < boundary['before'] <= boundary['upper'] < 2**63):
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError):
                raise ValueError('invalid cursor or cursor belongs to another query') from None
        with self.read_transaction() as db:
            upper = boundary['upper'] if boundary else db.execute('SELECT coalesce(max(rowid),0) FROM records').fetchone()[0]
            clauses, params = ['kind=?', 'agent=?', 'rowid<=?'], [kind, agent, upper]
            if row_filter is not None:
                condition, values = row_filter(db)
                clauses.append(condition)
                params.extend(values)
            where = ' AND '.join(clauses)
            total = db.execute('SELECT count(*) FROM records WHERE '+where, params).fetchone()[0]
            if boundary:
                where += ' AND rowid<?'
                params.append(boundary['before'])
            rows = db.execute('SELECT rowid,body,revision FROM records WHERE '+where+' ORDER BY rowid DESC LIMIT ?',
                              [*params, limit+1]).fetchall()
            has_more = len(rows) > limit
            rows = rows[:limit]
            next_cursor = None
            if has_more:
                value = {'v': 1, 'scope': scope, 'upper': upper, 'before': rows[-1]['rowid']}
                next_cursor = base64.urlsafe_b64encode(dumps(value).encode()).decode('ascii')
            return {'items': [{**json.loads(r['body']), 'revision': r['revision']} for r in rows],
                    'next_cursor': next_cursor, 'has_more': has_more, 'total': total, 'limit': limit}

    def put(self, kind, value, db, *, expected=None):
        value = dict(value)
        revision = value.pop('revision', 0)
        if expected is None:
            expected = revision
        if expected != 0 and (kind in self.immutable_kinds or kind in LEGACY_IMMUTABLE_KINDS):
            raise StateConflict(kind+' is immutable; create a new revision')
        body = dumps(value)
        if len(body.encode()) > 2*1024*1024:
            raise ValueError('record exceeds 2 MiB')
        if expected == 0:
            try:
                db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(kind,value['id'],value.get('agent',value['id']),1,body))
            except sqlite3.IntegrityError as exc:
                raise StateConflict('record already exists') from exc
        else:
            result=db.execute('UPDATE records SET revision=revision+1,body=? WHERE kind=? AND id=? AND revision=?',(body,kind,value['id'],expected))
            if result.rowcount != 1:
                raise StateConflict('stale record revision')
        return {**value,'revision':expected+1}

    def scan(self, kind, agent=None, db=None, *, filters=None, batch_size=256):
        """Oldest-first keyset scan, with filtering BEFORE pagination.

        Bound the scan to rows present at its start. Updates retain their rowid;
        new messages are picked up by the next scheduling pass. Unlike list(),
        this is a control-plane query and never silently drops old records.
        """
        if not 1 <= batch_size <= 1000:
            raise ValueError('invalid scan batch size')
        clauses, params = ['kind=?'], [kind]
        if agent is not None:
            clauses.append('agent=?'); params.append(agent)
        for field, values in (filters or {}).items():
            if field not in ('status', 'kind', 'chat_id', 'notified'):
                raise ValueError('unsupported record filter')
            values = tuple(values)
            if not values:
                return
            clauses.append('json_extract(body, ?) IN ('+','.join('?' for _ in values)+')')
            params.extend(['$.'+field, *values])
        def page(connection, after, upper):
            return connection.execute(
                'SELECT rowid,body,revision FROM records WHERE '+ ' AND '.join(clauses)+
                ' AND rowid>? AND rowid<=? ORDER BY rowid LIMIT ?',
                [*params, after, upper, batch_size]).fetchall()
        if db is None:
            with self.read_transaction() as connection:
                upper = connection.execute('SELECT coalesce(max(rowid),0) FROM records').fetchone()[0]
        else:
            upper = db.execute('SELECT coalesce(max(rowid),0) FROM records').fetchone()[0]
        after = 0
        while True:
            if db is None:
                with self.read_transaction() as connection:
                    rows = page(connection, after, upper)
            else:
                rows = page(db, after, upper)
            if not rows:
                return
            for row in rows:
                after = row['rowid']
                yield {**json.loads(row['body']), 'revision': row['revision']}

    def event(self, agent, kind, data, db):
        body=dumps(data)
        if len(body.encode()) > 65536:
            body=dumps({'truncated':True,'reason':'event exceeds limit'})
        db.execute('INSERT INTO events(agent,type,body,created) VALUES(?,?,?,?)',(agent,kind,body,time.time()))
        owner = self.get('agent', agent, db)
        limits = read_control_limits(owner)
        limit = limits.get('max_events', 10000)
        cutoff = db.execute('SELECT sequence FROM events WHERE agent=? ORDER BY sequence DESC LIMIT 1 OFFSET ?', (agent,limit)).fetchone()
        if cutoff:
            db.execute('DELETE FROM events WHERE agent=? AND sequence<=?', (agent,cutoff[0]))
            cursor = self.get('event_cursor', agent, db) or {'id':agent,'agent':agent}
            cursor['floor'] = cutoff[0]
            self.put('event_cursor',cursor,db)

    def events(self, agent, after=0, limit=100):
        with self.read_transaction() as db:
            floor = (self.get('event_cursor',agent,db) or {}).get('floor',0)
            gap = []
            if after and int(after) < floor:
                gap = [{'sequence':floor,'agent_id':agent,'type':'cursor.expired','data':{'reload_state':True},'created_at':time.time(),'schema_version':1}]
            rows=db.execute('SELECT * FROM events WHERE agent=? AND sequence>? ORDER BY sequence LIMIT ?',
                            (agent,int(after),min(max(int(limit),1),1000))).fetchall()
            return gap + [{'sequence':r['sequence'],'agent_id':agent,'type':r['type'],'data':json.loads(r['body']),
                     'created_at':r['created'],'schema_version':1} for r in rows]

    def enqueue(self, agent, content, key=None, kind='message', chat_id=None, steering=None, *, db=None):
        if not isinstance(content,str) or not content.strip() or len(content.encode())>65536:
            raise ValueError('message must contain 1..65536 bytes')
        from .redaction import contains_secret
        if contains_secret(content):
            raise ValueError('inbox content contains a known credential; use environment credentials')
        key=key or uid()
        if not isinstance(key,str) or not 1 <= len(key) <= 256:
            raise ValueError('invalid idempotency key')
        if db is None:
            with self.transaction() as connection:
                return self.enqueue(agent, content, key, kind, chat_id, steering, db=connection)
        owner = self.get('agent', agent, db)
        if not owner:
            raise KeyError(agent)
        validate, after_insert = self._inbox_policy(owner, kind, steering)
        if validate is not None:
            validate(self, owner, kind, chat_id, steering, db)
        existing=self.get('message',key,db)
        if existing:
            if (existing['agent'],existing['content'],existing['kind'],existing.get('chat_id'),existing.get('steering')) != (agent,content,kind,chat_id,steering):
                raise StateConflict('idempotency key reused for different message')
            return existing
        if owner.get('domain') == 'execution' and owner['status'] in ('completed', 'failed', 'cancelled'):
            raise StateConflict('terminal execution cannot accept inbox work')
        count = db.execute('SELECT count(*) FROM records WHERE agent=?', (agent,)).fetchone()[0]
        limits = read_control_limits(owner)
        if count >= limits.get('max_records', 10000):
            raise RecordBudgetExceeded('inbox record budget exceeded')
        from .storage import StorageBudget
        StorageBudget(self, limits.get('max_storage_bytes', 512*1024*1024)).check(len(dumps(content).encode())*2)
        value=self.put('message',{'id':key,'agent':agent,'content':content,'kind':kind,'chat_id':chat_id,
                                 'status':'persisted','steering':steering,'created_at':time.time()},db)
        if after_insert is not None:
            after_insert(self, owner, value, db)
        self.event(agent,'message.persisted',{'message_id':key,'kind':kind},db)
        return value

    @staticmethod
    def _inbox_policy(owner, kind, steering):
        if kind not in ('message', 'chat', 'steer'):
            raise ValueError('invalid inbox kind')
        if kind != 'steer' and steering is not None:
            raise ValueError('steering metadata requires kind=steer')
        if owner.get('domain') == 'execution':
            if kind != 'message':
                raise ValueError('invalid inbox kind for ordinary execution')
            return None, None
        from ..extensions import ExtensionRequired, legacy_export
        try:
            return legacy_export("inbox_policy")
        except ExtensionRequired:
            if kind != 'message':
                raise
            return None, None

    def require_epoch(self, agent, epoch, db):
        a=self.get('agent',agent,db)
        if not a or a.get('epoch')!=epoch:
            raise StateConflict('stale execution epoch')
        return a


# Storage schema is unchanged; old control databases are not rewritten.
ResearchStore = ControlStore
