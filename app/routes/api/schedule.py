from flask import Blueprint, jsonify, session
from app.models import User, DailyAllocations
from app.utils.utils import get_today
import datetime

schedule_api = Blueprint('schedule_api', __name__, url_prefix='/api')

def get_current_user():
    """ดึง user จาก session"""
    user_id = session.get('_user_id')  # ✅ เปลี่ยนเป็น _user_id
    
    print(f"🔍 get_current_user called")
    print(f"🔍 Session dict: {dict(session)}")
    print(f"🔍 _user_id from session: {user_id}")
    
    if not user_id:
        print(f"❌ No _user_id in session!")
        return None
    
    user = User.query.get(int(user_id))  # ✅ แปลงเป็น int
    print(f"🔍 User object: {user}")
    return user

@schedule_api.route('/schedule', methods=['GET'])
def get_schedule():
    """
    ดึงข้อมูลตารางการอ่านของ user ปัจจุบัน
    """
    print(f"=" * 50)
    print(f"📡 /api/schedule endpoint called")
    print(f"📡 Full session: {dict(session)}")
    print(f"=" * 50)
    
    user = get_current_user()
    
    if not user:
        print(f"❌ No user found - returning 401")
        return jsonify({'error': 'Unauthorized'}), 401
    
    print(f"✅ User found: {user.id} - {user.username}")
    
    simulated_today = get_today()
    
    allocations = (DailyAllocations.query
                   .filter_by(user_id=user.id)
                   .order_by(DailyAllocations.date.asc())
                   .all())
    
    print(f"📊 Found {len(allocations)} allocations")
    
    events = []
    for alloc in allocations:
        events.append({
            'day': alloc.date.isoformat(),
            'exam': alloc.exam_name_snapshot,
            'slots': alloc.slots,
            'is_exam_day': (
                alloc.plan is not None and 
                alloc.date + datetime.timedelta(days=1) == alloc.plan.exam_date
            ),
            'feedback_done': alloc.feedback_done
        })
    
    print(f"📤 Returning {len(events)} events")
    
    return jsonify({
        'simulated_today': simulated_today.isoformat(),
        'events': events
    })