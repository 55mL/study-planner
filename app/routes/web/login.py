import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models import User
from app.services.user_service import AuthService
from app import db

web_login = Blueprint('web_login', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend ใน web


@web_login.route('/')
def check_session():
    """
    ตรวจสอบ session ของผู้ใช้ ถ้า login แล้วให้ไปหน้า dashboard ถ้ายังไม่ login ให้ไปหน้า login
    """
    if current_user.is_authenticated:
        if os.environ.get("ENABLE_DEMO", "0") == "1":
            return redirect(url_for("web_dashboard.dashboard"))
        
        return redirect(url_for("web_main.home")) # เปลี่ยนไปหน้าที่ใช้ได้
    
    return redirect(url_for("web_login.login"))


@web_login.route('/login', methods=['GET', 'POST'])
def login():
    """
    ฟังก์ชันสำหรับ login ผู้ใช้
    - ถ้า method เป็น POST จะตรวจสอบ username และ password
    - ถ้าถูกต้องจะ login และไปหน้า dashboard
    - ถ้าผิดจะแสดงข้อความ error
    - ถ้า method เป็น GET จะแสดงหน้า login
    """
    if request.method == 'POST':
        username = request.form['username_login']
        password = request.form['password_login']
        user = User.query.filter_by(username=username).first()
        # ตรวจสอบว่ามี user และรหัสผ่านถูกต้องหรือไม่
        if user and AuthService.check_password(user, password):
            login_user(user)
            if os.environ.get("ENABLE_DEMO", "0") == "1":
                return redirect(url_for("web_dashboard.dashboard"))
            
            return redirect(url_for("web_main.home")) # เปลี่ยนไปหน้าที่ใช้ได้
        else:
            flash('incorrect username or password')

    return render_template('login.html')


@web_login.route('/register', methods=['GET', 'POST'])
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


@web_login.route('/logout')
def logout():
    """
    ฟังก์ชันสำหรับ logout ผู้ใช้
    - logout session ปัจจุบันและ redirect ไปหน้า login
    """
    logout_user()
    flash('just logout')

    return redirect(url_for('web_login.login'))
