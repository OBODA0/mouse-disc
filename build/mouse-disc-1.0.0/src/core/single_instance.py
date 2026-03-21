"""Single instance lock for Mouse Disc"""
import fcntl
from pathlib import Path


class SingleInstanceLock:
    """Ensure only one instance of the menu is running"""
    def __init__(self, lock_path: str = "/tmp/mouse-disc.lock"):
        self.lock_path = Path(lock_path)
        self.lock_file = None

    def acquire(self) -> bool:
        """Try to acquire lock. Returns True if successful, False if already locked."""
        self.lock_file = open(self.lock_path, 'w')
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            self.lock_file.close()
            self.lock_file = None
            return False

    def release(self):
        """Release the lock"""
        if self.lock_file:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None
        if self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except:
                pass
