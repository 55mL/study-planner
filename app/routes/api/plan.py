from flask import Blueprint, request, jsonify, session
from app.models import ReadingPlans, User
from app.services.user_service import UserUpdateService
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.utils.utils import get_today
from app import db

plan_api = Blueprint('plan_api', __name__, url_prefix='/api/plans')

def get_current_user():
    """ดึง user จาก session"""
    user_id = session.get('_user_id')
    if not user_id:
        return None
    return User.query.get(int(user_id))


@plan_api.route('', methods=['GET'])
def get_plans():
    """
    ดึงข้อมูลแผนการอ่านทั้งหมดของ user ปัจจุบัน
    - ตรวจสอบ session ว่ามี user หรือไม่
    - ลบแผนที่หมดอายุออก (cleanup)
    - คืนข้อมูล username, รายการแผน, จำนวน feedback ที่ยังไม่ได้ตอบ, และ slots สำหรับตารางอ่าน
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # ตรวจสอบและลบแผนที่หมดอายุ
    today = get_today()
    if not user.last_cleanup_date or user.last_cleanup_date < today:
        UserUpdateService.cleanup_expired_plans(user)

    # ดึงข้อมูลแผน, feedback, slots
    plans = ReadingPlans.query.filter_by(user_id=user.id).all()
    pending_count = len(Feedback.get_pending_feedback(user))
    slots = ScheduleService.calculate_slots(user, persist=False)

    # คืนข้อมูลทั้งหมดในรูปแบบ JSON
    return jsonify({
        'username': user.username,
        'plans': [{
            'id': plan.id,
            'exam_name': plan.exam_name,
            'exam_date': plan.exam_date.isoformat(),
            'level': plan.level
        } for plan in plans],
        'pending_count': pending_count,
        'slots': slots
    })


@plan_api.route('/daily-hours', methods=['POST'])
def set_daily_hours():
    """
    ตั้งค่าชั่วโมงอ่านหนังสือต่อวันของ user
    - ต้อง login ก่อน
    - รับ daily_read_hours (float) จาก request body
    - อัปเดตข้อมูลในฐานข้อมูล
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    try:
        daily_hours = float(data['daily_read_hours'])
        # อัปเดตชั่วโมงอ่านต่อวันในฐานข้อมูล
        UserUpdateService.set_daily_read_hours(user, daily_hours)
        return jsonify({'message': 'Updated daily reading hours'})
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400


@plan_api.route('', methods=['POST'])
def add_plan():
    """
    เพิ่มแผนการอ่านใหม่ให้ user ปัจจุบัน
    - ต้อง login ก่อน
    - รับ exam_name, exam_date, level จาก request body
    - คืน plan_id ที่เพิ่มสำเร็จ
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    try:
        # เพิ่มแผนใหม่และ commit ลงฐานข้อมูล
        plan = UserUpdateService.add_plan(
            user,
            exam_name=data['exam_name'],
            exam_date=data['exam_date'],
            level=int(data['level'])
        )
        db.session.commit()
        return jsonify({'message': 'Plan added', 'plan_id': plan.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plan_api.route('/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """
    ลบแผนการอ่านตาม plan_id ของ user ปัจจุบัน
    - ต้อง login ก่อน
    - ถ้าไม่เจอแผนจะคืน error
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # ตรวจสอบว่าแผนนี้เป็นของ user จริงไหม
    plan = ReadingPlans.query.filter_by(id=plan_id, user_id=user.id).first()

    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    
    # ลบแผนและ commit
    UserUpdateService.delete_plan(user, plan)
    db.session.commit()

    return jsonify({'message': 'Plan deleted'})