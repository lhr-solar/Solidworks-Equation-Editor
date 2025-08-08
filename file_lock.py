import os
from pathlib import Path


class FileHandleLock:
    def __init__(self, path: Path):
        self.path = path
        self.file = None
        self.locked = False
        self.readonly = False
        self._lock_len = 0

    def acquire(self):
        try:
            self.file = open(self.path, 'r+', encoding='utf-8')
        except Exception:
            try:
                self.file = open(self.path, 'r', encoding='utf-8')
                self.readonly = True
            except Exception:
                self.file = None
                return False
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
            self.locked = False
            self.readonly = True
            return False

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
        self.file.seek(0)
        return self.file.read()

    def write_all(self, text: str):
        if not self.file or self.readonly:
            raise IOError("File is read-only or not open.")
        self.file.seek(0)
        self.file.truncate(0)
        self.file.write(text)
        self.file.flush()
        try:
            os.fsync(self.file.fileno())
        except Exception:
            pass
