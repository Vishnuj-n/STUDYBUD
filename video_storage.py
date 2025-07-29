import sqlite3
import json
from typing import List, Dict

class VideoStorage:
    def __init__(self, db_path="file_hashes.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

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
                    url TEXT UNIQUE NOT NULL,
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
                    FOREIGN KEY (file_hash) REFERENCES files (hash),
                    FOREIGN KEY (video_id) REFERENCES videos (id)
                )
            """)

    def store_videos_for_file(self, file_hash: str, video_results: Dict[str, List[Dict[str, str]]], filename: str = None):
        with self.conn:
            # 1. Add the file to the 'files' table
            self.conn.execute(
                "INSERT OR IGNORE INTO files (hash, filename) VALUES (?, ?)",
                (file_hash, filename)
            )

            for concept, videos in video_results.items():
                for video in videos:
                    # 2. Add the video to the 'videos' table, ignoring if it already exists
                    cursor = self.conn.execute(
                        "INSERT OR IGNORE INTO videos (url, title, concept) VALUES (?, ?, ?)",
                        (video['url'], video['title'], concept)
                    )
                    
                    # 3. Get the ID of the video (whether it was just inserted or already existed)
                    if cursor.lastrowid:
                        video_id = cursor.lastrowid
                    else:
                        video_id = self.conn.execute(
                            "SELECT id FROM videos WHERE url = ?", (video['url'],)
                        ).fetchone()[0]

                    # 4. Create the link in the 'file_video_links' table
                    self.conn.execute(
                        "INSERT OR IGNORE INTO file_video_links (file_hash, video_id) VALUES (?, ?)",
                        (file_hash, video_id)
                    )

    def get_videos_for_file(self, file_hash: str) -> Dict[str, List[Dict[str, str]]]:
        query = """
            SELECT v.concept, v.title, v.url
            FROM videos v
            JOIN file_video_links fvl ON v.id = fvl.video_id
            WHERE fvl.file_hash = ?
        """
        cursor = self.conn.execute(query, (file_hash,))
        
        # Group results by concept
        video_results = {}
        for concept, title, url in cursor.fetchall():
            if concept not in video_results:
                video_results[concept] = []
            video_results[concept].append({'title': title, 'url': url})
            
        return video_results

    def close(self):
        if self.conn:
            self.conn.close()
