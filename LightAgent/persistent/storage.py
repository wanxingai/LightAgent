"""Shared-root storage admission and cooperative execution monitoring.

Managed file allocations use a separate process-shared filesystem lock, never
the control database writer slot. Snapshot batches account for each file in
memory and scan the existing tree only at the batch boundaries.
An arbitrary host/CLI process can write between polls: this is not an OS disk
quota. Such overruns cancel execution and may never be published as successes.
"""
from contextlib import contextmanager
import fcntl
from pathlib import Path
import os
import stat
import threading

from .store import uid


class StorageBudgetExceeded(RuntimeError):
    pass


class StorageBudget:
    # Keep space for terminal state, receipts and SQLite bookkeeping. This is
    # not charged as artifact capacity and cannot guarantee recovery on ENOSPC.
    CONTROL_HEADROOM = 64 * 1024

    def __init__(self, store, limit):
        self.store, self.limit = store, limit
        self._local = threading.local()

    def used(self):
        total = 0
        for path in self.store.root.rglob('*'):
            try:
                if path.is_file() and not path.is_symlink():
                    total += path.stat().st_size
            except FileNotFoundError:
                continue
        return total

    def check(self, allocation=0):
        if self.used()+allocation+self.CONTROL_HEADROOM > self.limit:
            raise StorageBudgetExceeded('persistent storage budget reached; archive data before resuming')

    @contextmanager
    def _allocation_lock(self):
        # Do not enter a control-store transaction while holding this lock.
        # Kernel ownership releases it automatically when a writer crashes.
        fd = os.open(self.store.root/'.storage.lock',
                     os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('storage lock must be a regular file')
            os.fchmod(fd, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    @contextmanager
    def batch(self):
        """Bound a snapshot without a whole-tree scan and DB lock per file.

        Other managed allocations wait on the filesystem lock; control-plane
        reads, heartbeats and inbox writes remain independent. Unmanaged backend
        writes still require cooperative monitoring and a final capacity check.
        """
        if getattr(self._local, 'remaining', None) is not None:
            raise RuntimeError('storage batches cannot be nested')
        with self._allocation_lock():
            remaining = self.limit-self.CONTROL_HEADROOM-self.used()
            if remaining < 0:
                raise StorageBudgetExceeded('persistent storage budget reached; archive data before resuming')
            self._local.remaining = remaining
            try:
                yield
                self.check()
            finally:
                del self._local.remaining

    @contextmanager
    def allocate(self, byte_count):
        if type(byte_count) is not int or byte_count < 0:
            raise ValueError('allocation must be a nonnegative byte count')
        remaining = getattr(self._local, 'remaining', None)
        if remaining is not None:
            if byte_count > remaining:
                raise StorageBudgetExceeded('persistent storage budget reached; archive data before resuming')
            self._local.remaining -= byte_count
            yield
            return
        with self._allocation_lock():
            self.check(byte_count)
            yield
            self.check()

    def write_bytes(self, path, data, *, mode=0o600):
        path = Path(path)
        if not path.parent.resolve().is_relative_to(self.store.root):
            raise ValueError('managed storage write leaves service root')
        # The quota lock reserves this allocation until it has become actual
        # disk usage, so independent workers/processes cannot spend it twice.
        with self.allocate(len(data)):
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.parent/('.allocation-'+uid())
            try:
                with temp.open('xb') as stream:
                    stream.write(data)
                temp.chmod(mode)
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)

    @contextmanager
    def watch(self, token):
        self.check()
        done = threading.Event()
        exceeded = threading.Event()
        def monitor():
            while not done.wait(.05):
                try:
                    self.check()
                except (StorageBudgetExceeded, OSError):
                    exceeded.set()
                    token.cancel('storage budget exceeded')
                    return
        thread = threading.Thread(target=monitor, name='lightagent-storage', daemon=True)
        thread.start()
        try:
            yield
        finally:
            done.set()
            thread.join()
            if exceeded.is_set():
                raise StorageBudgetExceeded('persistent storage budget exceeded during execution')
            self.check()
