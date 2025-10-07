from flask import Blueprint, request, jsonify, session
from app.models import ReadingPlans, User
from app.services.user_service import UserUpdateService
from app import db

plan_api = Blueprint('plan_api', __name__, url_prefix='/api/plans')

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@plan_api.route('', methods=['GET'])
def get_plans():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    plans = ReadingPlans.query.filter_by(user_id=user.id).all()
    return jsonify([
        {
            'id': plan.id,
            'exam_name': plan.exam_name,
            'exam_date': plan.exam_date.isoformat(),
            'level': plan.level
        } for plan in plans
    ])

@plan_api.route('', methods=['POST'])
def add_plan():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    try:
        plan = UserUpdateService.add_plan(
            user,
            exam_name=data['exam_name'],
            exam_date=data['exam_date'],
            level=int(data['level'])
        )
        db.session.commit()
        return jsonify({'message': 'Plan added', 'plan_id': plan.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@plan_api.route('/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    plan = ReadingPlans.query.filter_by(id=plan_id, user_id=user.id).first()
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    UserUpdateService.delete_plan(user, plan)
    db.session.commit()
    return jsonify({'message': 'Plan deleted'})