# table_analyzer.py
import ollama
import base64
import os
import json
import re
import csv
from datetime import datetime
from pathlib import Path

class TableAnalyzer:
    """画像からテーブルデータを解析するクラス"""
    
    def __init__(self, model='qwen2.5vl:latest'):
        self.model = model
        self.analysis_history = []
    
    def analyze_image(self, image_path, custom_prompt=None):
        """画像を解析してテーブルデータを抽出"""
        print(f"[Analyzing] {os.path.basename(image_path)}")
        
        if not os.path.exists(image_path):
            print(f"  ❌ Image not found: {image_path}")
            return None
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        if custom_prompt is None:
            prompt = """Extract all table data visible in this image.

Extraction rules:
1. Automatically detect table structure (columns, rows)
2. Extract all columns and values without missing any
3. Convert numbers to appropriate types (integer, float)
4. Preserve empty cells and special characters as much as possible
5. Extract table titles and annotations separately

Output format (JSON):
{
  "table_title": "Table title (if exists)",
  "columns": ["Column1", "Column2", "Column3"],
  "data": [
    {"Column1": "Value1", "Column2": "Value2", "Column3": "Value3"},
    ...
  ],
  "notes": "Notes or supplementary information",
  "metadata": {
    "rows_count": number_of_rows,
    "columns_count": number_of_columns
  }
}

Output only JSON, no explanatory text."""
        else:
            prompt = custom_prompt
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [image_data]
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"  ❌ Model error: {e}")
            return None
    
    def extract_json(self, text):
        """レスポンスからJSONを抽出"""
        if not text:
            return None
        
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        print(f"  ⚠️ JSON extraction failed")
        return None
    
    def analyze_folder(self, folder_path, output_format='html', custom_prompt=None):
        """フォルダ内の全画像を解析"""
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            return None
        
        images = [f for f in folder.iterdir() 
                 if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')]
        
        if not images:
            print(f"\n⚠️  No images found in {folder_path}")
            return None
        
        print(f"\n📷 Analyzing {len(images)} image(s)\n")
        
        all_results = []
        
        for i, img_path in enumerate(images, 1):
            print(f"[{i}/{len(images)}]", end=" ")
            
            response = self.analyze_image(str(img_path), custom_prompt)
            
            if response:
                data = self.extract_json(response)
                if data:
                    print(f"  ✅ Extraction successful")
                    all_results.append({
                        'file': img_path.name,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print(f"  ⚠️ JSON parsing failed")
                    all_results.append({
                        'file': img_path.name,
                        'raw_response': response,
                        'timestamp': datetime.now().isoformat()
                    })
            else:
                print(f"  ❌ No response")
                all_results.append({
                    'file': img_path.name,
                    'error': 'No response from model',
                    'timestamp': datetime.now().isoformat()
                })
        
        self.save_results(all_results, output_format)
        return all_results
    
    def analyze_single_image(self, image_path, output_format='html', custom_prompt=None):
        """単一画像を解析"""
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return None
        
        response = self.analyze_image(image_path, custom_prompt)
        
        if not response:
            print("❌ No response from model")
            return None
        
        data = self.extract_json(response)
        
        result = {
            'file': os.path.basename(image_path),
            'image_path': image_path,
            'timestamp': datetime.now().isoformat(),
            'raw_response': response
        }
        
        if data:
            result['data'] = data
            print(f"✅ Extraction successful")
        else:
            print(f"⚠️ JSON parsing failed")
        
        self.save_single_result(result, output_format)
        return result
    
    def save_single_result(self, result, output_format='html'):
        """単一結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = f"analysis_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON saved: {json_file}")
        
        if output_format.lower() == 'html':
            self.generate_html_report([result], timestamp)
        elif output_format.lower() == 'csv':
            self.generate_csv_files([result], timestamp)
    
    def save_results(self, results, output_format='html'):
        """複数結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_file = f"analysis_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON saved: {json_file}")
        
        if output_format.lower() == 'html':
            self.generate_html_report(results, timestamp)
        elif output_format.lower() == 'csv':
            self.generate_csv_files(results, timestamp)
        
        self.print_summary(results)
    
    def generate_html_report(self, results, timestamp):
        """HTMLレポート生成"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Table Analysis Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .card h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            overflow-x: auto;
            display: block;
        }}
        th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
        th {{ background: #667eea; color: white; font-weight: bold; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .error {{ background: #fee; color: #c33; padding: 10px; border-radius: 5px; }}
        .metadata {{ background: #f0f0f0; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 12px; }}
        .stats {{ display: inline-block; background: #667eea; color: white; padding: 5px 10px; border-radius: 5px; margin-right: 10px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📊 Table Analysis Report</h1>
        <p>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Items Processed: {len(results)}</p>
        <p>Model Used: {self.model}</p>
    </div>
"""
        
        for idx, result in enumerate(results, 1):
            title = result.get('file', 'unknown')
            html += f"""
    <div class="card">
        <h2>📷 Image {idx}: {title}</h2>
"""
            if 'error' in result:
                html += f'<div class="error">❌ Error: {result["error"]}</div>'
            elif 'data' in result:
                data = result['data']
                if isinstance(data, list):
                    for table_idx, table in enumerate(data, 1):
                        html += self._render_table(table, f"Table {table_idx}")
                elif isinstance(data, dict):
                    html += self._render_table(data, "Extracted Data")
            
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
    


    def _render_table(self, data, title):
        """テーブルをHTMLレンダリング"""
        html = f"<h3>{title}</h3>"
        
        if 'data' in data and isinstance(data['data'], list) and data['data']:
            columns = data.get('columns', list(data['data'][0].keys()))
            
            # 修正：開始タグを <table> に変更
            html += "<table><thead><tr>"
            for col in columns:
                html += f"<th>{col}</th>"
            # 修正：<tr> を </tr> に変更
            html += "</tr></thead><tbody>"
            
            for row in data['data']:
                html += "<tr>"
                for col in columns:
                    value = row.get(col, '')
                    # 修正：<tr> を <td> に変更
                    html += f"<td>{value}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            
            if 'metadata' in data:
                html += f"""<div class="metadata">
                    <small>Rows: {data['metadata'].get('rows_count', len(data['data']))} | 
                    Columns: {data['metadata'].get('columns_count', len(columns))}</small>
                </div>"""
        
        if 'table_title' in data and data['table_title']:
            html += f"<p><strong>Title:</strong> {data['table_title']}</p>"
        if 'notes' in data and data['notes']:
            html += f"<p><strong>Notes:</strong> {data['notes']}</p>"
        
        return html
        """テーブルをHTMLレンダリング"""
        html = f"<h3>{title}</h3>"
        
        if 'data' in data and isinstance(data['data'], list) and data['data']:
            columns = data.get('columns', list(data['data'][0].keys()))
            


            html += """</td><thead><tr>"""
            for col in columns:
                html += f"<th>{col}</th>"
            html += "<tr></thead><tbody>"
            
            for row in data['data']:
                html += "<tr>"
                for col in columns:
                    value = row.get(col, '')
                    html += f"<tr>{value}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            
            if 'metadata' in data:
                html += f"""<div class="metadata">
                    <small>Rows: {data['metadata'].get('rows_count', len(data['data']))} | 
                    Columns: {data['metadata'].get('columns_count', len(columns))}</small>
                </div>"""
        
        if 'table_title' in data and data['table_title']:
            html += f"<p><strong>Title:</strong> {data['table_title']}</p>"
        if 'notes' in data and data['notes']:
            html += f"<p><strong>Notes:</strong> {data['notes']}</p>"
        
        return html
    


    def generate_csv_files(self, results, timestamp):
        """CSVファイル生成"""
        for idx, result in enumerate(results, 1):
            if 'data' not in result:
                continue
            
            data = result['data']
            if isinstance(data, list):
                for table_idx, table in enumerate(data, 1):
                    if 'data' in table and table['data']:
                        filename = f"table_{timestamp}_{idx}_{table_idx}.csv"
                        self._write_csv(filename, table['data'], table.get('columns'))
            elif isinstance(data, dict) and 'data' in data and data['data']:
                filename = f"table_{timestamp}_{idx}.csv"
                self._write_csv(filename, data['data'], data.get('columns'))
    
    def _write_csv(self, filename, data, columns=None):
        """CSV書き込み"""
        if not data:
            return
        
        if not columns:
            columns = list(data[0].keys())
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(data)
        print(f"📊 CSV output: {filename}")
    
    def print_summary(self, results):
        """結果サマリー表示"""
        print(f"\n{'='*50}")
        print("📊 Analysis Summary")
        print(f"{'='*50}")
        
        success_count = len([r for r in results if 'data' in r])
        error_count = len([r for r in results if 'error' in r])
        
        print(f"✅ Successful: {success_count} image(s)")
        print(f"❌ Errors: {error_count} image(s)")
        print(f"📁 Total processed: {len(results)} image(s)")
        
        total_rows = 0
        for r in results:
            if 'data' in r:
                data = r['data']
                if isinstance(data, dict) and 'data' in data:
                    total_rows += len(data['data'])
                elif isinstance(data, list):
                    for table in data:
                        if isinstance(table, dict) and 'data' in table:
                            total_rows += len(table['data'])
        
        print(f"📊 Total rows extracted: {total_rows}")
        print(f"{'='*50}\n")


# ============================================
# ここに解析したい設定を直接書き込む
# ============================================
# 解析する画像フォルダ（Noneの場合は単一画像モード）
TARGET_FOLDER = "./screenshots"

# 単一画像を解析する場合のパス（TARGET_FOLDERがNoneの場合に使用）
SINGLE_IMAGE_PATH = None

# 出力形式: 'html' または 'csv'
OUTPUT_FORMAT = 'html'

# 使用するOllamaモデル
MODEL_NAME = 'qwen2.5vl:latest'

# カスタムプロンプト（必要に応じて設定）
CUSTOM_PROMPT = None
# 例:
# CUSTOM_PROMPT = "Extract only the numeric data from this table..."
# ============================================


def main():
    """メイン実行関数 - コード内の設定を使用"""
    print("="*60)
    print("🔍 Table Analyzer - Image Table Extraction Tool")
    print("="*60)
    
    analyzer = TableAnalyzer(model=MODEL_NAME)
    
    print(f"\n📋 設定:")
    print(f"  - モデル: {MODEL_NAME}")
    print(f"  - 出力形式: {OUTPUT_FORMAT}")
    
    if TARGET_FOLDER:
        print(f"  - モード: フォルダ解析")
        print(f"  - 対象フォルダ: {TARGET_FOLDER}")
        analyzer.analyze_folder(TARGET_FOLDER, OUTPUT_FORMAT, CUSTOM_PROMPT)
    elif SINGLE_IMAGE_PATH:
        print(f"  - モード: 単一画像解析")
        print(f"  - 対象画像: {SINGLE_IMAGE_PATH}")
        analyzer.analyze_single_image(SINGLE_IMAGE_PATH, OUTPUT_FORMAT, CUSTOM_PROMPT)
    else:
        print("\n❌ 解析対象が設定されていません")
        print("コード内の以下の変数を設定してください:")
        print("  - TARGET_FOLDER (フォルダ解析)")
        print("  - または SINGLE_IMAGE_PATH (単一画像解析)")


if __name__ == "__main__":
    main()