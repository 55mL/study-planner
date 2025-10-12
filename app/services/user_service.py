from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db
from app.models import User, ReadingPlans
from .schedule_service import ScheduleService
from datetime import datetime
from app.utils.utils import get_today

import logging
logger = logging.getLogger(__name__)

import logging



class AuthService:
	"""
	Service สำหรับจัดการ authentication ของ user เช่น set/check password, reset password
	"""
	# password check and set
	@staticmethod
	def set_password(user, password, persist=True):
		"""
		กำหนดรหัสผ่านใหม่ให้ user (hash ก่อนเก็บ)
		persist=True จะ commit ลง DB ทันที
		"""
		user.password = generate_password_hash(password)
		if persist:
			db.session.commit()

	@staticmethod
	def check_password(user, password):
		"""
		ตรวจสอบรหัสผ่าน (hash แล้วเทียบกับที่เก็บใน DB)
		"""
		return check_password_hash(user.password, password)

	# reset password
	@staticmethod
	def generate_reset_token(user, expires_sec=3600):
		"""
		สร้าง token สำหรับ reset password (ใช้ email เป็น payload)
		"""
		s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
		return s.dumps(user.email, salt="password-reset-salt")

	@staticmethod
	def verify_reset_token(token, max_age=3600):
		"""
		ตรวจสอบ token สำหรับ reset password ว่ายังใช้ได้ไหม (ยังไม่หมดอายุ)
		คืน user ถ้า valid, None ถ้าไม่ valid
		"""
		s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
		try:
			email = s.loads(token, salt="password-reset-salt", max_age=max_age)
		except Exception:
			return None
		return User.query.filter_by(email=email).first()




class UserUpdateService:
	"""
	Service สำหรับอัปเดตข้อมูล user เช่น daily_read_hours, การเพิ่ม/ลบแผน, ล้างแผนที่หมดอายุ
	"""
	@staticmethod
	def set_username(user, new_username, uniqeable=False, persist=True):
		if not new_username:
			raise KeyError("username not found")
		# ตรวจสอบว่า username ซ้ำหรือไม่
		if uniqeable:
			if User.query.filter_by(username=new_username).first():
				raise ValueError("username already used")
			
		user.username = new_username

		if persist:
			db.session.commit()

	@staticmethod
	def set_password(user, new_password, old_password, persist=True):
		if old_password and new_password:
			if not check_password_hash(user.password, old_password):
				raise UnicodeError("old password is incorrect")
			AuthService.set_password(user, new_password)
		else:
			raise KeyError("new_password or old_password is empty")
		
		if persist:
			db.session.commit()

	@staticmethod
	def set_daily_read_hours(user, daily_hours, persist=True):
		"""
		กำหนดจำนวนชั่วโมงอ่านหนังสือต่อวันใหม่ให้ user
		- ปรับ weight ของทุก plan ตามสัดส่วน
		- อัปเดตตาราง schedule ใหม่
		- persist=True จะ commit ลง DB ทันที
		"""
		if daily_hours <= 0 and daily_hours >= 24:
			raise ValueError("value must between 0-24")
		for plan in user.reading_plans:
			plan.weight = (plan.weight / user.daily_read_hours) * daily_hours
		user.daily_read_hours = daily_hours
		ScheduleService.update_schedule(user, persist=persist)
		if persist:
			db.session.commit()

	@staticmethod
	def set_email_notifications(user, val, persist=True):
		if isinstance(val, bool):
			user.email_notifications = val
		else:
			raise ValueError("email_notifications ต้องเป็น true/false")
		if persist:
			db.session.commit()

	@staticmethod
	def add_plan(user, exam_name, exam_date, level, persist=True):
		"""
		เพิ่ม ReadingPlan ใหม่ให้ user
		- ตรวจสอบชื่อซ้ำ ถ้ามีแล้วจะ raise error
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

	@staticmethod
	def cleanup_expired_plans(user):
		"""
		ลบแผนที่หมดอายุ (วันสอบ < วันนี้) ออกจาก user
		- เรียกใช้ delete_plan กับทุกแผนที่หมดอายุ
		- อัปเดต last_cleanup_date
		- commit ลง DB
		"""
		today = get_today()
		expired_plans = ReadingPlans.query.filter(
			ReadingPlans.user_id == user.id,
			ReadingPlans.exam_date < today
		).all()

		for plan in expired_plans:
			UserUpdateService.delete_plan(user, plan)

		user.last_cleanup_date = today
		db.session.commit()

