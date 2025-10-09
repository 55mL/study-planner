from flask import Blueprint, jsonify, session
from app.models import User, DailyAllocations, ReadingPlans
from app.services.schedule_service import ScheduleService
from app.utils.utils import get_today
import datetime

schedule_api = Blueprint('schedule_api', __name__, url_prefix='/api/schedule')

def get_current_user():
    """
    ดึง user ปัจจุบันจาก session (ใช้กับทุก endpoint ที่ต้อง login)
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@schedule_api.route('', methods=['GET'])
def get_schedule():
    """
    ดึงข้อมูลตารางการอ่านของ user ปัจจุบัน
    - ต้อง login ก่อน
    - คืน simulated_today (วันที่ปัจจุบัน) และ events (แต่ละวัน)
    - events: ข้อมูลแต่ละวัน เช่น วันที่, ชื่อสอบ, จำนวน slot, เป็นวันสอบไหม, feedback_done
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    # วันที่ปัจจุบัน (หรือวันที่จำลอง)
    simulated_today = get_today()

    # ดึง allocation (แต่ละวัน) ของ user ทั้งหมด เรียงตามวันที่
    allocations = (DailyAllocations.query
                   .filter_by(user_id=user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())

    events = []  # เก็บข้อมูลแต่ละวัน
    for alloc in allocations:
        # สร้าง dict สำหรับแต่ละวัน
        events.append({
            'day': alloc.date.isoformat(),
            'exam': alloc.exam_name_snapshot,
            'slots': alloc.slots,
            'is_exam_day': (
                alloc.plan is not None and 
                alloc.date + datetime.timedelta(days=1) == alloc.plan.exam_date  # วันก่อนสอบ
            ),
            'feedback_done': alloc.feedback_done
        })

    # คืนข้อมูลทั้งหมดในรูปแบบ JSON
    return jsonify({
        'simulated_today': simulated_today.isoformat(),
        'events': events
    })