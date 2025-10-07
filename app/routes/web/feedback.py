# web/feedback.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import DailyAllocations
from app.services.feedback_service import Feedback

web_feedback = Blueprint('web_feedback', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend ใน web)

@web_feedback.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        alloc_id = request.form.get('alloc_id')
        feedback_type = request.form.get('feedback_type')
        alloc = DailyAllocations.query.get_or_404(alloc_id)
        Feedback.submit_feedback(current_user, alloc, feedback_type)
        flash(f'บันทึกฟีดแบค {feedback_type} สำหรับ {alloc.exam_name_snapshot} วันที่ {alloc.date}')
        return redirect(url_for('web_feedback.feedback'))
    alloc = Feedback.get_next_feedback(current_user)
    if not alloc:
        flash('คุณตอบฟีดแบคครบทุกวันแล้ว 🎉')
        return render_template('feedback_done.html')
    return render_template('feedback.html', alloc=alloc)
