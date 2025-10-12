from flask import Blueprint, request, jsonify, session
from app.models import User, DailyAllocations
from app.services.feedback_service import Feedback

feedback_api = Blueprint('feedback_api', __name__, url_prefix='/api/feedback')

def get_current_user():
    """ดึง user จาก session"""
    user_id = session.get('_user_id')
    if not user_id:
        return None
    return User.query.get(int(user_id))


@feedback_api.route('/pending', methods=['GET'])
def pending_feedback():
    """
    ดึง feedback ที่ user ยังไม่ได้ตอบ
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pending = Feedback.get_pending_feedback(user)
    
    print(f"✅ Pending allocations for user {user.id}:")
    for alloc in pending:
        print(f"  - ID: {alloc.id}, Exam: {alloc.exam_name_snapshot}, Date: {alloc.date}")
    
    return jsonify([
        {
            'alloc_id': alloc.id,  # ✅ ใช้ alloc.id ไม่ใช่ alloc.alloc_id
            'date': alloc.date.isoformat(),
            'exam': alloc.exam_name_snapshot if alloc.exam_name_snapshot else 'Unknown',
            'slots': alloc.slots
        } for alloc in pending
    ])


@feedback_api.route('', methods=['POST'])
def submit_feedback():
    """
    ส่ง feedback สำหรับ allocation
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    alloc_id = data.get('alloc_id')
    feedback_type = data.get('feedback_type')
    
    print(f"📥 Received feedback: alloc_id={alloc_id}, type={feedback_type}")
    
    # ตรวจสอบว่า allocation เป็นของ user จริงไหม
    alloc = DailyAllocations.query.get(alloc_id)
    if not alloc or alloc.user_id != user.id:
        print(f"❌ Invalid allocation or wrong user")
        return jsonify({'error': 'Invalid allocation'}), 400
    
    # บันทึก feedback
    Feedback.submit_feedback(user, alloc, feedback_type)
    
    print(f"✅ Feedback submitted successfully")
    
    return jsonify({'message': 'Feedback submitted successfully'})