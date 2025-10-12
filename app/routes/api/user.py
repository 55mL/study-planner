from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, jsonify, session
from app.models import User
from app import db
from app.services.user_service import AuthService

user_api = Blueprint('user_api', __name__, url_prefix='/api/user')

def get_current_user():
    """
    ดึง user ปัจจุบันจาก session (ใช้กับทุก endpoint ที่ต้อง login)
    """
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    return User.query.get(user_id)

@user_api.route('/profile', methods=['GET'])
def profile():
    """
    ดึงข้อมูลโปรไฟล์ของ user ปัจจุบัน (ต้อง login)
    คืน id, username, email, daily_read_hours
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # คืนข้อมูลโปรไฟล์ user ปัจจุบัน
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'daily_read_hours': user.daily_read_hours
    })

@user_api.route('/settings', methods=['PUT'])
def update_settings():
    """
    อัปเดตการตั้งค่าของ user:
    - username
    - password (ต้องส่ง old_password และ new_password)
    - daily_read_hours
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # ✅ เปลี่ยน username
    new_username = data.get('username')
    if new_username:
        # ตรวจสอบว่า username ซ้ำหรือไม่
        if User.query.filter_by(username=new_username).first():
            return jsonify({'error': 'username นี้ถูกใช้แล้ว'}), 400
        user.username = new_username

    # ✅ เปลี่ยน password
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if old_password and new_password:
        if not check_password_hash(user.password, old_password):
            return jsonify({'error': 'รหัสผ่านเก่าไม่ถูกต้อง'}), 400
        user.password = generate_password_hash(new_password)

    # ✅ เปลี่ยน daily_read_hours
    daily_read_hours = data.get('daily_read_hours')
    if daily_read_hours is not None:
        try:
            hours = float(daily_read_hours)
            if hours < 0 or hours > 24:
                return jsonify({'error': 'daily_read_hours ต้องอยู่ระหว่าง 0-24'}), 400
            user.daily_read_hours = hours
        except ValueError:
            return jsonify({'error': 'daily_read_hours ต้องเป็นตัวเลข'}), 400

    # บันทึกการเปลี่ยนแปลง
    db.session.commit()

    return jsonify({
        'message': 'Settings updated',
        'username': user.username,
        'daily_read_hours': user.daily_read_hours
    }), 200



@user_api.route("/change-daily-read-hours", methods=["PUT"])
def change_daily_read_hours():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    new_hours = data.get("daily_read_hours")

    # ตรวจสอบว่ามีการส่งค่าเข้ามา
    if new_hours is None:
        return jsonify({"error": "กรุณาระบุ daily_read_hours"}), 400

    # ตรวจสอบว่าเป็นตัวเลขและไม่ติดลบ
    try:
        new_hours = float(new_hours)
        if new_hours < 0:
            return jsonify({"error": "daily_read_hours ต้องไม่ติดลบ"}), 400
    except ValueError:
        return jsonify({"error": "daily_read_hours ต้องเป็นตัวเลข"}), 400

    user.daily_read_hours = new_hours
    db.session.commit()

    return jsonify({
        "message": "อัปเดต daily_read_hours สำเร็จ",
        "daily_read_hours": user.daily_read_hours
    }), 200


# ✅ เปลี่ยน username
@user_api.route("/change-username", methods=["PUT"])
def change_username():

    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_username = data.get("username")

    if not new_username:
        return jsonify({"error": "กรุณาระบุ username ใหม่"}), 400

    # ตรวจสอบว่ามี username ซ้ำหรือไม่
    # if User.query.filter_by(username=new_username).first():
    #     return jsonify({"error": "username นี้ถูกใช้แล้ว"}), 400

    user.username = new_username
    db.session.commit()

    return jsonify({"message": "เปลี่ยน username สำเร็จ", "username": user.username}), 200


# ✅ เปลี่ยน password
@user_api.route("/change-password", methods=["PUT"])
def change_password():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "กรุณาระบุรหัสผ่านเก่าและใหม่"}), 400

    # ตรวจสอบรหัสผ่านเก่า
    if not check_password_hash(user.password, old_password):
        return jsonify({"error": "รหัสผ่านเก่าไม่ถูกต้อง"}), 400

    # เข้ารหัสรหัสผ่านใหม่
    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "เปลี่ยนรหัสผ่านสำเร็จ"}), 200
