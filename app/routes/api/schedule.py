from flask import Blueprint, jsonify, session
from app.models import User, DailyAllocations, ReadingPlans
from app.utils.utils import get_today
import datetime

schedule_api = Blueprint('schedule_api', __name__, url_prefix='/api')

def get_current_user():
    user_id = session.get('_user_id')
    if not user_id:
        return None
    return User.query.get(int(user_id))

@schedule_api.route('/schedule', methods=['GET'])
def get_schedule():
    """ดึงข้อมูลตารางการอ่านของ user ปัจจุบัน"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    simulated_today = get_today()

    # ดึง allocations และ plans
    allocations = (DailyAllocations.query
                   .filter_by(user_id=user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())
    plans = ReadingPlans.query.filter_by(user_id=user.id).all()

    # สร้าง map ของวันสอบ (exam_name -> exam_date) และ map ของ plan โดยชื่อเพื่อดึง level
    exam_dates_map = {plan.exam_name: plan.exam_date for plan in plans}
    plan_by_name = {plan.exam_name: plan for plan in plans}

    events = []
    exam_dates_added = {}

    print(f"\n{'='*60}")
    print(f"📊 Processing allocations...")

    # 1. เพิ่ม allocations (วันอ่าน)
    for alloc in allocations:
        date_str = alloc.date.strftime('%Y-%m-%d')
        exam_date = exam_dates_map.get(alloc.exam_name_snapshot)

        if exam_date:
            # ถ้าวันนี้ >= วันสอบ ให้ข้ามไป
            if alloc.date >= exam_date:
                print(f"⚠️ SKIP: {date_str} >= exam date {exam_date.strftime('%Y-%m-%d')}")
                continue

            # หาค่า level จาก plan
            plan = plan_by_name.get(alloc.exam_name_snapshot)
            level_value = plan.level if plan else None

            print(f"✅ ADD study day: {date_str} ({alloc.exam_name_snapshot}, {alloc.slots} ชม., level={level_value}, id={alloc.id})")

            events.append({
                'id': alloc.id,  # ✅ เพิ่ม id
                'alloc_id': alloc.id,  # ✅ เพิ่ม alloc_id
                'day': date_str,
                'exam': alloc.exam_name_snapshot,
                'slots': alloc.slots,
                'is_exam_day': False,
                'feedback_done': alloc.feedback_done,
                'event_type': 'study',
                'level': level_value
            })

    # 2. เพิ่มวันสอบ (จาก plans)
    for plan in plans:
        if plan.exam_date:
            exam_date_str = plan.exam_date.strftime('%Y-%m-%d')

            if exam_date_str not in exam_dates_added:
                exam_dates_added[exam_date_str] = []

            if plan.exam_name not in exam_dates_added[exam_date_str]:
                exam_dates_added[exam_date_str].append(plan.exam_name)

                print(f"✅ ADD exam day: {exam_date_str} ({plan.exam_name}, level={plan.level})")

                events.append({
                    'id': None,  # ✅ วันสอบไม่มี allocation id
                    'alloc_id': None,  # ✅ วันสอบไม่มี allocation id
                    'day': exam_date_str,
                    'exam': plan.exam_name,
                    'slots': 0,
                    'is_exam_day': True,
                    'feedback_done': False,
                    'event_type': 'exam',
                    'level': plan.level
                })

    print(f"📤 Total events: {len(events)}")
    print(f"{'='*60}\n")

    return jsonify({
        'simulated_today': simulated_today.strftime('%Y-%m-%d'),
        'events': events
    })