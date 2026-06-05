# screenshot_capture.py
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class ScreenshotCapture:
    """Webページのスクリーンショットを撮影するクラス"""
    
    def __init__(self, output_dir="./screenshots"):
        self.output_dir = output_dir
        # 出力ディレクトリの作成
        os.makedirs(output_dir, exist_ok=True)
    
    def capture(self, url, wait_time=3, filename=None):
        """
        URLのスクリーンショットを撮影
        
        Args:
            url: 対象URL
            wait_time: ページ読み込み待機時間（秒）
            filename: 保存ファイル名（Noneの場合は自動生成）
        
        Returns:
            保存されたファイルパス（失敗時はNone）
        """
        print(f"[Screenshot] Capturing: {url}")
        
        # Chromeオプション設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # ヘッドレスモード
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        
        # ファイル名の生成
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_url = self._sanitize_filename(url)
            filename = f"{safe_url}_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        driver = None
        try:
            # ChromeDriverの自動セットアップ
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # URLにアクセス
            driver.get(url)
            
            # ページ読み込み待機
            time.sleep(wait_time)
            
            # スクリーンショット保存
            driver.save_screenshot(filepath)
            
            print(f"  ✅ Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"  ❌ Screenshot failed: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()
    
    def capture_multiple(self, urls, wait_time=3):
        """複数のURLのスクリーンショットを撮影"""
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")
            filepath = self.capture(url, wait_time)
            results.append({
                'url': url,
                'filepath': filepath,
                'success': filepath is not None
            })
        
        # サマリー表示
        success_count = sum(1 for r in results if r['success'])
        print(f"\n{'='*50}")
        print(f"📸 Screenshot Summary")
        print(f"{'='*50}")
        print(f"✅ Success: {success_count}/{len(urls)}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"{'='*50}")
        
        return results
    
    def _sanitize_filename(self, url):
        """URLから安全なファイル名を生成"""
        import re
        safe = re.sub(r'^https?://', '', url)
        safe = re.sub(r'[^a-zA-Z0-9]', '_', safe)
        safe = safe[:50]
        return safe


# ============================================
# ここに撮影したいURLを直接書き込む
# ============================================
TARGET_URLS = [
"https://kakaku.com/item/J0000049128/",
"https://kakaku.com/item/K0001714995/pricehistory/",
"https://kakaku.com/item/K0001714996/pricehistory/",
"https://kakaku.com/keyword/",
]

WAIT_TIME = 3  # ページ読み込み待機時間（秒）
# ============================================


def main():
    """メイン実行関数 - コード内のURLを使用"""
    print("="*60)
    print("📸 Screenshot Capture Tool")
    print("="*60)
    
    if not TARGET_URLS:
        print("❌ TARGET_URLSが設定されていません")
        print("コード内の TARGET_URLS リストにURLを追加してください")
        return
    
    print(f"\n📋 対象URL: {len(TARGET_URLS)}件")
    for i, url in enumerate(TARGET_URLS, 1):
        print(f"  {i}. {url}")
    
    capture = ScreenshotCapture()
    capture.capture_multiple(TARGET_URLS, WAIT_TIME)


if __name__ == "__main__":
    main()