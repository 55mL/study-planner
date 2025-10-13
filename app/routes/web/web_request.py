import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user, login_user
from sqlalchemy import or_
from app.models import ReadingPlans, User
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.services.user_service import AuthService, UserUpdateService
from app.utils.utils import get_today
from app.extensions import db

web_req = Blueprint('web_req', __name__, url_prefix='/req', template_folder='template')

@web_req.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    """
    ฟังก์ชันสำหรับขอ reset password
    - ถ้า method เป็น POST จะรับ email และส่งลิงก์ reset password ไปยัง email ถ้ามีในระบบ
    - ถ้าไม่พบ email จะแจ้งเตือนว่าไม่มีในระบบ
    - ถ้า method เป็น GET จะแสดงหน้า forgot password
    """
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            # สร้าง token สำหรับ reset password และส่งอีเมล
            token = AuthService.generate_reset_token(user, user.email)
            reset_url = url_for('web_main.reset_password', token=token, _external=True)
            from flask_mail import Message
            from app import mail
            msg = Message('Password Reset Request',
                          sender=os.environ.get('SENDER_MAIL', 'idk-bruh'),
                          recipients=[user.email])
            msg.body = f'click for reset password: {reset_url}'
            mail.send(msg)
            flash('email sent, please check on checkbox')
        else:
            flash('dont have email in system')
            
    return render_template('forgotpassword.html')

@web_req.route('/login', methods=['GET', 'POST'])
def login():
    """
    ฟังก์ชันสำหรับ login ผู้ใช้
    - ถ้า method เป็น POST จะตรวจสอบ username และ password
    - ถ้าถูกต้องจะ login และไปหน้า dashboard
    - ถ้าผิดจะแสดงข้อความ error
    - ถ้า method เป็น GET จะแสดงหน้า login
    """
    if request.method == 'POST':
        username_or_email = request.form['username_login']
        password = request.form['password_login']

        # หา user โดย username หรือ email
        users = User.query.filter(
            or_(User.username == username_or_email,
                User.email == username_or_email)
        ).all()
        
        if len(users) > 1:
            flash('Duplicate username found, please use email to login')
            return render_template('login.html')

        user = users[0] if users else None

        # ตรวจสอบว่ามี user และรหัสผ่านถูกต้องหรือไม่
        if user and AuthService.check_password(user, password):
            login_user(user)
            if os.environ.get("ENABLE_DEMO", "0") == "1":
                return redirect(url_for("web_dashboard.dashboard"))
            
            return redirect(url_for("web_main.home")) # เปลี่ยนไปหน้าที่ใช้ได้
        else:
            flash('incorrect username or password')

    return

@web_req.route('/register', methods=['GET', 'POST'])
def register():
    """
    ฟังก์ชันสำหรับสมัครสมาชิกใหม่
    - ถ้า method เป็น POST จะรับข้อมูลจากฟอร์มและสร้าง user ใหม่
    - ถ้าสมัครสำเร็จจะ redirect ไปหน้า login
    - ถ้ามี error จะ rollback และแสดง error
    - ถ้า method เป็น GET จะแสดงหน้า register
    """
    if request.method == 'POST':
        email = request.form['email_register']
        username = request.form['username_register']
        password = request.form['password_register']
        new_user = User(username=username, email=email)
        AuthService.set_password(new_user, password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('register complete! please login')
            return redirect(url_for('web_login.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}')
            
    return render_template('register.html')