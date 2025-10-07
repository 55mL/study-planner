from flask import Blueprint, request, jsonify, session
from app.models import User, DailyAllocations
from app.services.feedback_service import Feedback

feedback_api = Blueprint('feedback_api', __name__, url_prefix='/api/feedback')

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@feedback_api.route('/pending', methods=['GET'])
def pending_feedback():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    pending = Feedback.get_pending_feedback(user)
    return jsonify([
        {
            'alloc_id': alloc.id,
            'date': alloc.date.isoformat(),
            'exam': alloc.plan.exam_name if alloc.plan else None,
            'slots': alloc.slots
        } for alloc in pending
    ])

@feedback_api.route('', methods=['POST'])
def submit_feedback():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    alloc_id = data.get('alloc_id')
    feedback_type = data.get('feedback_type')
    alloc = DailyAllocations.query.get(alloc_id)
    if not alloc or alloc.user_id != user.id:
        return jsonify({'error': 'Invalid allocation'}), 400
    Feedback.submit_feedback(user, alloc, feedback_type)
    return jsonify({'message': 'Feedback submitted'})