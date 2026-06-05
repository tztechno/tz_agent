# code_generator.py
import ollama
import os
import json
import re
from datetime import datetime
from pathlib import Path

class CompetitiveCodeGenerator:
    """スクレイピングされた競プロ問題テキストから、Pythonの解答コードを自動生成するクラス"""
    
    def __init__(self, model='qwen2.5-coder:7b'):
        self.model = model
    
    def generate_code_from_file(self, file_path, custom_prompt=None):
        """問題テキストファイルを読み込んで解答コードを生成"""
        print(f"[Analyzing Problem] {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"  ❌ File not found: {file_path}")
            return None
        
        # スクレイピングされた問題文の読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            problem_statement = f.read()
        
        # デフォルトプロンプト（競プロ解答専用に最適化）
        if custom_prompt is None:
            prompt = f"""あなたは競技プログラミングのマスターです。
提供された以下の問題文、制約、入力・出力形式、サンプルケースを完璧に理解し、すべてのテストケースをパスするPython 3のコードを作成してください。

【問題文データ】
{problem_statement}

【出力に関する絶対制約】
1. 回答は「Pythonコードのみ」を出力してください。
2. コードの前に「解説」や「挨拶」などの自然言語を一切含めないでください。
3. コードブロック（ ```python ... ``` ）の形式でコードを囲んで出力してください。
4. 標準入力（input / sys.stdin.read）からデータを受け取り、標準出力（print）に結果を出力する、単一ファイルで動作するスクリプトにしてください。
5. 問題の制約（最大値など）を考慮し、制限時間内（実行時間制限）に間に合う効率的なアルゴリズム（必要に応じて計算量 O(N) や O(N log N) など）を選択してください。
"""
        else:
            prompt = f"{custom_prompt}\n\n【問題文データ】\n{problem_statement}"
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"  ❌ Model error: {e}")
            return None
    
    def process_folder(self, folder_path, custom_prompt=None):
        """フォルダ内の全問題テキストからコードを生成"""
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            return None
        
        text_files = [f for f in folder.iterdir() if f.suffix.lower() == '.txt']
        
        if not text_files:
            print(f"\n⚠️  No problem text files found in {folder_path}")
            return None
        
        print(f"\n💻 Generating codes for {len(text_files)} problem(s)\n")
        
        for i, file_path in enumerate(text_files, 1):
            print(f"[{i}/{len(text_files)}]", end=" ")
            
            raw_response = self.generate_code_from_file(str(file_path), custom_prompt)
            
            if raw_response:
                # コードブロックから中身のPythonコードだけを抽出
                code = self._extract_python_code(raw_response)
                if code:
                    self.save_code(file_path.stem, code, raw_response)
                    print(f"  ✅ Code generated and saved")
                else:
                    print(f"  ⚠️  Model generated response, but failed to extract code block.")
            else:
                print(f"  ❌ Failed")

    def process_single_file(self, file_path, custom_prompt=None):
        """単一の問題ファイルを解析してコードを生成"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        raw_response = self.generate_code_from_file(file_path, custom_prompt)
        if not raw_response:
            print("❌ Failed to generate response")
            return None
            
        code = self._extract_python_code(raw_response)
        if code:
            base_name = Path(file_path).stem
            self.save_code(base_name, code, raw_response)
            print(f"  ✅ Code generated and saved")
            return code
        else:
            print(f"  ⚠️  Failed to extract code block.")
            return None

    def _extract_python_code(self, response_text):
        """AIの出力から ```python ... ``` の中身だけを取り出す"""
        pattern = r"```python\s*(.*?)\s*```"
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 万が一バッククォーツだけのブロックだった場合のフォールバック
        pattern_fallback = r"```\s*(.*?)\s*```"
        match_fallback = re.search(pattern_fallback, response_text, re.DOTALL)
        if match_fallback:
            return match_fallback.group(1)
            
        return None
    
    def save_code(self, base_name, code, raw_response):
        """提出用の.pyファイルと、ログ用の生の出力を保存"""
        output_dir = "./generated_codes"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 提出用Pythonコードの保存
        py_file = os.path.join(output_dir, f"solution_{base_name}.py")
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"💾 Saved submission code: {py_file}")
        
        # 2. AIの生出力（万が一解説が含まれていた場合のためのバックアップ）
        log_file = os.path.join(output_dir, f"log_{base_name}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(raw_response)
        print(f"📄 Saved full log: {log_file}")


# ============================================
# 設定項目
# ============================================
# web_scraper.py で保存したテキストが入っているフォルダ
TARGET_FOLDER = "./scraped_texts"

# 単一ファイルだけでテストしたい場合
SINGLE_FILE_PATH = None

# 使用するOllamaモデル
MODEL_NAME = 'qwen2.5vl:latest'
# ============================================


def main():
    print("="*60)
    print("🤖 Competitive Code Generator - 競プロ解答自動生成")
    print("="*60)
    
    generator = CompetitiveCodeGenerator(model=MODEL_NAME)
    
    if TARGET_FOLDER:
        print(f"  - モード: フォルダ内問題の一括解答")
        print(f"  - 対象フォルダ: {TARGET_FOLDER}")
        generator.process_folder(TARGET_FOLDER)
    elif SINGLE_FILE_PATH:
        print(f"  - モード: 単一問題解答")
        print(f"  - 対象ファイル: {SINGLE_FILE_PATH}")
        generator.process_single_file(SINGLE_FILE_PATH)
    else:
        print("\n❌ 解析対象が設定されていません")


if __name__ == "__main__":
    main()