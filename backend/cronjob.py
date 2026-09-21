import asyncio
import datetime
import os
import sys

# Thêm đường dẫn tới folder scraper
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraper"))

from scrape import main

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "scraper", "logs", "cronjob.log")

def log(message: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {message}\n")

def my_task():
    log("Bắt đầu cào data...")
    try:
        asyncio.run(main())
        log("Cào data thành công!")
    except Exception as e:
        log(f"Lỗi khi cào data: {e}")