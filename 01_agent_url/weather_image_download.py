# screenshot_capture.py
import os
import time
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image  # 必須: pip install Pillow

# ============================================
# ⚙️ 設定パラメータ（ここを書き換えて位置を微調整してください）
# ============================================
TARGET_URLS = [
    "https://www.jma.go.jp/bosai/weather_map/",
]

WAIT_TIME = 3  # ページ読み込み待機時間（秒）

# --- ✂️ トリミング（切り抜き）の自由座標設定 ---
# 1920x1080 の元画像から、切り取りたい「左上の位置」と「サイズ」を指定します。
CROP_PARAMS = {
    "start_x": 500,   # 切り取りを開始する左端の座標 (X座標)
    "start_y": 160,   # 切り取りを開始する上端の座標 (Y座標)
    "width": 596,    # そこから右に何ピクセル切り取るか (幅)
    "height": 580     # そこから下に何ピクセル切り取るか (高さ)
}
# ============================================


class ScreenshotCapture:
    """Webページのスクリーンショットを撮影・加工し、固定フォルダへ出力するクラス"""
    
    def __init__(self, output_dir="./screenshots", final_dir="./input_weather"):
        self.output_dir = output_dir
        self.final_dir = final_dir
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)
    
    def _trim_image(self, image_path):
        """指定された左上の座標(X, Y)と幅・高さに基づいてトリミングする"""
        try:
            with Image.open(image_path) as img:
                img_w, img_h = img.size
                
                # パラメータの読み込み
                x = CROP_PARAMS["start_x"]
                y = CROP_PARAMS["start_y"]
                w = CROP_PARAMS["width"]
                h = CROP_PARAMS["height"]
                
                # クロップ範囲の座標決定 (左, 上, 右, 下)
                left = x
                top = y
                right = x + w
                bottom = y + h
                
                # 画像の実際のサイズを超えないように安全弁を入れる
                right = min(right, img_w)
                bottom = min(bottom, img_h)
                
                # 切り抜きを実行
                cropped_img = img.crop((left, top, right, bottom))
                cropped_img.save(image_path)
                
                print(f"  ✂️ トリミング成功: {img_w}x{img_h} -> {cropped_img.size[0]}x{cropped_img.size[1]}")
                print(f"      (指定範囲: 左上({x}, {y}) から 幅:{w}px, 高さ:{h}px)")
                
        except Exception as e:
            print(f"  ⚠️ トリミング失敗: {e}")

    def capture(self, url, wait_time=3, filename=None):
        print(f"[Screenshot] 撮影開始: {url}")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_url = self._sanitize_filename(url)
            filename = f"{safe_url}_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get(url)
            time.sleep(wait_time)
            driver.save_screenshot(filepath)
            print(f"  ✅ 元画像の保存完了: {filepath}")
            
            # 画像を自由座標で切り抜く
            self._trim_image(filepath)
            
            # 気象庁のURLの場合、固定フォルダ（input_weather/target.png）へコピー
            if "weather_map" in url:
                fixed_dest = os.path.join(self.final_dir, "target.png")
                shutil.copy(filepath, fixed_dest)
                print(f"  🚀 次段の固定フォルダへ複製完了: {fixed_dest}")
                
            return filepath
            
        except Exception as e:
            print(f"  ❌ 撮影エラー: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()
    
    def capture_multiple(self, urls, wait_time=3):
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")
            filepath = self.capture(url, wait_time)
            results.append({
                'url': url,
                'filepath': filepath,
                'success': filepath is not None
            })
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n{'='*50}")
        print(f"📸 実行結果サマリー")
        print(f"{'='*50}")
        print(f"✅ 成功件数: {success_count}/{len(urls)}")
        print(f"📁 履歴保存先: {self.output_dir}")
        print(f"📁 次段の入力先: {self.final_dir}")
        print(f"{'='*50}")
        
        return results
    
    def _sanitize_filename(self, url):
        import re
        safe = re.sub(r'^https?://', '', url)
        safe = re.sub(r'[^a-zA-Z0-9]', '_', safe)
        safe = safe[:50]
        return safe


def main():
    print("="*60)
    print("📸 Screenshot Capture & Coordinate Adjustment Tool")
    print("="*60)
    
    if not TARGET_URLS:
        print("❌ TARGET_URLSが設定されていません")
        return
    
    capture = ScreenshotCapture()
    capture.capture_multiple(TARGET_URLS, WAIT_TIME)

if __name__ == "__main__":
    main()