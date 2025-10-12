import math
from dataclasses import dataclass
from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import date, datetime, timedelta
from app.extensions import db
from app.models import DailyAllocations, ReadingPlans, User
from datetime import date, timedelta
from app.utils.utils import log, get_today

@dataclass
class Subject:
	name: str
	level: int
	required: int
	exam_day: int
	remaining: int
	plan_id: int   # เก็บ id ของ ReadingPlans ไว้ด้วย

def check_feasible(start_day: int, daily_hours: int, subjects: List[Subject]) -> bool:
	"""
	ตรวจสอบว่าเวลาที่มีพอสำหรับอ่านทุกวิชาหรือไม่ (feasibility check)
	"""
	last_day = max(s.exam_day for s in subjects)
	total_time = (last_day - start_day) * daily_hours
	total_required = sum(s.required for s in subjects)
	log(f"check feasible: total_time {total_time}, total_required {total_required}", debug=True)
	return total_time == total_required

def redistribute_subject(start_day: int, daily_hours: int, subjects: List[Subject]) -> bool:
	"""
	กระจายชั่วโมงอ่านที่เกินไปยังวิชาที่สอบทีหลัง (ถ้าเวลาวิชาแรกไม่พอ)
	"""
	# ตรวจสอบ feasibility รายวิชา
	# (เพิ่ม)เรียงวิชาที่เสี่ยงก่อน: สอบเร็วที่สุดมาก่อน
	subjects_sorted = sorted(subjects, key=lambda s: s.exam_day)
	redistributeted = 0 # เพิ่มตัวเก็บที่ redistribute ไปแล้ว
	for s in subjects_sorted:
		available = (s.exam_day - start_day) * daily_hours
		if (s.required + redistributeted) > available: # เพิ่มการหักด้วย redistributeted
			excess = (s.required + redistributeted) - available # คิดกับ redistributeted
			print(f"Subject '{s.name}' requires {s.required} but only {available - redistributeted} hours available before exam day {s.exam_day}")
			print(f"Redistributing excess {excess} hours to later subjects...")
			redistributeted += s.required - excess # เพิ่มการเก็บ redistributeted

			# หา subjects ที่สอบหลังจาก s.exam_day
			later_subjects = [t for t in subjects if t.exam_day > s.exam_day]
			if not later_subjects:
				print("No later subjects to redistribute to → Impossible")
				return False

			weights = [t.required for t in later_subjects]
			allocation = largest_remainder_allocation(weights, excess)
			for t, hrs in zip(later_subjects, allocation):
				t.required += hrs
				t.remaining += hrs
			s.required = available
			s.remaining = available

def largest_remainder_allocation(weights: List[int], capacity: int) -> List[int]:
	"""
	กระจาย capacity (จำนวนชั่วโมง) ให้แต่ละวิชาตามสัดส่วน weight โดยใช้ largest remainder method
	"""
	total = sum(weights)
	if total <= 0:
		return [0] * len(weights)
	shares = [(w * capacity) / total for w in weights]
	floors = [math.floor(s) for s in shares]
	allocated = sum(floors)
	remainder = capacity - allocated
	frac = [(i, shares[i] - floors[i]) for i in range(len(shares))]
	frac.sort(key=lambda x: x[1], reverse=True)
	result = floors[:]
	for i in range(remainder):
		result[frac[i][0]] += 1
	return result

