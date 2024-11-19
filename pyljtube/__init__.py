from .dataset import create_youtube_dataset
from .playlist import get_playlist_urls
from .downloader import YouTubeDownloader
import json

__version__ = "0.1.0"


def from_url_json(json_path: str):
    """
    JSONファイルからURLを読み込み、データセットを構築
    """
    with open(json_path, 'r') as f:
        urls = json.load(f)
        for url in urls:
            create_youtube_dataset(url)
