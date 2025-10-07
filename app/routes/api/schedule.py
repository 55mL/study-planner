from flask import Blueprint, jsonify, session
from app.models import User, DailyAllocations, ReadingPlans
from app.services.schedule_service import ScheduleService

schedule_api = Blueprint('schedule_api', __name__, url_prefix='/api/schedule')

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@schedule_api.route('', methods=['GET'])
def get_schedule():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    allocations = DailyAllocations.query.join(ReadingPlans).filter(DailyAllocations.user_id == user.id).order_by(DailyAllocations.date.asc()).all()
    events = []
    for alloc in allocations:
        if not alloc.plan:
            continue
        events.append({
            'date': alloc.date.isoformat(),
            'exam': alloc.plan.exam_name,
            'slots': alloc.slots,
            'is_exam_day': (alloc.date == alloc.plan.exam_date),
            'feedback_done': alloc.feedback_done
        })
    return jsonify(events)