def schedule_backward(start_day: int, daily_hours: int, subjects: List[Subject]) -> Dict[int, List[Tuple[str, int]]]:
	"""
	สร้างตารางอ่านหนังสือย้อนหลัง (backward scheduling)
	- ใส่วันที่ทบทวนก่อน (วันก่อนสอบ)
	- ไล่จากวันหลัง → วันหน้า กระจายชั่วโมงที่เหลือ
	คืน dict: day ordinal → list ของ (subject, hours)
	"""
	last_day = max(s.exam_day for s in subjects)
	schedule: Dict[int, List[Tuple[str, int]]] = {day: [] for day in range(start_day, last_day)}

	if not check_feasible(start_day, daily_hours, subjects):
		log(f"it's feasible return null", debug=True)
		return None
    
	redistribute_subject(start_day, daily_hours, subjects)

	# 1. ใส่วันที่ทบทวนก่อน (วันก่อนสอบ)
	exam_groups: Dict[int, List[Subject]] = {}
	for s in subjects:
		review_day = s.exam_day - 1
		if review_day >= start_day:
			exam_groups.setdefault(review_day, []).append(s)

	for review_day, subs in exam_groups.items():
		weights = [s.remaining for s in subs]
		allocation = largest_remainder_allocation(weights, daily_hours)
		entries = []
		for s, hrs in zip(subs, allocation):
			if hrs > 0:
				s.remaining -= hrs
				entries.append((s.name, hrs))
		schedule[review_day].extend(entries)

	# 2. ไล่จากวันหลัง → วันหน้า
	for day in range(last_day-1, start_day-1, -1):
		remaining_capacity = daily_hours - sum(hrs for _, hrs in schedule[day])
		if remaining_capacity <= 0:
			continue

		# เลือก candidates ที่ยังเหลือ requirement และสอบหลังจากวันนี้
		candidates = [s for s in subjects if s.remaining > 0 and s.exam_day > day]
		if not candidates:
			continue

		# เรียง: ง่ายที่สุดก่อน (remaining น้อยก่อน), ถ้าเท่ากันค่อยสอบไกลก่อน, ถ้าเท่ากันเรียงจากชื่อย้อนกลับ
		candidates.sort(key=lambda s: (s.level, -s.exam_day, s.name[::-1]))

		while remaining_capacity > 0 and candidates:
			s = candidates[0]
			hrs = min(s.remaining, remaining_capacity)
			s.remaining -= hrs
			schedule[day].append((s.name, hrs))
			remaining_capacity -= hrs
			if s.remaining == 0:
				candidates.pop(0)

	return schedule


