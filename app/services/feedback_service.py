from .schedule_service import ScheduleService
from .user_service import UserUpdateService
import datetime
from app.extensions import db
from app.models import DailyAllocations, ReadingPlans
from app.utils.utils import get_today, log



def full_oneday_weight(weight, total_weight, days_till_exam):
    """
    คำนวณน้ำหนักที่ควรอ่านใน 1 วัน (ใช้ใน feedback แบบ 'read_all')
    ระวังกรณี days_till_exam = 1 เพราะจะหารด้วยศูนย์
    """
    if days_till_exam == 1:
        return 0
    output = (total_weight - (weight * days_till_exam)) / (1 - days_till_exam)
    log(f"weight: {weight}, oneday_weight: {output}", debug=True)
    return weight - output



class Feedback:
    """
    Service สำหรับจัดการ feedback ของผู้ใช้ เช่น คืน allocation ที่ต้อง feedback, ส่ง feedback, ปรับ weight
    """
    @staticmethod
    def get_pending_feedback(user):
        """
        คืน allocations ที่ยังไม่ได้ feedback และถึงวันแล้ว (เรียงจากวันเก่าสุด)
        ใช้สำหรับแสดงรายการ feedback ที่ต้องทำ
        """
        today = get_today()
        return (DailyAllocations.query
                .filter(
                    DailyAllocations.user_id == user.id,
                    DailyAllocations.feedback_done == False,
                    DailyAllocations.date <= today,
                    DailyAllocations.plan_id.isnot(None)
                )
                .order_by(DailyAllocations.date.asc())
                .all())

    @staticmethod
    def get_next_feedback(user):
        """
        คืน allocation วันเก่าสุดที่ยังไม่ได้ feedback และถึงวันแล้ว (ใช้สำหรับ feedback ทีละรายการ)
        """
        today = get_today()
        return (DailyAllocations.query
                .join(ReadingPlans)
                .filter(
                    DailyAllocations.user_id == user.id,
                    DailyAllocations.feedback_done == False,
                    DailyAllocations.date <= today
                )
                .order_by(DailyAllocations.date.asc())
                .first())

    @staticmethod
    def submit_feedback(user, allocation, feedback_type, persist=True):
        """
        รับ feedback จากผู้ใช้และปรับ weight ของแผนตามประเภท feedback
        - read_in_time: อ่านทัน → ลด weight
        - harder: ยาก → เพิ่ม weight
        - easier: ง่าย → ลด weight
        - read_all: อ่านหมด → ปรับ weight ตามสูตร
        ถ้า weight หมดหรือวันสอบเลยแล้วจะลบแผนออก
        อัปเดตตาราง schedule ใหม่หลัง feedback
        persist=True จะ commit ลง DB ทันที
        """
        plan = allocation.plan
        # apply feedback logic
        if feedback_type == "read_in_time":
            plan.weight = max(0, plan.weight - plan.level * allocation.slots)
        elif feedback_type == "harder":
            plan.weight *= 1.2
        elif feedback_type == "easier":
            plan.weight *= 0.8
        elif feedback_type == "read_all":
            total_weight = ScheduleService.get_total_weight(user)
            days_till_exam = ScheduleService.get_days_till_exam(user)
            plan.weight = max(0, min(plan.weight - plan.level * allocation.slots, 
                                     full_oneday_weight(plan.weight, total_weight, days_till_exam)))            

        # mark feedback done
        allocation.feedback_done = True

        if persist:
            db.session.commit()

        review_day = plan.exam_date
        # ถ้า weight หมดหรือวันสอบเลยแล้วให้ลบแผนออก
        if plan.weight <= 0 or (review_day < get_today() and allocation.feedback_done):
            UserUpdateService.delete_plan(user, plan)
        
        ScheduleService.update_schedule(user, persist=persist)

        if persist:
            db.session.commit()
