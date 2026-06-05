
open .
右クリック
圧縮

pip install selenium ollama webdriver-manager
pip install pydantic google-genai crawl4ai feedparser
crawl4ai-setup


python3 -m venv venv
source venv/bin/activate

#!/bin/bash

self_made LLM agentsの全体像 2026/06/05

urlのsnapshotを撮りサイトの内容を解釈する
python3 screen_capture.py
python3 image_describer.py

手動で準備した天気図を解釈する
python3 weather_image_describer.py

手動で準備した画像をテーブルにする
python3 table_analyzer.py

kaggle順位画像をテーブルにする
python3 kaggle_image_download.py 
python3 table_analyzer.py

urlのscrapingを行いコンテンツをまとめる
python3 web_scraper.py
python3 text_interpreter_j.py

urlの競技プログラミング問題を読み取り解答を作る
python3 web_scraper.py
python3 code_generator.py

snapshotで天気図を入手しそれを天気図を解釈する
python3 weather_image_download.py 
python3 weather_image_describer.py

youtubeの文字起こしをおこない解釈する
python3 youtube_mp3.py 
python3 mp3_text.py　
python3 text_interpreter_j.py

screenshotsを閲覧する
screenshots_viewer.html
