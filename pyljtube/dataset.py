import os
import csv
from typing import Dict, List
from moviepy.editor import VideoFileClip
import pysrt
import pandas as pd
import re
from tqdm import tqdm
import numpy as np
from downloader import YouTubeDownloader

class YouTubeDatasetCreator(YouTubeDownloader):
    def __init__(self, output_path: str = 'dataset'):
        super().__init__(output_path)
        self.transcript_dir = os.path.join(output_path, 'transcript')
        self.video_dir = os.path.join(output_path, 'videos')
        self.wavs_dir = os.path.join(output_path, 'wavs')
        os.makedirs(self.transcript_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.wavs_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """字幕テキストのクリーニング"""
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?\'";:\[\]()&-]', '', text)
        return text.strip()

    def is_valid_segment(self, text: str, duration: float) -> bool:
        """セグメントが有効かチェック"""
        if len(text) < 10 or len(text) > 200:
            return False
        if duration < 1.0 or duration > 10.0:
            return False
        return True

    def extract_audio(self, video_clip, output_path: str) -> None:
        """動画からオーディオを抽出してWAVとして保存"""
        temp_audio = video_clip.audio
        temp_audio.write_audiofile(
            output_path,
            fps=22050,  # LJSpeech互換
            nbytes=2,   # 16-bit
            codec='pcm_s16le',
            ffmpeg_params=["-ac", "1"]  # モノラル
        )

    def create_dataset(
        self,
        video_path: str,
        subtitle_path: str,
        video_id: str
    ) -> List[Dict]:
        """動画を字幕に基づいて分割しデータセットを作成"""
        dataset_entries = []
        subs = pysrt.open(subtitle_path)
        video = VideoFileClip(video_path)
        
        print("字幕に基づいて動画を分割中...")
        for i, sub in tqdm(enumerate(subs)):
            text = self.clean_text(sub.text)
            start_time = sub.start.ordinal / 1000
            end_time = sub.end.ordinal / 1000
            duration = end_time - start_time
            
            if not self.is_valid_segment(text, duration):
                continue
            
            clip_id = f"{video_id}_{i:04d}"
            video_filename = f"{clip_id}.mp4"
            wav_filename = f"{clip_id}.wav"
            video_path = os.path.join(self.video_dir, video_filename)
            wav_path = os.path.join(self.wavs_dir, wav_filename)
            
            try:
                clip = video.subclip(start_time, end_time)
                # 動画の保存
                clip.write_videofile(
                    video_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None
                )
                # WAVの抽出と保存
                self.extract_audio(clip, wav_path)
                
                dataset_entries.append({
                    'id': clip_id,
                    'video_filename': video_filename,
                    'wav_filename': wav_filename,
                    'text': text,
                    'duration': round(duration, 3),
                    'start_time': round(start_time, 3),
                    'end_time': round(end_time, 3)
                })
            except Exception as e:
                print(f"クリップ {clip_id} の処理中にエラー: {str(e)}")
                continue
        
        video.close()
        return dataset_entries

def create_youtube_dataset(
    url: str,
    output_dir: str = 'dataset',
    min_clips: int = 10
) -> None:
    """YouTubeビデオからデータセットを作成"""
    creator = YouTubeDatasetCreator(output_dir)
    info = creator.get_video_info(url)
    if not info:
        print("動画情報の取得に失敗しました")
        return
    
    video_id = info['id']
    video_path, _ = creator.download_video(
        url,
        download_subs=True,
        format_type='video'
    )
    
    if not video_path:
        print("ダウンロードに失敗しました")
        return
    
    subtitle_path = f"{os.path.splitext(video_path)[0]}.en.srt"
    if not os.path.exists(subtitle_path):
        print("英語字幕が見つかりません")
        return
    
    dataset_entries = creator.create_dataset(
        video_path,
        subtitle_path,
        video_id
    )
    
    if len(dataset_entries) < min_clips:
        print(f"警告: 生成されたクリップが少なすぎます ({len(dataset_entries)} < {min_clips})")
        return
    
    metadata_path = os.path.join(output_dir, 'metadata.csv')
    df = pd.DataFrame(dataset_entries)
    
    if os.path.exists(metadata_path):
        existing_df = pd.read_csv(metadata_path)
        df = pd.concat([existing_df, df], ignore_index=True)
    
    df.to_csv(metadata_path, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
    
    print(f"\n=== データセット作成完了 ===")
    print(f"総クリップ数: {len(dataset_entries)}")
    print(f"総時間: {sum(entry['duration'] for entry in dataset_entries):.2f}秒")
    print(f"平均長: {np.mean([entry['duration'] for entry in dataset_entries]):.2f}秒")
