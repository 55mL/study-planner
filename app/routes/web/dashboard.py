from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import ReadingPlans
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserUpdateService
from utils import get_today

web_dashboard = Blueprint('web_dashboard', __name__, template_folder='templates') # ชี้ไปที่โฟลเดอร์ templates ใน web

@web_dashboard.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set_daily_read_hours':
            daily_hours = float(request.form['daily_read_hours'])
            UserUpdateService.set_daily_read_hours(current_user, daily_hours)
            flash('Updated daily reading hours')
            return redirect(url_for('web_dashboard.dashboard'))
        elif action == 'add_plan':
            try:
                UserUpdateService.add_plan(
                    current_user,
                    exam_name=request.form['exam_name'],
                    exam_date=request.form['exam_date'],
                    level=int(request.form['level'])
                )
                flash('Added reading plan')
            except ValueError as e:
                flash(str(e))
            return redirect(url_for('web_dashboard.dashboard'))
    pending_count = len(Feedback.get_pending_feedback(current_user))
    plans = ReadingPlans.query.filter_by(user_id=current_user.id).all()
    slots = ScheduleService.calculate_slots(current_user, persist=False)
    return render_template('dashboard.html', username=current_user.username, plans=plans, slots=slots, pending_count=pending_count)

@web_dashboard.route('/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    plan = ReadingPlans.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    UserUpdateService.delete_plan(current_user, plan)
    flash('Deleted reading plan')
    return redirect(url_for('web_dashboard.dashboard'))

@web_dashboard.route('/simulate_day/<days>')
@login_required
def simulate_day(days):
    from datetime import date, timedelta
    try:
        days = int(days)
    except ValueError:
        flash('ค่า days ต้องเป็นตัวเลข')
        return redirect(url_for('web_dashboard.dashboard'))
    if 'simulated_date' in session:
        base_date = date.fromisoformat(session['simulated_date'])
    else:
        base_date = date.today()
    simulated = base_date + timedelta(days=days)
    session['simulated_date'] = simulated.isoformat()
    flash(f'จำลองวันเป็น {simulated}')
    return redirect(url_for('web_dashboard.dashboard'))

@web_dashboard.route('/clear_simulation')
@login_required
def clear_simulation():
    session.pop('simulated_date', None)
    flash('กลับมาใช้วันจริงแล้ว')
    return redirect(url_for('web_dashboard.dashboard'))
