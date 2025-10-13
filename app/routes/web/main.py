import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user, logout_user
from app.models import ReadingPlans, User
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.services.user_service import AuthService, UserUpdateService
from app.utils.utils import get_today

web_main = Blueprint('web_main', __name__, template_folder='template')

@web_main.route('/')
def check_session():
    if current_user.is_authenticated:
        return redirect(url_for("web_main.home")) # เปลี่ยนไปหน้าที่ใช้ได้
    
    return render_template('index.html')

@web_main.route('/home')
@login_required
def home():
    print(f"=" * 50)
    print(f"✅ /home route accessed")
    print(f"✅ Session data: {dict(session)}")
    print(f"✅ user_id in session: {session.get('user_id')}")
    print(f"=" * 50)
    return render_template('schedule.html')

@web_main.route('/feedback')
@login_required
def feedback():
    return render_template('home.html')

@web_main.route('/add')
@login_required
def add():
    return render_template('add.html')

@web_main.route('/stat')
@login_required
def stat():
    return render_template('stat.html')

@web_main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@web_main.route('/forgotpassword')
def forgotpassword(): 
    return render_template('forgotpassword.html')

@web_main.route('/register')
def register(): 
    return render_template('register.html')

@web_main.route('/login')
def login_page():  
    return render_template('login.html')

@web_main.route('/logout')
def logout():
    """
    ฟังก์ชันสำหรับ logout ผู้ใช้
    - logout session ปัจจุบันและ redirect ไปหน้า login
    """
    logout_user()
    flash('just logout')

    return redirect(url_for('web_main.check_session'))

@web_main.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    ฟังก์ชันสำหรับ reset password
    - ตรวจสอบ token ว่ายังใช้ได้หรือไม่
    - ถ้า token หมดอายุหรือไม่ถูกต้องจะ redirect ไปหน้า login
    - ถ้า method เป็น POST จะเปลี่ยนรหัสผ่านใหม่และ redirect ไปหน้า login
    - ถ้า method เป็น GET จะแสดงหน้า reset password
    """
    user = AuthService.verify_reset_token(token)
    if not user:
        flash('this link is expired')
        return redirect(url_for('web_main.forgotpassword'))
    
    if request.method == 'POST':
        new_password = request.form['new-password']
        # เปลี่ยนรหัสผ่านใหม่และบันทึกลงฐานข้อมูล
        AuthService.set_password(user, new_password, persist=True)
        flash('password reset complete')
        return redirect(url_for('web_main.login_page'))
    
    return render_template('resetpassword.html')
