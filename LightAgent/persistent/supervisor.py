"""One supervisor lifetime for ordinary execution and optional domain extensions."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from pathlib import Path
import os
import sqlite3
import threading
import time
from .store import ControlStore, StateConflict, uid
from ..backends.sessions import BackendSessionStore


class ServiceSupervisor:
    runner_module = "LightAgent.persistent.runner"

    def __init__(self, root=None, *, backend_factories=None, max_concurrent_jobs=8):
        if type(max_concurrent_jobs) is not int or max_concurrent_jobs < 1:
            raise ValueError("max_concurrent_jobs must be a positive integer")
        self.store = ControlStore(root)
        self.root = self.store.root
        self.bindings = BackendSessionStore(self.root / "bindings")
        self.backend_factories = dict(backend_factories or {})
        self.max_concurrent_jobs = max_concurrent_jobs
        self._stop = threading.Event()
        self._active = {}
        self._instance = uid()

    def _can_start_detached(self):
        return not self.backend_factories

    @contextmanager
    def _supervisor_guard(self):
        with self.bindings.lock('supervisor', 'main'):
            self._supervisor_thread = threading.get_ident()
            try:
                yield
            finally:
                self._supervisor_thread = None

    def start(self, *, env=None, timeout=15):
        """Launch a detached foreground runner; OS service managers may run it directly."""
        import subprocess
        import sys
        if not self._can_start_detached():
            raise ValueError('custom host factories/policies require serve_forever in a host-owned process')
        with self.bindings.lock('startup', 'service'):
            if self.healthy():
                if self.store.get('service','main').get('max_concurrent_jobs',8)!=self.max_concurrent_jobs:
                    raise StateConflict('running supervisor has a different Job concurrency limit')
                return
            environment = dict(os.environ)
            environment.update(env or {})
            package_root = str(Path(__file__).resolve().parents[2])
            environment['PYTHONPATH'] = package_root + os.pathsep + environment.get('PYTHONPATH', '')
            log = self.root/'runner.log'
            with log.open('ab') as stream:
                process = subprocess.Popen([sys.executable, '-m', self.runner_module, '--root', str(self.root),
                                            '--max-concurrent-jobs',str(self.max_concurrent_jobs)],
                                           stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                                           start_new_session=True, env=environment, cwd=str(self.root))
            until = time.monotonic() + timeout
            while time.monotonic() < until:
                if self.healthy():
                    return
                if process.poll() is not None:
                    raise RuntimeError('runner failed to start; inspect the local runner.log')
                time.sleep(.05)
            raise TimeoutError('runner startup not confirmed; inspect heartbeat before retrying')


    def healthy(self):
        record = self.store.get('service', 'main')
        if not (record and record.get('status') == 'running' and time.time()-record['heartbeat_at'] < 10):
            return False
        from ..backends import BackendError
        try:
            with self.bindings.lock('supervisor','main'):
                return False
        except BackendError:
            return True


    def _heartbeat(self, status='running'):
        with self.store.transaction() as db:
            old = self.store.get('service', 'main', db)
            value = dict(id='main', instance=self._instance, heartbeat_at=time.time(), status=status,
                         max_concurrent_jobs=self.max_concurrent_jobs,
                         revision=old['revision'] if old else 0,
                         stop_requested=bool(old and old.get('instance') == self._instance and old.get('stop_requested')))
            self.store.put('service', value, db)


    def _heartbeat_if_available(self, status='running'):
        """A transient SQLite writer must not terminate the supervisor."""
        try:
            self._heartbeat(status)
            return True
        except sqlite3.OperationalError as exc:
            code = getattr(exc, 'sqlite_errorcode', None)
            busy = ((code is not None and code & 0xff in (getattr(sqlite3,'SQLITE_BUSY',5), getattr(sqlite3,'SQLITE_LOCKED',6)))
                    or (code is None and str(exc).lower() in ('database is locked', 'database table is locked')))
            if not busy:
                raise
            return False


    def request_shutdown(self):
        with self.store.transaction() as db:
            service = self.store.get('service','main',db)
            if service:
                service['stop_requested'] = True
                self.store.put('service',service,db)


    def stop(self):
        self._stop.set()


    def _service_resources(self):
        return nullcontext()

    def _pending_futures(self):
        return (future for future, _ in self._active.values())

    def _drain(self):
        # Shutdown stops claiming; only explicit user interruption cancels work.
        active = tuple(self._pending_futures())
        while any(not future.done() for future in active):
            self._heartbeat_if_available('stopping')
            for aid, (_, token) in self._active.items():
                if self.store.get('agent', aid)['desired'] in ('interrupted', 'cancelled'):
                    token.cancel('user interruption during service shutdown')
            time.sleep(.05)

    def serve_forever(self, *, poll_interval=.2, max_ticks=None):
        with self._supervisor_guard():
            self.recover()
            try:
                with ThreadPoolExecutor(max_workers=8, thread_name_prefix='lightagent-service') as pool, self._service_resources():
                    try:
                        ticks = 0
                        while not self._stop.is_set():
                            if not self._heartbeat_if_available():
                                self._stop.wait(max(poll_interval, .01))
                                continue
                            if self.store.get('service','main').get('stop_requested'):
                                break
                            self.tick(pool)
                            ticks += 1
                            if max_ticks is not None and ticks >= max_ticks:
                                break
                            self._stop.wait(poll_interval)
                    finally:
                        self._drain()
            finally:
                self._heartbeat_if_available('stopped')
