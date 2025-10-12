# app/notification/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz, logging
from app.models import User
from app.routes.api.study import get_daily_summary
from app.notification.email_service import send_email

BANGKOK_TZ = pytz.timezone("Asia/Bangkok")

def process_user(user, date_local):
    try:
        summary = get_daily_summary(user.id, date_local)
        if summary["total_hours"] == 0:
            return False

        body_html = f"""
        <html>
          <body>
            <h2>📚 สรุปการอ่าน {date_local}</h2>
            <p>รวม {summary['total_hours']} ชั่วโมง</p>
            <ul>
              {''.join(f"<li>{s['name']}: {s['hours']} ชั่วโมง</li>" for s in summary['subjects'])}
            </ul>
          </body>
        </html>
        """
        send_email(user.email, "สรุปการอ่านหนังสือวันนี้", body_html)
        return True
    except Exception as e:
        logging.error(f"Error processing user {user.id}: {e}")
        return False

def batch_job():
    users = User.query.filter_by(email_notifications=True).all()
    now_th = datetime.now(BANGKOK_TZ).date()
    for u in users:
        process_user(u, now_th)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(batch_job, "cron", hour=0, minute=1)  # รันทุกวัน 00:01 เวลาไทย
    scheduler.start()