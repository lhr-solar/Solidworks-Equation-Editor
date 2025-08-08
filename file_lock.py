import os
import sys
from pathlib import Path


def is_bundled():
    """Check if the application is running in a bundled environment"""
    return hasattr(sys, '_MEIPASS')


class FileHandleLock:
    def __init__(self, path: Path):
        self.path = path
        self.file = None
        self.locked = False
        self.readonly = False
        self._lock_len = 0

    def acquire(self):
        try:
            # Try to open with read-write access
            self.file = open(self.path, 'r+', encoding='utf-8')
        except Exception:
            try:
                # Fall back to read-only
                self.file = open(self.path, 'r', encoding='utf-8')
                self.readonly = True
            except Exception:
                self.file = None
                return False
        
        # In bundled environments, file locking might not work as expected
        # So we'll be more lenient with locking failures
        try:
            if os.name == 'nt':
                import msvcrt
                self.file.seek(0, os.SEEK_END)
                size = self.file.tell()
                self.file.seek(0)
                self._lock_len = max(1, size if size > 0 else 1)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, self._lock_len)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.locked = True
            self.readonly = False
            return True
        except Exception:
            # In bundled environments, we'll allow the file to be opened
            # even if locking fails, but mark it as potentially read-only
            self.locked = False
            if is_bundled():
                # In bundled mode, assume we can write even without lock
                self.readonly = False
            else:
                self.readonly = True
            return True

    def release(self):
        if self.file is None:
            return
        try:
            if self.locked:
                if os.name == 'nt':
                    import msvcrt
                    if self._lock_len <= 0:
                        self.file.seek(0, os.SEEK_END)
                        size = self.file.tell()
                        self.file.seek(0)
                        self._lock_len = max(1, size if size > 0 else 1)
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, self._lock_len)
                else:
                    import fcntl
                    fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass  # Ignore unlock errors
        finally:
            try:
                self.file.close()
            except Exception:
                pass
            self.file = None
            self.locked = False
            self._lock_len = 0

    def read_all(self) -> str:
        if not self.file:
            return ''
        try:
            self.file.seek(0)
            return self.file.read()
        except Exception:
            return ''

    def write_all(self, text: str):
        if not self.file or self.readonly:
            raise IOError("File is read-only or not open.")
        
        try:
            # Method 1: Try truncate approach
            self.file.seek(0)
            self.file.truncate(0)
            self.file.write(text)
            self.file.flush()
        except Exception as e:
            # Method 2: If truncate fails, close and reopen
            try:
                self.file.close()
                # Reopen the file for writing
                self.file = open(self.path, 'w', encoding='utf-8')
                self.file.write(text)
                self.file.flush()
            except Exception as e2:
                # Method 3: Final fallback - write without file handle
                self._write_fallback(text)
        
        # Ensure data is written to disk
        try:
            os.fsync(self.file.fileno())
        except Exception:
            pass

    def _write_fallback(self, text: str):
        """Fallback write method that bypasses file locking entirely"""
        try:
            # Write directly to the file path
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            raise IOError(f"All write methods failed: {e}")
