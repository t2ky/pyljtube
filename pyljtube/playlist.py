import requests
import re
from typing import List

def get_playlist_urls(playlist_url: str) -> List[str]:
    """
    YouTubeの再生リストから動画URLを取得（改良版）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(playlist_url, headers=headers)
    
    # 動画URLを直接抽出
    video_urls = []
    pattern = r'watch\?v=([a-zA-Z0-9_-]+)'
    matches = re.finditer(pattern, response.text)
    
    seen_ids = set()
    for match in matches:
        video_id = match.group(1)
        if video_id not in seen_ids:
            video_urls.append(f'https://www.youtube.com/watch?v={video_id}')
            seen_ids.add(video_id)
    
    return video_urls

# 使用例
if __name__ == '__main__':
    playlist_url = 'https://www.youtube.com/playlist?list=プレイリストID'
    urls = get_playlist_urls(playlist_url)
    for url in urls:
        print(url)
    