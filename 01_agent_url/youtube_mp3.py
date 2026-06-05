# youtube_mp3.py
import os
import re
import subprocess

# ============================================
# ⚙️ 設定パラメータ（入力URLと固定出力フォルダ）
# ============================================
# 1. ダウンロードしたいYouTubeのURLリスト（改行区切りで複数指定可能）
TARGET_URLS = """
https://www.youtube.com/watch?v=RIshv2_VCws
"""

# 2. 音声ファイルを保存する特定の固定フォルダ名
OUTPUT_DIR = "./input_audio"
# ============================================


def extract_video_id(url):
    """
    様々な形式のYouTube URLから頑健にvideo_idを抽出する
    例: watch?v=ID, youtu.be/ID, embed/ID, クエリパラメータ付きなど
    """
    url = url.strip()
    if not url:
        return None
        
    # 一般的なYouTubeのvideo_id（11文字）を抽出する正規表現パターン
    pattern = r'(?:v=|\/embed\/|\/1\/|\/v\/|https:\/\/youtu\.be\/|\/shorts\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    # 最終手段として、'v=' で分割する元のロジックをフォールバックとして残す
    if 'v=' in url:
        return url.split('v=')[-1].split('&')[0]
        
    return None


def main():
    print("=" * 60)
    print("🎬 YouTube MP3 Downloader (Local Tool)")
    print("=" * 60)
    
    # 出力先固定フォルダの作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # テキストブロックを1行ずつのリストに分解・不純物の除去
    lines = [line.strip() for line in TARGET_URLS.strip().splitlines() if line.strip()]
    
    video_ids = []
    for line in lines:
        video_id = extract_video_id(line)
        if video_id:
            video_ids.append(video_id)
            
    if not video_ids:
        print("❌ 有効なYouTubeのURLまたはVideo IDが見つかりませんでした。")
        return
        
    print(f"📋 処理対象のVideo ID: {video_ids}\n")

    for video_id in video_ids:
        url = f'https://www.youtube.com/watch?v={video_id}'
        # 拡張子 (.mp3) は yt-dlp 側が自動で付与するため、テンプレートには含めない
        output_template = os.path.join(OUTPUT_DIR, f"{video_id}.%(ext)s")
        
        print(f"[Download] 処理中: {url}")
        
        # ローカル環境の標準コマンドとして安全に実行できるように subprocess.run を使用
        # 引数をリスト形式で渡すことで、URLに特殊文字（&や?など）が含まれていてもシェルで誤作動しません
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", output_template,
            url
        ]
        
        try:
            # コマンドの実行。check=Trueでエラー発生時に例外を投げさせる
            subprocess.run(cmd, check=True)
            expected_mp3 = os.path.join(OUTPUT_DIR, f"{video_id}.mp3")
            print(f"  ✅ 作成完了: {expected_mp3}\n")
            
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {video_id} のダウンロードまたはMP3変換に失敗しました。")
            print(f"  エラー詳細: {e}\n")
        except FileNotFoundError:
            print("  ❌ ターミナルから 'yt-dlp' コマンドを認識できませんでした。")
            print("  'pip install yt-dlp' がローカル環境で完了しているか確認してください。\n")
            break

    print("=" * 60)
    print(f"📁 すべての処理が終了しました。出力先: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()