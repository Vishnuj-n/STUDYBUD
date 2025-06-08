import sqlite3
import json

class VideoStorage:
    def __init__(self, db_path="file_hashes.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS video_links (hash TEXT PRIMARY KEY, videos TEXT)"
            )

    def store_links(self, file_hash: str, video_urls: list[str]):
        video_json = json.dumps(video_urls)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO video_links (hash, videos) VALUES (?, ?)",
                (file_hash, video_json)
            )

    def get_links(self, file_hash: str) -> list[str]:
        cursor = self.conn.execute(
            "SELECT videos FROM video_links WHERE hash = ?", (file_hash,)
        )
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []

    def close(self):
        self.conn.close()
