# notification\scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
import requests, pytz
from datetime import datetime
from email_service import send_email

API_BASE = "http://core-api:5000"  # เรียก core API

def fetch_users():
    r = requests.get(f"{API_BASE}/api/users/with-email-notifications")
    return r.json()

def fetch_summary(user_id, date_str):
    r = requests.get(f"{API_BASE}/api/study-summary",
                     params={"user_id": user_id, "date": date_str})
    return r.json()

def process_user(user):
    tz = pytz.timezone(user["timezone"])
    now_local = datetime.now(pytz.utc).astimezone(tz)
    date_local = now_local.date().isoformat()

    summary = fetch_summary(user["id"], date_local)
    if summary["total_hours"] == 0:
        return

    body = f"สรุปการอ่าน {date_local}\nรวม {summary['total_hours']} ชั่วโมง"
    send_email(user["email"], "สรุปการอ่านหนังสือวันนี้", body)

def batch_job():
    users = fetch_users()
    for u in users:
        tz = pytz.timezone(u["timezone"])
        local_now = datetime.now(pytz.utc).astimezone(tz)
        if local_now.hour == 0 and local_now.minute < 10:
            process_user(u)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(batch_job, "interval", minutes=5)
    scheduler.start()