# notification\scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
import requests, pytz
from datetime import datetime
from email_service import send_email
import logging

API_BASE = "https://study-planner-gv2l.onrender.com"  # เรียก core API
BANGKOK_TZ = pytz.timezone("Asia/Bangkok")

def fetch_users():
    try:
        r = requests.get(f"{API_BASE}/api/users/with-email-notifications", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return []

def fetch_summary(user_id, date_str):
    try:
        r = requests.get(f"{API_BASE}/api/study/daily-summary",
                         params={"user_id": user_id, "date": date_str}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.error(f"Error fetching summary for user {user_id}: {e}")
        return {"total_hours": 0, "subjects": []}

def process_user(user):
    now_th = datetime.now(BANGKOK_TZ)
    date_local = now_th.date().isoformat()

    summary = fetch_summary(user["id"], date_local)
    if summary["total_hours"] == 0:
        return False

    # ✅ HTML Template
    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color:#2c3e50;">📚 สรุปการอ่านประจำวันที่ {date_local}</h2>
        <p><b>รวมเวลาที่อ่าน:</b> {summary['total_hours']} ชั่วโมง</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; margin-top:10px;">
          <tr style="background-color:#f2f2f2;">
            <th>วิชา</th>
            <th>ชั่วโมง</th>
          </tr>
          {''.join(f"<tr><td>{s['name']}</td><td>{s['hours']}</td></tr>" for s in summary['subjects'])}
        </table>
        <p style="margin-top:20px;">สู้ ๆ นะ {user['username']} ✨</p>
      </body>
    </html>
    """

    send_email(user["email"], "สรุปการอ่านหนังสือวันนี้", body_html)
    return True


def batch_job():
    users = fetch_users()
    now_th = datetime.now(BANGKOK_TZ)   # เวลาไทย
    date_local = now_th.date().isoformat()

    for u in users:
        summary = fetch_summary(u["id"], date_local)
        if summary["total_hours"] == 0:
            continue

        body = f"สรุปการอ่าน {date_local}\nรวม {summary['total_hours']} ชั่วโมง"
        send_email(u["email"], "สรุปการอ่านหนังสือวันนี้", body)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(batch_job, "cron", hour=0, minute=1)  # รันทุกวัน 00:01 เวลาไทย
    scheduler.start()