import os
from flask import Blueprint, render_template, url_for, flash, redirect, request
from app.models import User
from app.services.user_service import AuthService

web_password = Blueprint('web_password', __name__, template_folder='demo_backend') # ชี้ไปที่โฟลเดอร์ demo_backend ใน web


@web_password.route('/forgot', methods=['GET', 'POST'])
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
            reset_url = url_for('web_password.reset_password', token=token, _external=True)
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
            
    return render_template('forgot.html')


@web_password.route('/reset/<token>', methods=['GET', 'POST'])
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
        return redirect(url_for('web_login.login'))
    
    if request.method == 'POST':
        new_password = request.form['password']
        # เปลี่ยนรหัสผ่านใหม่และบันทึกลงฐานข้อมูล
        AuthService.set_password(user, new_password, persist=True)
        flash('password reset complete')
        return redirect(url_for('web_login.login'))
    
    return render_template('reset.html')
