from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, request, jsonify, session
from app.models import User
from app import db
from app.services.user_service import AuthService, UserUpdateService

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
    updated = {}
    errors = {}

    # ✅ เปลี่ยน username
    if "new_username" in data:
        try:
            UserUpdateService.set_username(user, data["new_username"])
            updated["username"] = user.username
        except ValueError:
            errors["new_username"] = "username นี้ถูกใช้แล้ว"

    # ✅ เปลี่ยน password
    if "old_password" in data and "new_password" in data:
        try:
            UserUpdateService.set_password(user, data["old_password"], data["new_password"])
            updated["password"] = "updated"
        except KeyError:
            errors["password"] = "กรุณาระบุรหัสผ่านเก่าและใหม่"
        except UnicodeError:
            errors["password"] = "รหัสผ่านเก่าไม่ถูกต้อง"

    # ✅ เปลี่ยน daily_read_hours
    if "daily_read_hours" in data:
        try:
            UserUpdateService.set_daily_read_hours(user, data["daily_read_hours"])
            updated["daily_read_hours"] = user.daily_read_hours
        except ValueError:
            errors["password"] = "daily_read_hours ต้องเป็นตัวเลขระหว่าง 0-24"

    # ✅ email_notifications
    if "email_notifications" in data:
        try:
            UserUpdateService.set_email_notifications(user, data["email_notifications"])
            updated["email_notifications"] = user.email_notifications
        except Exception as e:
            errors["email_notifications"] = str(e)
    
    return jsonify({
        "message": "Settings processed",
        "updated": updated,
        "errors": errors
    }), 200


@user_api.route("/change-daily_read_hours", methods=["PUT"])
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
        UserUpdateService.set_daily_read_hours(user, new_hours)
    except ValueError:
        return jsonify({"error": "daily_read_hours ต้องเป็นตัวเลข"}), 400

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

    UserUpdateService.set_username(user, new_username)

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

    try:
        UserUpdateService.set_password(user, new_password, old_password)
    except KeyError:
        return jsonify({"error": "กรุณาระบุรหัสผ่านเก่าและใหม่"}), 400
    except UnicodeError:
        return jsonify({"error": "รหัสผ่านเก่าไม่ถูกต้อง"}), 400

    return jsonify({"message": "เปลี่ยนรหัสผ่านสำเร็จ"}), 200


# ✅ เปลี่ยน email_notifications
@user_api.route("/change-email_notifications", methods=["PUT"])
def change_email_notifications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    email_notifications = data.get("email_notifications")
    try:
        UserUpdateService.set_email_notifications(user, email_notifications)
    except ValueError:
        return jsonify({"error": "email_notifications ต้องเป็น true/false"}), 400

    return jsonify({"message": "เปลี่ยน email_notifications สำเร็จ"}), 200


# get email setting
@user_api.route("/with-email-notifications", methods=["GET"])
def users_with_email_notifications():
    users = User.query.filter_by(email_notifications=True).all()
    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "timezone": u.timezone or "UTC",
            "username": u.username
        } for u in users
    ])
