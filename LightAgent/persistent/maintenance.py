"""Generic bounded service logging; research retention lives in LightResearch."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import select
import stat
import sys
import threading

class _RotatingWriter:
    def __init__(self, root, max_bytes, backups):
        self.path = Path(root)/'runner.log'
        self.max_bytes, self.backups = max_bytes, backups
        self.stream = self._open()

    def _open(self):
        fd = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise ValueError('runner log must be a regular file')
        os.fchmod(fd, 0o600)
        size = os.fstat(fd).st_size
        if size > self.max_bytes:
            tail = os.pread(fd, self.max_bytes, size-self.max_bytes)
            os.ftruncate(fd, 0)
            os.write(fd, tail)
        return os.fdopen(fd, 'ab', buffering=0)

    def _rotate(self):
        self.stream.close()
        for number in range(self.backups, 0, -1):
            source = self.path if number == 1 else Path(str(self.path)+'.'+str(number-1))
            target = Path(str(self.path)+'.'+str(number))
            if source.exists() or source.is_symlink():
                os.replace(source, target)
        self.stream = self._open()

    def write(self, data):
        while data:
            size = os.fstat(self.stream.fileno()).st_size
            if size >= self.max_bytes:
                self._rotate()
                size = 0
            portion = data[:self.max_bytes-size]
            self.stream.write(portion)
            data = data[len(portion):]

    def close(self):
        self.stream.close()


@contextmanager
def runtime_logging(root, *, max_bytes=1024*1024, backups=3):
    """Capture runner FD 1/2 through a bounded rotating writer owned by runner.

    Use only at process startup, before workers are launched. The reader stays
    alive with the detached runner, independent of the initiating SDK process.
    This captures Python and native writes to stdout/stderr and inherited FDs.
    """
    if type(max_bytes) is not int or max_bytes < 16 or type(backups) is not int or not 1 <= backups <= 20:
        raise ValueError('invalid runner log retention')
    root = Path(root).resolve(strict=True)
    lockfd = os.open(root/'runner-log.lock', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    writer = None
    saved = []
    readfd = writefd = None
    thread = None
    done = threading.Event()
    errors = []
    try:
        fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        writer = _RotatingWriter(root, max_bytes, backups)
        sys.stdout.flush(); sys.stderr.flush()
        saved = [os.dup(1), os.dup(2)]
        readfd, writefd = os.pipe()

        def drain():
            try:
                while True:
                    ready, _, _ = select.select([readfd], [], [], .1)
                    if ready:
                        data = os.read(readfd, 65536)
                        if not data:
                            break
                        writer.write(data)
                    elif done.is_set():
                        break
            except OSError as exc:
                # Continue draining if storage is full; never deadlock workers
                # behind a full pipe while they try to report that same failure.
                errors.append(exc)
                while not done.is_set():
                    if select.select([readfd], [], [], .1)[0] and not os.read(readfd, 65536):
                        break
        thread = threading.Thread(target=drain, name='lightagent-runner-log', daemon=True)
        thread.start()
        os.dup2(writefd, 1); os.dup2(writefd, 2)
        os.close(writefd); writefd = None
        yield
    finally:
        if saved:
            sys.stdout.flush(); sys.stderr.flush()
            os.dup2(saved[0], 1); os.dup2(saved[1], 2)
            for fd in saved:
                os.close(fd)
        done.set()
        if thread:
            thread.join(timeout=5)
        if readfd is not None:
            os.close(readfd)
        if writefd is not None:
            os.close(writefd)
        if writer:
            writer.close()
        os.close(lockfd)
        if errors:
            raise RuntimeError('runner log storage failed') from errors[0]
