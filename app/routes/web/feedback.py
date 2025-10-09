# web/feedback.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import DailyAllocations
from app.services.feedback_service import Feedback

web_feedback = Blueprint('web_feedback', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend ใน web)

@web_feedback.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    """
    แสดงหน้า feedback สำหรับผู้ใช้
    - GET: แสดงฟอร์ม feedback สำหรับ allocation ถัดไป
    - POST: รับค่าฟีดแบคและบันทึกลงฐานข้อมูล
    """
    if request.method == 'POST':
        # รับค่าฟีดแบคจากฟอร์ม
        alloc_id = request.form.get('alloc_id')
        feedback_type = request.form.get('feedback_type')
        # ดึง allocation ที่ต้องการ feedback ถ้าไม่เจอจะ 404
        alloc = DailyAllocations.query.get_or_404(alloc_id)
        # บันทึก feedback ลงฐานข้อมูล
        Feedback.submit_feedback(current_user, alloc, feedback_type)
        flash(f'บันทึกฟีดแบค {feedback_type} สำหรับ {alloc.exam_name_snapshot} วันที่ {alloc.date}')
        return redirect(url_for('web_feedback.feedback'))
    # ดึง allocation ถัดไปที่ต้อง feedback
    alloc = Feedback.get_next_feedback(current_user)
    if not alloc:
        flash('คุณตอบฟีดแบคครบทุกวันแล้ว 🎉')
        return render_template('feedback_done.html')
    
    return render_template('feedback.html', alloc=alloc)
