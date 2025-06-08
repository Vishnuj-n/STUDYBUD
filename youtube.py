import yt_dlp
from typing import List, Dict

class YouTubeSearcher:
    """Simple YouTube video searcher using yt-dlp."""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
    
    def search(self, query: str, count: int = 2) -> List[Dict]:
        """Search for videos with specified query and result count."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{count}:{query}", download=False)
                
                videos = []
                if 'entries' in info and info['entries']:
                    for entry in info['entries']:
                        if entry:
                            videos.append({
                                'title': entry.get('title', 'Unknown'),
                                'url': entry.get('webpage_url', entry.get('url', ''))
                            })
                return videos
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_multiple(self, queries: List[str], count: int = 2) -> Dict:
        """Search multiple queries and return results."""
        results = {}
        for query in queries:
            results[query] = self.search(query, count)
        return results
        
    def print_results(self, results: Dict) -> None:
        """Print search results in a readable format."""
        for query, videos in results.items():
            print(f"\nResults for '{query}':")
            for i, video in enumerate(videos, 1):
                print(f"  {i}. {video['title']}")
                print(f"     {video['url']}")


def main():
    """Demo the simplified YouTubeSearcher."""
    queries = ["Python programming", "Machine Learning"]
    searcher = YouTubeSearcher()
    
    # Search single query
    python_videos = searcher.search("Python tutorial")
    print("=== PYTHON TUTORIALS ===")
    for i, video in enumerate(python_videos, 1):
        print(f"{i}. {video['title']}")
        print(f"   {video['url']}")
    
    # Search multiple queries
    results = searcher.search_multiple(queries)
    print("\n=== MULTIPLE SEARCHES ===")
    searcher.print_results(results)


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Install yt-dlp: pip install yt-dlp")