from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import ReadingPlans
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserUpdateService
from app.utils.utils import get_today

web_dashboard = Blueprint('web_dashboard', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend

@web_dashboard.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """
    แสดงหน้า dashboard หลักของผู้ใช้
    - GET: แสดงแผนการอ่าน, ตาราง slot, จำนวน feedback ที่ยังไม่ได้ตอบ
    - POST: รับ action จากฟอร์ม (เพิ่มแผน/ตั้งค่าชั่วโมงอ่าน)
    """
    today = get_today()
    # ลบแผนที่หมดอายุออก (cleanup)
    if not current_user.last_cleanup_date or current_user.last_cleanup_date < today:
        UserUpdateService.cleanup_expired_plans(current_user)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'set_daily_read_hours':
            # ตั้งค่าชั่วโมงอ่านต่อวันใหม่
            daily_hours = float(request.form['daily_read_hours'])
            UserUpdateService.set_daily_read_hours(current_user, daily_hours)
            flash('Updated daily reading hours')
            return redirect(url_for('web_dashboard.dashboard'))
        elif action == 'add_plan':
            # เพิ่มแผนการอ่านใหม่
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
    # จำนวน feedback ที่ยังไม่ได้ตอบ
    pending_count = len(Feedback.get_pending_feedback(current_user))
    # รายการแผนการอ่านทั้งหมด
    plans = ReadingPlans.query.filter_by(user_id=current_user.id).all()
    # ตาราง slot สำหรับแสดงผล
    slots = ScheduleService.calculate_slots(current_user, persist=False)

    return render_template('dashboard.html', username=current_user.username, plans=plans, slots=slots, pending_count=pending_count)


@web_dashboard.route('/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """
    ลบแผนการอ่านตาม plan_id ของ user ปัจจุบัน
    """
    # ดึงแผนที่ต้องการลบ ถ้าไม่เจอจะ 404
    plan = ReadingPlans.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    UserUpdateService.delete_plan(current_user, plan)
    flash('Deleted reading plan')

    return redirect(url_for('web_dashboard.dashboard'))


@web_dashboard.route('/simulate_day/<days>')
@login_required
def simulate_day(days):
    """
    จำลองวันในระบบ (เช่น ข้ามไปอนาคต N วัน)
    - รับจำนวนวันที่ต้องการข้ามจาก url param
    - เก็บวันที่จำลองไว้ใน session
    """
    from datetime import date, timedelta
    try:
        days = int(days)
    except ValueError:
        flash('ค่า days ต้องเป็นตัวเลข')
        return redirect(url_for('web_dashboard.dashboard'))
    
    # ถ้ามีวันจำลองใน session ให้ใช้เป็น base date
    if 'simulated_date' in session:
        base_date = date.fromisoformat(session['simulated_date'])
    else:
        base_date = date.today()
    # คำนวณวันใหม่
    simulated = base_date + timedelta(days=days)
    session['simulated_date'] = simulated.isoformat()
    flash(f'จำลองวันเป็น {simulated}')

    return redirect(url_for('web_dashboard.dashboard'))


@web_dashboard.route('/clear_simulation')
@login_required
def clear_simulation():
    """
    ลบวันจำลอง กลับมาใช้วันจริง
    """
    session.pop('simulated_date', None)
    flash('กลับมาใช้วันจริงแล้ว')

    return redirect(url_for('web_dashboard.dashboard'))
