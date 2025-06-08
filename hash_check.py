import hashlib
import sqlite3

class PDFDuplicateChecker:
    def __init__(self, db_path: str = "file_hashes.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS file_hashes (hash TEXT PRIMARY KEY)"
            )

    def compute_hash(self, file_bytes: bytes) -> str:
        """Compute SHA-256 hash of the given file content."""
        return hashlib.sha256(file_bytes).hexdigest()

    def is_duplicate(self, file_bytes: bytes) -> bool:
        """Check if the file hash exists in the database."""
        file_hash = self.compute_hash(file_bytes)
        cursor = self.conn.execute(
            "SELECT 1 FROM file_hashes WHERE hash = ?", (file_hash,)
        )
        return cursor.fetchone() is not None

    def mark_uploaded(self, file_bytes: bytes) -> None:
        """Insert the new file hash into the database."""
        file_hash = self.compute_hash(file_bytes)
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO file_hashes (hash) VALUES (?)", (file_hash,)
            )

    def check_and_mark(self, file_bytes: bytes) -> bool:
        """
        Returns True if the file is a duplicate.
        Otherwise, stores it in the database and returns False.
        """
        if self.is_duplicate(file_bytes):
            return True
        else:
            self.mark_uploaded(file_bytes)
            return False

    def close(self):
        """Close the database connection."""
        self.conn.close()
