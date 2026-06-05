# mp3_text.py
import os
import glob

# ============================================
# ⚙️ 設定パラメータ（固定入力フォルダと出力フォルダ）
# ============================================
# 1. 読み込み対象の音声が溜まる固定フォルダ（youtube_mp3.pyの出力先）
INPUT_DIR = "./input_audio"

# 2. 文字起こしテキストを保存する特定の固定フォルダ
OUTPUT_DIR = "./output_text"

# 3. Whisperのモデルサイズ設定 ('tiny', 'base', 'small', 'medium', 'large-v3')
# 日本語の精度と速度のバランスが良い 'small' または 'medium' がローカルではおすすめです
WHISPER_MODEL_SIZE = "small"
# ============================================


def transcribe_local(mp3_path):
    """faster-whisperを使ってローカルで文字起こしを実行する"""
    from faster_whisper import WhisperModel
    
    print(f"  🧠 Whisperモデル({WHISPER_MODEL_SIZE})をロード中...")
    # CPU / GPU(MPS) の自動判定。Apple Silicon環境なら安定して動作します
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    
    print(f"  🎙️ 音声解析中...: {os.path.basename(mp3_path)}")
    # language="ja" で日本語を指定して精度を安定させます
    #segments, info = model.transcribe(mp3_path, beam_size=5, language="ja")
    #segments, info = model.transcribe(mp3_path, beam_size=5, language="en")
    segments, info = model.transcribe(mp3_path, beam_size=5)

    full_text = ""
    for segment in segments:
        # タイムスタンプ付きで結合していく場合（必要に応じて形式を変更してください）
        # full_text += f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}\n"
        full_text += f"{segment.text}\n"
        
    return full_text


def transcribe_api(mp3_path):
    """【予備】OpenAI APIを使ってクラウドで高速に文字起こしする場合"""
    # API方式に切り替える場合は、この関数のコメントアウトを解除して使用してください
    # from openai import OpenAI
    # client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    # with open(mp3_path, "rb") as audio_file:
    #     transcript = client.audio.transcriptions.create(
    #         model="whisper-1", 
    #         file=audio_file,
    #         language="ja"
    #     )
    # return transcript.text
    pass


def main():
    print("=" * 60)
    print("🎙️ MP3 Audio Transcriber (Whisper Part)")
    print("=" * 60)
    
    # 出力先フォルダの作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # input_audioフォルダ内のすべての.mp3ファイルを取得
    mp3_files = glob.glob(os.path.join(INPUT_DIR, "*.mp3"))
    
    if not mp3_files:
        print(f"❌ '{INPUT_DIR}' フォルダの中に .mp3 ファイルが見つかりませんでした。")
        print("先に youtube_mp3.py を実行して音声を準備してください。")
        return
        
    print(f"📋 検出されたファイル数: {len(mp3_files)}件")
    for i, file in enumerate(mp3_files, 1):
        print(f"  {i}. {os.path.basename(file)}")
    print()

    for file_path in mp3_files:
        filename = os.path.basename(file_path)
        base_name, _ = os.path.splitext(filename)
        
        # 出力ファイル名（例: input_audio/RIshv2_VCws.mp3 -> output_text/RIshv2_VCws.txt）
        output_txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
        
        # すでに文字起こし済みの場合はスキップする（無駄な計算を防ぐ安全弁）
        if os.path.exists(output_txt_path):
            print(f"⏩ スキップ: すでにテキスト化されています -> {output_txt_path}")
            continue
            
        print(f"[Process] 文字起こしを開始します: {filename}")
        
        try:
            # ローカルのWhisperを実行
            text_result = transcribe_local(file_path)
            
            # 結果を保存
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(text_result)
                
            print(f"  ✅ 文字起こし完了 -> {output_txt_path}\n")
            
        except Exception as e:
            print(f"  ❌ {filename} の処理中にエラーが発生しました。")
            print(f"  エラー詳細: {e}\n")

    print("=" * 60)
    print(f"📁 すべての文字起こしが終了しました。出力先: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()