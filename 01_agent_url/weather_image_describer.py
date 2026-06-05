# image_describer.py
import ollama
import base64
import os
import json
import re
from datetime import datetime
from pathlib import Path

class ImageDescriber:
    """画像の内容を文章で説明するクラス"""
    
    def __init__(self, model='qwen2.5vl:latest'):
        self.model = model
        self.description_history = []
    
    def describe_image(self, image_path, custom_prompt=None):
        """画像を解析して文章で説明"""
        print(f"[Describing] {os.path.basename(image_path)}")
        
        if not os.path.exists(image_path):
            print(f"  ❌ Image not found: {image_path}")
            return None
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # デフォルトプロンプト（文章記述用）
        if custom_prompt is None:
            
            
            prompt = """あなたはベテランの気象予報士です。提供された日本周辺の天気図画像を詳細に解析し、プロとしての深い洞察に基づいた気象レポートを作成してください。

画像を解析する際は、特に以下の「天気図の解読ルール」を厳守してください。

⚠️【最重要：天気図の解読ルール】
1. 移動方向の誤認に注意：天気図上の「白い矢印（◯km/h）」は、その低気圧や高気圧が「進む方向」を示しています。矢印の向き（右＝東、右上＝北東など）を物理的に正しく解釈してください。日本周辺のシステムは基本的に西から東へ進みます。
2. 前線の種類の見分け：
   - 赤の半円と青の三角が並んでいる長い前線は『停滞前線（梅雨前線）』です。
   - 青い三角だけは『寒冷前線』、赤い半円だけは『温暖前線』です。
3. 文字の紐づけ：気圧の数字（例: 992）や「熱低」などの文字が、どの「×」印（中心位置）を指しているか、位置関係を正確に読み取ってください。

以下の【フォーマット】に従ってレポートを出力してください。括弧内の指示文そのものは出力に含めず、具体的な解析結果の文章のみを記述してください。

【1. 基本情報】
- 天気図の種類：(例: 地上天気図)
- 日時・対象領域：(例: 令和8年6月5日9時、日本周辺)

【2. 主要な気象システム】
- 高気圧：(中心気圧、位置、および今後の動きを解説)
- 低気圧・熱帯低気圧：(中心気圧、位置、矢印から読み取れる移動方向、発達具合を解説)
- 前線：(識別した前線の種類、位置、活動度を解説)

【3. 気象分布の要約】
- 等圧線の混み具合と風の強さ：(どのエリアで風が強まるか)
- 注目すべき気象特徴：(トラフ、リッジ、または高気圧の張り出しの有無)
- 現時点での天気傾向：(晴れ、雨、荒天の予想エリア)

【4. 気象予報士としての見解（今後の予測）】
- 今後の気象変化：(今後数時間〜翌日にかけての気象の変化を論理的に予測)
- 注意・警戒すべきポイント：(強風、大雨、雷、気温急変など、自治体や国民が警戒すべき点)

※「矢印の向きを正しく読み取ること」などの指示文そのものは出力に含めないでください。
※文章は客観的、かつプロの気象予報士として自然な語り口で構成してください。"""

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
    
    def describe_folder(self, folder_path, output_format='html', custom_prompt=None):
        """フォルダ内の全画像を解析して説明"""
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            return None
        
        images = [f for f in folder.iterdir() 
                 if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')]
        
        if not images:
            print(f"\n⚠️  No images found in {folder_path}")
            return None
        
        print(f"\n📷 Describing {len(images)} image(s)\n")
        
        all_results = []
        
        for i, img_path in enumerate(images, 1):
            print(f"[{i}/{len(images)}]", end=" ")
            
            description = self.describe_image(str(img_path), custom_prompt)
            
            if description:
                print(f"  ✅ Description generated")
                all_results.append({
                    'file': img_path.name,
                    'description': description,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"  ❌ Failed")
                all_results.append({
                    'file': img_path.name,
                    'error': 'No description generated',
                    'timestamp': datetime.now().isoformat()
                })
        
        self.save_results(all_results, output_format)
        return all_results
    
    def describe_single_image(self, image_path, output_format='html', custom_prompt=None):
        """単一画像を解析して説明"""
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return None
        
        description = self.describe_image(image_path, custom_prompt)
        
        if not description:
            print("❌ No description generated")
            return None
        
        result = {
            'file': os.path.basename(image_path),
            'image_path': image_path,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Description generated")
        self.save_single_result(result, output_format)
        return result
    
    def save_single_result(self, result, output_format='html'):
        """単一結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON保存
        json_file = f"description_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON saved: {json_file}")
        
        # テキストファイル保存
        txt_file = f"description_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Image: {result['file']}\n")
            f.write(f"Timestamp: {result['timestamp']}\n")
            f.write(f"{'='*60}\n\n")
            f.write(result['description'])
        print(f"📄 Text saved: {txt_file}")
        
        # HTML出力
        if output_format.lower() == 'html':
            self.generate_html_report([result], timestamp)
    
    def save_results(self, results, output_format='html'):
        """複数結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON保存
        json_file = f"description_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON saved: {json_file}")
        
        # テキストファイル（全結果を1ファイルに）
        txt_file = f"descriptions_summary_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for i, result in enumerate(results, 1):
                f.write(f"\n{'='*60}\n")
                f.write(f"Image {i}: {result.get('file', 'unknown')}\n")
                f.write(f"Timestamp: {result.get('timestamp', 'unknown')}\n")
                f.write(f"{'='*60}\n\n")
                if 'description' in result:
                    f.write(result['description'])
                elif 'error' in result:
                    f.write(f"ERROR: {result['error']}")
                f.write("\n\n")
        print(f"📄 Text summary: {txt_file}")
        
        # HTML出力
        if output_format.lower() == 'html':
            self.generate_html_report(results, timestamp)
        
        # サマリー表示
        self.print_summary(results)
    
    def generate_html_report(self, results, timestamp):
        """HTMLレポート生成（文章記述用）"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Image Description Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Noto Sans JP', Arial, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
        .header h1 {{ color: #11998e; }}
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            color: #11998e;
            border-bottom: 2px solid #11998e;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .description {{
            background: #f8f9fa;
            border-left: 4px solid #11998e;
            padding: 20px;
            border-radius: 8px;
            line-height: 1.8;
            font-size: 14px;
            white-space: pre-wrap;
            font-family: 'Segoe UI', 'Noto Sans JP', monospace;
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
            background: #11998e;
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
        <h1>📝 Image Description Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Images Processed: {len(results)}</p>
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
            elif 'description' in result:
                # 説明文を整形
                description_text = result['description'].replace('\n', '<br>')
                html += f"""
        <div class="description">
            {description_text}
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
        
        html_file = f"description_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📄 HTML report: {html_file}")
    
    def print_summary(self, results):
        """結果サマリー表示"""
        print(f"\n{'='*50}")
        print("📝 Description Summary")
        print(f"{'='*50}")
        
        success_count = len([r for r in results if 'description' in r])
        error_count = len([r for r in results if 'error' in r])
        
        print(f"✅ Successful descriptions: {success_count} image(s)")
        print(f"❌ Errors: {error_count} image(s)")
        print(f"📁 Total processed: {len(results)} image(s)")
        
        # 文字数統計
        total_chars = 0
        for r in results:
            if 'description' in r:
                total_chars += len(r['description'])
        
        if success_count > 0:
            avg_chars = total_chars // success_count
            print(f"📊 Average description length: {avg_chars} characters")
        print(f"{'='*50}\n")


# ============================================
# ここに解析したい設定を直接書き込む
# ============================================
# 説明する画像フォルダ（Noneの場合は単一画像モード）
TARGET_FOLDER = "./screenshots"

# 単一画像を説明する場合のパス（TARGET_FOLDERがNoneの場合に使用）
SINGLE_IMAGE_PATH = None

# 出力形式: 'html' または 'txt'（テキストファイル）
OUTPUT_FORMAT = 'html'

# 使用するOllamaモデル
MODEL_NAME = 'qwen2.5vl:latest'

# カスタムプロンプト（必要に応じて設定）
CUSTOM_PROMPT = None
# 例:
# CUSTOM_PROMPT = "Describe this image in Japanese, focusing on business data and trends"
# CUSTOM_PROMPT = "Explain what this screenshot shows, as if teaching a beginner"
# ============================================


def main():
    """メイン実行関数 - コード内の設定を使用"""
    print("="*60)
    print("📝 Image Describer - 画像内容を文章で説明")
    print("="*60)
    
    describer = ImageDescriber(model=MODEL_NAME)
    
    print(f"\n📋 設定:")
    print(f"  - モデル: {MODEL_NAME}")
    print(f"  - 出力形式: {OUTPUT_FORMAT}")
    
    if TARGET_FOLDER:
        print(f"  - モード: フォルダ解析")
        print(f"  - 対象フォルダ: {TARGET_FOLDER}")
        describer.describe_folder(TARGET_FOLDER, OUTPUT_FORMAT, CUSTOM_PROMPT)
    elif SINGLE_IMAGE_PATH:
        print(f"  - モード: 単一画像解析")
        print(f"  - 対象画像: {SINGLE_IMAGE_PATH}")
        describer.describe_single_image(SINGLE_IMAGE_PATH, OUTPUT_FORMAT, CUSTOM_PROMPT)
    else:
        print("\n❌ 解析対象が設定されていません")
        print("コード内の以下の変数を設定してください:")
        print("  - TARGET_FOLDER (フォルダ内の画像を説明)")
        print("  - または SINGLE_IMAGE_PATH (単一画像を説明)")


if __name__ == "__main__":
    main()