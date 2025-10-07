from flask import Blueprint, request, jsonify, session
from app.models import User
from app.services.user_service import AuthService
from app import db

auth_api = Blueprint('auth_api', __name__, url_prefix='/api/auth')

@auth_api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or email already exists'}), 400
    user = User(username=username, email=email)
    AuthService.set_password(user, password, persist=False)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Register complete'}), 201

@auth_api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and AuthService.check_password(user, password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login success'}), 200
    return jsonify({'error': 'Incorrect username or password'}), 401

@auth_api.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'}), 200

@auth_api.route('/forgot', methods=['POST'])
def forgot():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Email not found'}), 400
    token = AuthService.generate_reset_token(user)
    # TODO: send email with token (mock)
    return jsonify({'message': 'Reset email sent', 'token': token}), 200

@auth_api.route('/reset', methods=['POST'])
def reset():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    user = AuthService.verify_reset_token(token)
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400
    AuthService.set_password(user, new_password, persist=True)
    return jsonify({'message': 'Password reset complete'}), 200