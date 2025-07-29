import sqlite3
from typing import List, Dict

class VideoStorage:
    def __init__(self, db_path="file_hashes.db"):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """Enable the use of 'with VideoStorage() as vs:' syntax."""
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the connection is closed."""
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        with self.conn:
            # Table for storing file information
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    hash TEXT PRIMARY KEY,
                    filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for storing unique video information
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    concept TEXT
                )
            """)
            # Linking table for the many-to-many relationship
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS file_video_links (
                    file_hash TEXT,
                    video_id INTEGER,
                    PRIMARY KEY (file_hash, video_id),
                    FOREIGN KEY (file_hash) REFERENCES files (hash) ON DELETE CASCADE,
                    FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
                )
            """)
            # Add indexes to speed up queries
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_url ON videos (url)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_file_video_links_file_hash ON file_video_links (file_hash)")

    def _add_file(self, file_hash: str, filename: str = None):
        """Adds a file record to the database, ignoring if it already exists."""
        self.conn.execute(
            "INSERT OR IGNORE INTO files (hash, filename) VALUES (?, ?)",
            (file_hash, filename)
        )

    def _get_or_create_video(self, concept: str, video: Dict[str, str]) -> int:
        """
        Finds a video by URL or creates it if it doesn't exist.
        Returns the video's ID.
        """
        cursor = self.conn.execute("SELECT id FROM videos WHERE url = ?", (video['url'],))
        result = cursor.fetchone()
        
        if result:
            return result[0]  # Video already exists, return its ID
        else:
            # Video doesn't exist, insert it and return the new ID
            cursor = self.conn.execute(
                "INSERT INTO videos (url, title, concept) VALUES (?, ?, ?)",
                (video['url'], video['title'], concept)
            )
            return cursor.lastrowid

    def _link_file_to_video(self, file_hash: str, video_id: int):
        """Creates a link between a file and a video."""
        self.conn.execute(
            "INSERT OR IGNORE INTO file_video_links (file_hash, video_id) VALUES (?, ?)",
            (file_hash, video_id)
        )

    def store_videos_for_file(self, file_hash: str, video_results: Dict[str, List[Dict[str, str]]], filename: str = None):
        """
        Stores all videos and their links for a given file within a single transaction.
        """
        with self.conn:
            self._add_file(file_hash, filename)
            for concept, videos in video_results.items():
                for video in videos:
                    video_id = self._get_or_create_video(concept, video)
                    self._link_file_to_video(file_hash, video_id)

    def get_videos_for_file(self, file_hash: str) -> Dict[str, List[Dict[str, str]]]:
        """Retrieves all videos for a given file, grouped by concept."""
        query = """
            SELECT v.concept, v.title, v.url
            FROM videos v
            JOIN file_video_links fvl ON v.id = fvl.video_id
            WHERE fvl.file_hash = ?
        """
        cursor = self.conn.execute(query, (file_hash,))
        
        video_results = {}
        for concept, title, url in cursor.fetchall():
            if concept not in video_results:
                video_results[concept] = []
            video_results[concept].append({'title': title, 'url': url})
            
        return video_results
