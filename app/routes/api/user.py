from flask import Blueprint, request, jsonify, session
from app.models import User
from app import db

user_api = Blueprint('user_api', __name__, url_prefix='/api/user')

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@user_api.route('/profile', methods=['GET'])
def profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'daily_read_hours': user.daily_read_hours
    })

@user_api.route('/settings', methods=['PUT'])
def update_settings():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    daily_read_hours = data.get('daily_read_hours')
    if daily_read_hours is not None:
        try:
            user.daily_read_hours = float(daily_read_hours)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return jsonify({'message': 'Settings updated'})