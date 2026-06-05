# web_scraper.py
import os
import time
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

class WebScraper:
    """Webページのテキストコンテンツをスクレイピングするクラス"""
    
    def __init__(self, output_dir="./scraped_texts"):
        self.output_dir = output_dir
        # 出力ディレクトリの作成
        os.makedirs(output_dir, exist_ok=True)
        
        # サイトにブロックされにくくするための標準的なヘッダー
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def scrape(self, url, filename=None):
        """
        URLからテキストを抽出して保存
        
        Args:
            url: 対象URL
            filename: 保存ファイル名（Noneの場合は自動生成）
        
        Returns:
            保存されたファイルパス（失敗時はNone）
        """
        print(f"[Scraping] Fetching: {url}")
        
        # ファイル名の生成
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_url = self._sanitize_filename(url)
            filename = f"{safe_url}_{timestamp}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # ページリクエストの送信
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # 文字コードの自動設定
            response.encoding = response.apparent_encoding
            
            # HTMLの解析と不要要素のクレンジング
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # スクリプト、スタイル、ナビゲーションなど不要なテキスト要素を排除
            for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                element.decompose()
            
            # プレーンテキストの抽出
            text_content = soup.get_text()
            
            # 行間の余分な空白や改行をクレンジング
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)
            
            # テキストファイルとして保存
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Source URL: {url}\n")
                f.write(f"Scraped Time: {datetime.now().isoformat()}\n")
                f.write(f"{'='*60}\n\n")
                f.write(clean_text)
            
            print(f"  ✅ Text scraped and saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"  ❌ Scraping failed: {e}")
            return None
    
    def scrape_multiple(self, urls):
        """複数のURLを連続スクレイピング"""
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")
            filepath = self.scrape(url)
            results.append({
                'url': url,
                'filepath': filepath,
                'success': filepath is not None
            })
            # 連続アクセスによる負荷軽減のための短いウェイト
            time.sleep(1)
        
        # サマリー表示
        success_count = sum(1 for r in results if r['success'])
        print(f"\n{'='*50}")
        print(f"📝 Scraping Summary")
        print(f"{'='*50}")
        print(f"✅ Success: {success_count}/{len(urls)}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"{'='*50}")
        
        return results
    
    def _sanitize_filename(self, url):
        """URLから安全なファイル名を生成"""
        safe = re.sub(r'^https?://', '', url)
        safe = re.sub(r'[^a-zA-Z0-9]', '_', safe)
        safe = safe[:50]
        return safe


# ============================================
# ここにスクレイピングしたいURLを直接書き込む
# ============================================
TARGET_URLS = [
    "https://zenn.dev/kairim/articles/35dd71c526b64f",
]
# ============================================


def main():
    """メイン実行関数 - コード内のURLを使用"""
    print("="*60)
    print("📝 Web Scraper Tool (Text Base)")
    print("="*60)
    
    if not TARGET_URLS:
        print("❌ TARGET_URLSが設定されていません")
        print("コード内の TARGET_URLS リストにURLを追加してください")
        return
    
    print(f"\n📋 対象URL: {len(TARGET_URLS)}件")
    for i, url in enumerate(TARGET_URLS, 1):
        print(f"  {i}. {url}")
    
    scraper = WebScraper()
    scraper.scrape_multiple(TARGET_URLS)


if __name__ == "__main__":
    main()