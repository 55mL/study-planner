# web/schedule.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import DailyAllocations
from app.services.schedule_service import ScheduleService
from utils import get_today

web_schedule = Blueprint('web_schedule', __name__, template_folder='templates') # ชี้ไปที่โฟลเดอร์ templates ใน web

@web_schedule.route('/study_schedule')
@login_required
def study_schedule():
    simulated_today = get_today()
    allocations = (DailyAllocations.query
                   .filter_by(user_id=current_user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())
    events = []
    for alloc in allocations:
        if not alloc.plan:
            continue
        events.append({
            'day': alloc.date,
            'exam': alloc.plan.exam_name,
            'slots': alloc.slots,
            'is_exam_day': (alloc.date == alloc.plan.exam_date),
            'feedback_done': alloc.feedback_done
        })
    return render_template('study_schedule.html', events=events, simulated_today=simulated_today)
