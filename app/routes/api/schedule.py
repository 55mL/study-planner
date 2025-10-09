from flask import Blueprint, jsonify, session
from app.models import User, DailyAllocations, ReadingPlans
from app.services.schedule_service import ScheduleService
from app.utils.utils import get_today
import datetime

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
    
    simulated_today = get_today()
    allocations = (DailyAllocations.query
                   .filter_by(user_id=user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())
    
    events = []
    for alloc in allocations:
        events.append({
            'day': alloc.date.isoformat(),
            'exam': alloc.exam_name_snapshot,
            'slots': alloc.slots,
            'is_exam_day': (
                alloc.plan is not None and 
                alloc.date + datetime.timedelta(days=1) == alloc.plan.exam_date
            ),
            'feedback_done': alloc.feedback_done
        })
    
    return jsonify({
        'simulated_today': simulated_today.isoformat(),
        'events': events
    })