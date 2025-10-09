from flask import Blueprint, request, jsonify, session
from app.models import User, DailyAllocations
from app.services.feedback_service import Feedback

feedback_api = Blueprint('feedback_api', __name__, url_prefix='/api/feedback')

def get_current_user():
    """
    ดึง user ปัจจุบันจาก session (ใช้กับทุก endpoint ที่ต้อง login)
    """
    user_id = session.get('user_id')

    if not user_id:
        return None
    
    return User.query.get(user_id)


@feedback_api.route('/pending', methods=['GET'])
def pending_feedback():
    """
    ดึง feedback ที่ user ยังไม่ได้ตอบ (pending feedback)
    - ต้อง login ก่อน
    - คืนรายการ allocation ที่ต้อง feedback
    """
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    # ดึง allocation ที่ user ยังไม่ได้ตอบ feedback
    pending = Feedback.get_pending_feedback(user)

    return jsonify([
        {
            'alloc_id': alloc.id,
            'date': alloc.date.isoformat(),
            'exam': alloc.exam_name_snapshot if alloc.exam_name_snapshot else None,
            'slots': alloc.slots
        } for alloc in pending
    ])


@feedback_api.route('', methods=['POST'])
def submit_feedback():
    """
    ส่ง feedback สำหรับ allocation (วันที่อ่าน)
    - ต้อง login ก่อน
    - รับ alloc_id และ feedback_type จาก request body
    - ตรวจสอบว่า allocation เป็นของ user จริงไหม
    - บันทึก feedback
    """
    user = get_current_user()

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    alloc_id = data.get('alloc_id')
    feedback_type = data.get('feedback_type')
    # ตรวจสอบว่า allocation นี้เป็นของ user จริงไหม
    alloc = DailyAllocations.query.get(alloc_id)

    if not alloc or alloc.user_id != user.id:
        return jsonify({'error': 'Invalid allocation'}), 400
    # บันทึก feedback ลงฐานข้อมูล
    Feedback.submit_feedback(user, alloc, feedback_type)

    return jsonify({'message': 'Feedback submitted'})