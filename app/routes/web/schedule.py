# web/schedule.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
import datetime
from app.models import DailyAllocations
from app.services.schedule_service import ScheduleService
from app.utils.utils import get_today

web_schedule = Blueprint('web_schedule', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend ใน web


@web_schedule.route('/study_schedule')
@login_required
def study_schedule():
    """
    แสดงตารางเรียน (study schedule) ของผู้ใช้
    - ต้อง login ก่อนถึงจะเข้าหน้านี้ได้
    - ดึงข้อมูล DailyAllocations ของ user ปัจจุบัน
    - สร้าง list ของ events สำหรับแสดงผลใน template
    - ส่ง events และวันที่ปัจจุบัน (simulated_today) ไปยัง template
    """
    simulated_today = get_today()
    allocations = (DailyAllocations.query
                   .filter_by(user_id=current_user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())
    events = []
    for alloc in allocations:
        # ถ้า allocation ไม่มีแผน (plan) จะข้าม (แต่ปัจจุบันถูก comment ไว้)
        events.append({
            'day': alloc.date,
            'exam': alloc.exam_name_snapshot,
            'slots': alloc.slots,
            'is_exam_day': (
                alloc.plan is not None and 
                alloc.date + datetime.timedelta(days=1) == alloc.plan.exam_date
            ),
            'feedback_done': alloc.feedback_done
        })

    return render_template('study_schedule.html', events=events, simulated_today=simulated_today)


from datetime import timedelta
@web_schedule.app_template_filter('add_days')
def add_days(date_obj, days):
    """
    ฟิลเตอร์ Jinja2 สำหรับบวกจำนวนวันให้กับวันที่ (date_obj)
    ใช้ใน template เพื่อแสดงวันที่ที่เพิ่มขึ้น
    """
    return date_obj + timedelta(days=days)
