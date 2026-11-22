"""Keep concurrent factory runs from replacing the same episode's temporary files."""
from contextlib import contextmanager
import os

@contextmanager
def episode_lock(folder):
    folder.mkdir(parents=True,exist_ok=True)
    work=folder/"work"
    work.mkdir(exist_ok=True)
    with (work/"episode.lock").open("a+b") as lock:
        if not lock.seek(0,2):
            lock.write(b"1");lock.flush()
        lock.seek(0)
        try:
            if os.name=="nt":
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as e:raise RuntimeError(f"{folder.name} already has an active render") from e
        try:yield
        finally:
            lock.seek(0)
            if os.name=="nt":msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock,fcntl.LOCK_UN)
