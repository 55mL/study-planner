# app/notification/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz, logging
from app.notification.email_service import send_email

BANGKOK_TZ = pytz.timezone("Asia/Bangkok")


def process_user(user, date_local):
    """สร้างสรุปการอ่านของ user และส่งอีเมล"""
    from app.routes.api.study import get_daily_summary 
    try:
        summary = get_daily_summary(user.id, date_local)
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
            <p style="margin-top:20px;">
                👉 ดูรายละเอียดเพิ่มเติมได้ที่ 
                <a href="https://study-planner-gv2l.onrender.com" 
                    style="color:#1a73e8; text-decoration:none;">
                    คลิกที่นี่
                </a>
            </p>
            <p style="margin-top:20px;">สู้ ๆ นะ {user.username} ✨</p>
          </body>
        </html>
        """

        send_email(user.email, "สรุปการอ่านหนังสือวันนี้", body_html)
        return True
    except Exception as e:
        logging.error(f"Error processing user {getattr(user, 'id', '?')}: {e}")
        return False


def batch_job():
    """ดึง users ที่เปิด email_notifications แล้วส่งสรุปให้ทุกคน"""
    from app.models import User  # 👈 import ข้างในเพื่อเลี่ยง circular import

    now_th = datetime.now(BANGKOK_TZ).date()
    users = User.query.filter_by(email_notifications=True).all()

    for u in users:
        process_user(u, now_th)


def start_scheduler():
    """เริ่ม APScheduler ให้รัน batch_job ทุกวันเวลา 00:01 (เวลาไทย)"""
    scheduler = BackgroundScheduler(timezone="Asia/Bangkok")
    scheduler.add_job(batch_job, "cron", hour=0, minute=1)
    scheduler.start()