class ScheduleService:
	"""
	Service สำหรับจัดการตารางเรียน/อ่านหนังสือของ user
	- ใช้เมื่อมีการเพิ่ม/ลบแผน, เปลี่ยน weight, เปลี่ยนเวลาต่อวัน ฯลฯ
	"""
	@staticmethod
	def get_total_weight(user):
		"""
		คืนผลรวม weight ของทุกแผนใน user (ใช้สำหรับคำนวณ feedback)
		"""
		return sum(p.weight for p in user.reading_plans)


	@staticmethod
	def get_days_till_exam(user, start_days=None, next_day=False):
		"""
		คืนจำนวนวันจนถึงวันสอบล่าสุด (ใช้สำหรับคำนวณ feedback)
		"""
		latest_exam = max(p.exam_date for p in user.reading_plans)
		if start_days is None:
			start_days = get_today()
		log(f"start_days: {start_days}", debug=True)
		start_days = (latest_exam - start_days).days
		if next_day:
			start_days -= 1

		return start_days


	@staticmethod
	def update_schedule(user, persist=True):
		"""
		อัปเดตตาราง schedule ของ user
		- ถ้าวันนี้ตอบ feedback ครบแล้ว → สร้างตารางใหม่เริ่มพรุ่งนี้
		- ถ้ายังไม่เคยมี allocation วันนี้เลย → สร้างตารางเริ่มวันนี้
		- ถ้ายังตอบ feedback ไม่ครบ → คำนวณตารางใหม่ (แต่ไม่เปลี่ยน horizon)
		persist=True จะ commit ลง DB ทันที
		"""
		today = get_today()

		# ยังมี allocation ของวันนี้ที่ยังไม่ได้ feedback อยู่ไหม?
		pending_today = DailyAllocations.query.filter(
			DailyAllocations.user_id == user.id,
			DailyAllocations.date == today,
			DailyAllocations.feedback_done == False
		).count()

		# เช็กว่ามี allocation ของวันนี้อยู่หรือเปล่า
		has_today = DailyAllocations.query.filter(
			DailyAllocations.user_id == user.id,
			DailyAllocations.date == today
		).count() > 0

		if pending_today == 0:
			if has_today:
				# ✅ มี allocation วันนี้แล้ว และตอบครบ → สร้างตารางใหม่เริ่มพรุ่งนี้
				ScheduleService.calculate_slots(user, next_day=True, persist=persist)
				ScheduleService.distribute_schedule(user, next_day=True, persist=persist)
			else:
				# ✅ ยังไม่เคยมี allocation วันนี้เลย (เพิ่งเพิ่มวิชาแรก)
				# → สร้างตารางเริ่มจากวันนี้
				ScheduleService.calculate_slots(user, next_day=False, persist=persist)
				ScheduleService.distribute_schedule(user, next_day=False, persist=persist)
		else:
			ScheduleService.calculate_slots(user, persist=persist)
			ScheduleService.distribute_schedule(user, persist=persist)



	@staticmethod
	def calculate_slots(user, start_days=None, next_day=False, mode="latest", persist=True):
		"""
		คำนวณ slot ของแต่ละวิชา
		- start_days: วันเริ่มอ่าน (ถ้าไม่ใส่จะใช้วันนี้)
		- next_day: ความคลาดเคลื่อนของวัน (อย่างลงวันนี้อ่านพรุ่งนี้ กันบรีฟแตก)
		- persist: ถ้า True จะอัปเดต weight และ allocated_slot ลง DB
		"""
		if not user.reading_plans:
			return {}

		# --- 1) หา latest exam จากทุก plan ---
		latest_exam = max(p.exam_date for p in user.reading_plans)
		if start_days is None:
			start_days = get_today()
        
		log(f"start_days: {start_days}", debug=True)

		start_days = (latest_exam - start_days).days
		if next_day:
			start_days -= 1

		# --- 2) ถ้าไม่มีวันเหลือ ---
		if not start_days or start_days <= 0:
			result = {plan.exam_name: 0 for plan in user.reading_plans}
			if persist:
				for plan in user.reading_plans:
					plan.weight = 0
					plan.allocated_slot = 0
				db.session.commit()
			return result

		# slot ทั้งหมดที่มี
		day_slots = start_days * user.daily_read_hours

		# --- 3) ตรวจ horizon เดิม (เก็บไว้ใน user.latest_exam_date) ---
		old_latest = getattr(user, "latest_exam_date", None)
		if old_latest is None:
			user.latest_exam_date = latest_exam
			old_latest = latest_exam

		log(f"check horizon")

		if latest_exam > old_latest:
			# horizon ขยาย → เพิ่ม weight
			delta_days = (latest_exam - old_latest).days
			if next_day:
				delta_days -= 1

			log("calculate_slots", f"horizon extended, delta_days: {delta_days}")

			for plan in user.reading_plans:
				if plan.allocated_slot > 0:
					plan.weight += plan.level * delta_days

			user.latest_exam_date = latest_exam

		elif latest_exam < old_latest:
			# horizon หด → ลด weight
			delta_days = (old_latest - latest_exam).days
			if next_day:
				delta_days -= 1

			log("calculate_slots", f"horizon shrunk, delta_days: {delta_days}")

			for plan in user.reading_plans:
				if plan.allocated_slot > 0:
					# ลดน้ำหนัก แต่ไม่ให้ติดลบ
					plan.weight = max(0, plan.weight - plan.level * delta_days)

			user.latest_exam_date = latest_exam


		# --- 4) คำนวณ weight ของแต่ละวิชา ---
		subjects = []
		today = get_today()

		for plan in user.reading_plans:
			if mode == "per-exam":
				days_until_exam = (plan.exam_date - today).days
			if mode == "latest":
				days_until_exam = (user.latest_exam_date - today).days

			if not next_day:
				days_until_exam += 1

			if days_until_exam < 0 or days_until_exam == 0:
				# วันสอบเลยไปแล้วหรือวันสอบวันนี้ → ข้ามไปเลย
				continue
			else:
				base_weight = plan.level * days_until_exam * user.daily_read_hours

			final_weight = plan.weight if plan.weight else base_weight

			subjects.append({
				"plan": plan,
				"weight": final_weight,
				"base_weight": base_weight
			})

		# --- 5) รวม weight ---
		total_weight = sum(s["weight"] for s in subjects)
		if total_weight == 0:
			result = {s["plan"].exam_name: 0 for s in subjects}
			if persist:
				for s in subjects:
					s["plan"].weight = 0
					s["plan"].allocated_slot = 0
				db.session.commit()
			return result

		# --- 6) คำนวณ slot ตามสัดส่วน weight ---
		raw = [(s["plan"], (s["weight"] / total_weight) * day_slots, s["weight"]) for s in subjects]

		floored = {plan.exam_name: math.floor(val) for plan, val, weight in raw}
		remaining = int(day_slots - sum(floored.values()))

		# แจก remainder ให้วิชาที่มีเศษมากที่สุด
		remainders = sorted(
			[(plan.exam_name, val - math.floor(val), plan) for plan, val, weight in raw],
			key=lambda x: x[1],
			reverse=True
		)
		for i in range(remaining):
			idx = i % len(remainders)
			floored[remainders[idx][0]] += 1

		# --- 7) persist ลง DB ---
		if persist:
			for plan, val, weight in raw:
				plan.weight = weight
				plan.allocated_slot = floored[plan.exam_name]
			db.session.commit()

		# --- 8) return พร้อม weight ---
		result = {
			plan.exam_name: {
				"hours": floored[plan.exam_name],
				"weight": weight
			}
			for plan, val, weight in raw
		}
		return result


	@staticmethod
	def distribute_schedule(user, start_day=None, next_day=False, persist=True):
		"""
		โหลด ReadingPlans ของ user จาก DB, แปลงเป็น Subject,
		เรียก schedule_backward, และ persist ลง DailyAllocations ถ้าต้องการ

		คืนค่า:
		  - None เมื่อ impossible หรือไม่มีแผน
		  - schedule dict (day ordinal -> list of (subject, hours)) เมื่อสำเร็จ
		"""
		plans = ReadingPlans.query.filter_by(user_id=user.id).all()
		if not plans:
			log("no plan", debug=True)
			return None

		# แปลงเป็น Subject (copy ค่า primitive จริง ๆ + plan_id)
		subjects: List[Subject] = []
		for p in plans:
			subjects.append(Subject(
				name=str(p.exam_name),                  # copy string
				level=int(p.level),                  # copy string
				required=int(p.allocated_slot),         # copy int
				exam_day=int(p.exam_date.toordinal()),  # copy int
				remaining=int(p.allocated_slot),        # copy int
				plan_id=int(p.id)                       # copy id
			))

		if start_day is None:
			start_day = get_today().toordinal()
        
		if next_day:
			start_day += 1

		daily_hours = int(user.daily_read_hours)

		schedule = schedule_backward(start_day, daily_hours, subjects)
		if schedule is None:
			log("no schedule")
			return None

		if persist:
			today = get_today()
			# ลบเฉพาะ allocation ที่ยังไม่ได้ feedback และเป็นวันอนาคต
			# เปลี่ยนเป็นลบเป็นวันอนาคตเฉยๆ
			DailyAllocations.query.filter(
				DailyAllocations.user_id == user.id,
				DailyAllocations.feedback_done == False,
				DailyAllocations.date >= today
			).delete()

			db.session.commit()
			
			# เพิ่ม allocations ใหม่จาก schedule
			for d in sorted(schedule.keys()):
				for subject_name, hours in schedule[d]:
					subj = next((s for s in subjects if s.name == subject_name), None)
					if not subj:
						continue
					db.session.add(DailyAllocations(
						user_id=user.id,
						plan_id=subj.plan_id,
						date=date.fromordinal(d),
						slots=hours,
						exam_name_snapshot=subj.name  # ✅ copy ชื่อวิชาเก็บไว้
					))

			db.session.commit()
			return schedule # คืนตารางด้วยเพื่อให้ route แสดงหรือ redirect ได้

		return schedule