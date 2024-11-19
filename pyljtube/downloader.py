import yt_dlp
import os
from typing import Dict, Optional, Tuple

class YouTubeDownloader:
    def __init__(self, output_path: str = 'downloads'):
        """
        YouTubeダウンローダーの初期化
        Args:
            output_path (str): ダウンロードしたファイルの保存先
        """
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True)

    def download_video(
        self,
        url: str,
        format_type: str = 'video',
        download_subs: bool = True
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """
        YouTubeから動画をダウンロード
        
        Args:
            url (str): YouTubeのURL
            format_type (str): 'video' または 'audio'
            download_subs (bool): 字幕をダウンロードするかどうか
            
        Returns:
            Tuple[Optional[str], Optional[Dict]]: (ファイルパス, 動画情報)
        """
        try:
            # 基本オプションの設定
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' 
                         if format_type == 'video' else 'bestaudio[ext=m4a]/best',
                'outtmpl': os.path.join(
                    self.output_path, 
                    '%(title)s_%(upload_date)s.%(ext)s'
                ),
                'writethumbnail': True,
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'postprocessors': []
            }

            # 字幕のダウンロード設定
            if download_subs:
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en', 'ja'],  # 英語と日本語の字幕
                    'postprocessors': [{
                        'key': 'FFmpegSubtitlesConvertor',
                        'format': 'srt',
                    }]
                })

            # 音声のみの場合の設定
            if format_type == 'audio':
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                })

            # ダウンロードと情報取得
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info is None:
                    return None, None
                    
                # ダウンロードされたファイルのパスを取得
                filename = ydl.prepare_filename(info)
                if format_type == 'audio':
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                return filename, info

        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return None, None

    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        動画の情報のみを取得
        
        Args:
            url (str): YouTubeのURL
            
        Returns:
            Optional[Dict]: 動画の情報
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
                
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            return None

    @staticmethod
    def _progress_hook(d: Dict):
        """ダウンロード進捗のコールバック関数"""
        if d['status'] == 'downloading':
            percentage = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            print(f"\rダウンロード進捗: {percentage} 速度: {speed}", end='')
        elif d['status'] == 'finished':
            print("\nダウンロード完了！処理中...")
