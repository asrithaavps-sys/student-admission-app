import schedule
import time
from scraper import run_scraper

FILE = "uploads/latest.xlsx"

def job():
    print("🔄 Updating admission data...")
    run_scraper(FILE)

schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)