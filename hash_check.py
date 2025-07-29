import hashlib
import sqlite3


class PDFDuplicateChecker:
    def __init__(self, db_path: str = "file_hashes.db"):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """Enable the use of 'with' statement for safe connection handling."""
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the database connection is closed on exit."""
        if self.conn:
            self.conn.close()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS file_hashes (hash TEXT PRIMARY KEY, key_concepts TEXT)"
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
                "INSERT OR IGNORE INTO file_hashes (hash, key_concepts) VALUES (?, NULL)", (file_hash,)
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
            
    def store_key_concepts(self, file_bytes: bytes, key_concepts: list) -> None:
        """
        Store key concepts for a file in the database.
        """
        file_hash = self.compute_hash(file_bytes)
        # Convert list to string for storage
        key_concepts_str = ', '.join(key_concepts) if key_concepts else ''
        
        with self.conn:
            self.conn.execute(
                "UPDATE file_hashes SET key_concepts = ? WHERE hash = ?", 
                (key_concepts_str, file_hash)
            )
    
    def get_key_concepts(self, file_bytes: bytes) -> list:
        """
        Retrieve key concepts for a file from the database.
        Returns empty list if not found.
        """
        file_hash = self.compute_hash(file_bytes)
        cursor = self.conn.execute(
            "SELECT key_concepts FROM file_hashes WHERE hash = ?", (file_hash,)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0].split(', ')
        return []
    
    def check_and_store_key_concepts(self, file_bytes: bytes, key_concepts: list) -> tuple:
        """
        Check if the file is a duplicate and store key concepts if it's not.
        Returns (is_duplicate, existing_key_concepts)
        """
        file_hash = self.compute_hash(file_bytes)
        cursor = self.conn.execute(
            "SELECT key_concepts FROM file_hashes WHERE hash = ?", (file_hash,)
        )
        result = cursor.fetchone()
        
        if result:  # File exists in database
            existing_concepts = result[0].split(', ') if result[0] else []
            return (True, existing_concepts)
        else:
            # Not a duplicate, store file hash and key concepts
            key_concepts_str = ', '.join(key_concepts) if key_concepts else ''
            with self.conn:
                self.conn.execute(
                    "INSERT INTO file_hashes (hash, key_concepts) VALUES (?, ?)",
                    (file_hash, key_concepts_str)
                )
            return (False, [])

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def close(self):
        """Close the database connection."""
        self.conn.close()
