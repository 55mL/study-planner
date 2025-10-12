from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import ReadingPlans
from app.services.feedback_service import Feedback
from app.services.schedule_service import ScheduleService
from app.services.user_service import UserUpdateService
from app.utils.utils import get_today

web_main = Blueprint('web_main', __name__, template_folder='template') # ชี้ไปที่โฟลเดอร์ demo_backend

@web_main.route('/home')
@login_required
def home():
    print(f"=" * 50)
    print(f"✅ /home route accessed")
    print(f"✅ Session data: {dict(session)}")
    print(f"✅ user_id in session: {session.get('user_id')}")
    print(f"=" * 50)
    return render_template('schedule.html')

@web_main.route('/home.html')
@login_required
def feedback():
    return render_template('home.html')

@web_main.route('/add.html')
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
