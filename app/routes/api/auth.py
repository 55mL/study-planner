from flask import Blueprint, request, jsonify, session
from sqlalchemy import or_
from app.models import User
from app.services.user_service import AuthService
from app import db

auth_api = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_api.route('/register', methods=['POST'])
def register():
    """
    สมัครสมาชิกใหม่
    - รับ username, email, password จาก request body
    - ตรวจสอบซ้ำ ถ้ามี username หรือ email ในระบบจะ error
    - เพิ่ม user ใหม่ในฐานข้อมูล
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400
    
    # ตรวจสอบว่ามี username หรือ email ซ้ำในระบบหรือไม่
    if User.query.filter(User.email == email).first():
        return jsonify({'error': 'Username or email already exists'}), 400
    
    user = User(username=username, email=email)
    AuthService.set_password(user, password, persist=False)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Register complete'}), 201


@auth_api.route('/login', methods=['POST'])
def login():
    """
    เข้าสู่ระบบ
    - รับ username, password จาก request body
    - ตรวจสอบรหัสผ่าน ถ้าถูกต้องจะเก็บ user_id ใน session
    - คืน message success หรือ error
    """
    data = request.get_json()
    username_or_email = data.get('username')
    password = data.get('password')
    
    # หา user โดย username หรือ email
    users = User.query.filter(
        or_(User.username == username_or_email,
            User.email == username_or_email)
    ).all()
    
    if len(users) > 1:
        return jsonify({'error': 'Duplicate username found, please use email to login'}), 400

    user = users[0] if users else None

    # ตรวจสอบรหัสผ่าน ถ้าถูกต้องจะเก็บ user_id ใน session
    if user and AuthService.check_password(user, password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login success'}), 200
    
    return jsonify({'error': 'Incorrect username or password'}), 401


@auth_api.route('/logout', methods=['POST'])
def logout():
    """
    ออกจากระบบ (ลบ user_id ออกจาก session)
    """
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'}), 200


@auth_api.route('/forgot', methods=['POST'])
def forgot():
    """
    ขอ reset password (mock)
    - รับ email จาก request body
    - ถ้ามี user จะ generate token (mock ส่ง email)
    - คืน token กลับ (จริงๆ ต้องส่ง email)
    """
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()

    # ตรวจสอบว่ามี email นี้ในระบบหรือไม่
    if not user:
        return jsonify({'error': 'Email not found'}), 400
    
    # สร้าง token สำหรับ reset password (mock)
    token = AuthService.generate_reset_token(user)

    # TODO: send email with token (mock)
    return jsonify({'message': 'Reset email sent', 'token': token}), 200


@auth_api.route('/reset', methods=['POST'])
def reset():
    """
    reset password ด้วย token
    - รับ token กับ new_password จาก request body
    - ตรวจสอบ token ถ้าถูกต้องจะเปลี่ยนรหัสผ่าน user
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    user = AuthService.verify_reset_token(token)

    # ตรวจสอบ token ว่า valid หรือหมดอายุ
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400
    
    # เปลี่ยนรหัสผ่านใหม่
    AuthService.set_password(user, new_password, persist=True)

    return jsonify({'message': 'Password reset complete'}), 200