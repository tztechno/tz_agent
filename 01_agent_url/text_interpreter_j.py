# text_interpreter.py
import ollama
import os
import json
from datetime import datetime
from pathlib import Path

class TextInterpreter:
    """スクレイピングされたテキストの内容を解析・解釈するクラス"""
    
    def __init__(self, model='qwen2.5vl:latest'):
        self.model = model
        self.analysis_history = []
    
    def analyze_text_file(self, file_path, custom_prompt=None):
        """テキストファイルを読み込んでOllamaで解析"""
        print(f"[Analyzing] {os.path.basename(file_path)}")
        
        if not os.path.exists(file_path):
            print(f"  ❌ File not found: {file_path}")
            return None
        
        # テキストデータの読み込み
        with open(file_path, "r", encoding="utf-8") as f:
            scraped_content = f.read()

        # デフォルトプロンプト（動画の文字起こし・多言語解析・翻訳要約用）
        if custom_prompt is None:
            prompt = f"""あなたは優秀な技術リサーチアシスタントです。
提供されたデータは、動画から抽出された「文字起こし（トランスクリプト）データ」です。口語表現や、句読点のないテキスト、または英語のデータが含まれている可能性があります。
内容を深く精読・理解した上で、エッセンスを抽出し、日本の開発者向けに客観的かつ構造的な「日本語の要約レポート」を作成してください。

【解析対象データ】
{scraped_content}

上記のデータに基づき、以下の構成でわかりやすい日本語レポートを出力してください。

【1. 動画の概要（サマリー）】
- この動画が全体として何について解説しているか、テーマや結論の全体像を3行程度で簡潔に要約してください。

【2. 重要トピック・技術的ポイント】
- 動画内で述べられている主要な主張、提示されたデータ、重要な事実や技術的キーワード（専門用語）を3〜5つのセクションに分けて、箇条書きを交えて分かりやすく整理してください。海外独自の概念や固有名詞がある場合は、補足説明も加えてください。

【3. 発表の背景と意図（コンテキスト）】
- スピーカーがなぜこのテーマについて話しているのか、技術的な課題、背景、またはその意図について、文字起こしから読み取れる文脈を記述してください。

【4. キーインサイト・エンジニアへの示唆】
- この動画から得られる最終的な結論や、日本のエンジニアが今後の開発・研究・実務において次にアクションを起こすためのヒント、あるいはトレンドに対する客観的な見解を述べてください。

※元の言語が英語の場合でも、翻訳調ではなく、自然でプロフェッショナルな日本語の常体（である調）で記述してください。
※出力は通常のプレーンテキスト（マークダウン形式推奨）で記述してください。
"""

        else:
            prompt = f"{custom_prompt}\n\n【解析対象データ】\n{scraped_content}"
        
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
    
    def analyze_folder(self, folder_path, output_format='html', custom_prompt=None):
        """フォルダ内の全テキストファイルを解析"""
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            return None
        
        text_files = [f for f in folder.iterdir() if f.suffix.lower() == '.txt']
        
        if not text_files:
            print(f"\n⚠️  No text files found in {folder_path}")
            return None
        
        print(f"\n📝 Analyzing {len(text_files)} text file(s)\n")
        
        all_results = []
        
        for i, file_path in enumerate(text_files, 1):
            print(f"[{i}/{len(text_files)}]", end=" ")
            
            analysis = self.analyze_text_file(str(file_path), custom_prompt)
            
            if analysis:
                print(f"  ✅ Analysis generated")
                all_results.append({
                    'file': file_path.name,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"  ❌ Failed")
                all_results.append({
                    'file': file_path.name,
                    'error': 'No analysis generated',
                    'timestamp': datetime.now().isoformat()
                })
        
        self.save_results(all_results, output_format)
        return all_results

    def analyze_single_file(self, file_path, output_format='html', custom_prompt=None):
        """単一ファイルを解析"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        analysis = self.analyze_text_file(file_path, custom_prompt)
        
        if not analysis:
            print("❌ No analysis generated")
            return None
        
        result = {
            'file': os.path.basename(file_path),
            'file_path': file_path,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Analysis generated")
        self.save_single_result(result, output_format)
        return result
    
    def save_single_result(self, result, output_format='html'):
        """単一結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = f"analysis_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON saved: {json_file}")
        
        txt_file = f"analysis_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Source File: {result['file']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"{'='*60}\n\n")
            f.write(result['analysis'])
        print(f"📄 Text saved: {txt_file}")
        
        if output_format.lower() == 'html':
            self.generate_html_report([result], timestamp)
    
    def save_results(self, results, output_format='html'):
        """複数結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = f"analysis_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON saved: {json_file}")
        
        txt_file = f"analysis_summary_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for i, result in enumerate(results, 1):
                f.write(f"\n{'='*60}\n")
                f.write(f"Text {i}: {result.get('file', 'unknown')}\n")
                f.write(f"Timestamp: {result.get('timestamp', 'unknown')}\n")
                f.write(f"{'='*60}\n\n")
                if 'analysis' in result:
                    f.write(result['analysis'])
                elif 'error' in result:
                    f.write(f"ERROR: {result['error']}")
                f.write("\n\n")
        print(f"📄 Text summary: {txt_file}")
        
        if output_format.lower() == 'html':
            self.generate_html_report(results, timestamp)
        
        self.print_summary(results)
    
    def generate_html_report(self, results, timestamp):
        """HTMLレポート生成"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Web Content Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Noto Sans JP', Arial, sans-serif;
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: #333;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .header h1 {{ color: #2c3e50; }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .card h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .analysis {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 20px;
            border-radius: 8px;
            line-height: 1.8;
            font-size: 15px;
            white-space: pre-wrap;
        }}
        .error {{
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
        }}
        .metadata {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 12px;
        }}
        .stats {{
            display: inline-block;
            background: #2c3e50;
            color: white;
            padding: 5px 12px;
            border-radius: 5px;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 Web Content Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Files Processed: {len(results)}</p>
        <p>Model Used: {self.model}</p>
    </div>
"""
        
        for idx, result in enumerate(results, 1):
            title = result.get('file', 'unknown')
            html += f"""
    <div class="card">
        <h2>📄 Data {idx}: {title}</h2>
"""
            if 'error' in result:
                html += f'<div class="error">❌ Error: {result["error"]}</div>'
            elif 'analysis' in result:
                analysis_text = result['analysis'].replace('\n', '<br>')
                html += f"""
        <div class="analysis">
            {analysis_text}
        </div>
"""
            
            html += f"""
        <div class="metadata">
            <span class="stats">🕐 {result['timestamp']}</span>
        </div>
    </div>
"""
        
        html += """
</div>
</body>
</html>"""
        
        html_file = f"analysis_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📄 HTML report: {html_file}")
    
    def print_summary(self, results):
        """サマリー表示"""
        print(f"\n{'='*50}")
        print("📊 Analysis Summary")
        print(f"{'='*50}")
        
        success_count = len([r for r in results if 'analysis' in r])
        error_count = len([r for r in results if 'error' in r])
        
        print(f"✅ Successful analyses: {success_count} file(s)")
        print(f"❌ Errors: {error_count} file(s)")
        print(f"📁 Total processed: {len(results)} file(s)")
        print(f"{'='*50}\n")


# ============================================
# 設定項目
# ============================================
TARGET_FOLDER = "./scraped_texts"
#TARGET_FOLDER = "./output_text"
SINGLE_FILE_PATH = None
OUTPUT_FORMAT = 'html'
MODEL_NAME = 'qwen2.5vl:latest'
CUSTOM_PROMPT = None
# ============================================


def main():
    print("="*60)
    print("📊 Web Text Interpreter - 汎用Webページ解析ツール")
    print("="*60)
    
    interpreter = TextInterpreter(model=MODEL_NAME)
    
    if TARGET_FOLDER:
        print(f"  - モード: フォルダ内テキストの一括解析")
        print(f"  - 対象フォルダ: {TARGET_FOLDER}")
        interpreter.analyze_folder(TARGET_FOLDER, OUTPUT_FORMAT, CUSTOM_PROMPT)
    elif SINGLE_FILE_PATH:
        print(f"  - モード: 単一ファイル解析")
        print(f"  - 対象ファイル: {SINGLE_FILE_PATH}")
        interpreter.analyze_single_file(SINGLE_FILE_PATH, OUTPUT_FORMAT, CUSTOM_PROMPT)
    else:
        print("\n❌ 解析対象が設定されていません")


if __name__ == "__main__":
    main()