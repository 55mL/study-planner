from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db
from app.models import User, ReadingPlans
from .schedule_service import ScheduleService
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

import logging

class AuthService:
	# password check and set
	@staticmethod
	def set_password(user, password, persist=True):
		user.password = generate_password_hash(password)
		if persist:
			db.session.commit()

	@staticmethod
	def check_password(user, password):
		return check_password_hash(user.password, password)

	# reset password
	@staticmethod
	def generate_reset_token(user, expires_sec=3600):
		s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
		return s.dumps(user.email, salt="password-reset-salt")

	@staticmethod
	def verify_reset_token(token, max_age=3600):
		s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
		try:
			email = s.loads(token, salt="password-reset-salt", max_age=max_age)
		except Exception:
			return None
		return User.query.filter_by(email=email).first()


class UserUpdateService:
	@staticmethod
	def set_daily_read_hours(user, daily_hours, persist=True):
		if daily_hours <= 0 and daily_hours >= 24:
			raise ValueError("value must between 0-24")
		for plan in user.reading_plans:
			plan.weight = (plan.weight / user.daily_read_hours) * daily_hours
		user.daily_read_hours = daily_hours
		ScheduleService.update_schedule(user, persist=persist)
		if persist:
			db.session.commit()

	@staticmethod
	def add_plan(user, exam_name, exam_date, level, persist=True):
		"""
		เพิ่ม ReadingPlan ใหม่ให้ user
		- ตรวจสอบชื่อซ้ำ
		- แปลง exam_date จาก string → date
		- persist ลง DB
		"""
		logger.debug(f"add {exam_name}")

		# กันชื่อซ้ำ
		existing = ReadingPlans.query.filter_by(user_id=user.id, exam_name=exam_name).first()
		if existing:
			raise ValueError("You already have a subject with that name.")

		# แปลงวันที่
		exam_date_obj = datetime.strptime(exam_date, "%Y-%m-%d").date()

		# สร้าง plan ใหม่
		plan = ReadingPlans(
			user_id=user.id,
			exam_name=exam_name,
			exam_date=exam_date_obj,
			level=level,
		)
		db.session.add(plan)
		db.session.flush()   # ให้ plan.id ถูกสร้างก่อน

		# เรียกคำนวณ slots ใหม่ (จะจัดการ weight/horizon ให้เอง)
		ScheduleService.update_schedule(user, persist=persist)

		if persist:
			db.session.commit()

		return plan

	@staticmethod
	def delete_plan(user, plan, persist=True):
		"""
		ลบ ReadingPlan ออกจาก user
		- ลบ plan ออกจาก DB
		- เรียกคำนวณ slots ใหม่ (จะจัดการ weight/horizon ให้เอง)
		- persist ลง DB
		"""
		logger.debug(f"delete {plan.exam_name}")

		# ลบ plan ออกจาก session
		db.session.delete(plan)
		db.session.flush()

		# เรียกคำนวณ slots ใหม่ (ลดน้ำหนัก/จัดสรรใหม่)
		ScheduleService.update_schedule(user, persist=persist)

		if persist:
			db.session.commit()