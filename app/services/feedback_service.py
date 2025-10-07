from .schedule_service import ScheduleService
from .user_service import UserUpdateService
from app import db
from app.models import DailyAllocations, ReadingPlans
from utils import get_today


def full_oneday_weight(weight, total_weight, days_till_exam):
    # ระวังกรณี days_till_exam = 1 เพราะจะหารด้วยศูนย์
    if days_till_exam == 1:
        return 0
    
    output = (total_weight - (weight * days_till_exam)) / (1 - days_till_exam)
    return output


class Feedback:
    @staticmethod
    def get_pending_feedback(user):
        """คืน allocations ที่ยังไม่ได้ feedback และถึงวันแล้ว เรียงจากวันเก่าสุด"""
        today = get_today()
        return (DailyAllocations.query
                .filter(
                    DailyAllocations.user_id == user.id,
                    DailyAllocations.feedback_done == False,
                    DailyAllocations.date <= today
                )
                .order_by(DailyAllocations.date.asc())
                .all())

    @staticmethod
    def get_next_feedback(user):
        """คืน allocation วันเก่าสุดที่ยังไม่ได้ feedback และถึงวันแล้ว"""
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
        feedback_type เช่น "read_in_time", "harder", "easier"
        """
        plan = allocation.plan
        # apply feedback logic
        if feedback_type == "read_in_time":
            allocation.plan.weight = max(0, plan.weight - plan.level * allocation.slots)
        elif feedback_type == "harder":
            allocation.plan.weight *= 1.2
        elif feedback_type == "easier":
            allocation.plan.weight *= 0.8
        elif feedback_type == "read_all":
            total_weight = ScheduleService.get_total_weight(user)
            days_till_exam = ScheduleService.get_days_till_exam(user)
            allocation.plan.weight = max(0, min(plan.weight - plan.level * allocation.slots, 
                                                full_oneday_weight(plan.weight, total_weight, days_till_exam)))            

        # mark feedback done
        allocation.feedback_done = True

        if plan.weight <= 0:
            UserUpdateService.delete_plan(user, plan)
        
        next_day = False
        if allocation.date == get_today():
            next_day = True

        ScheduleService.update_schedule(user, persist=persist)

        if persist:
            db.session.commit()
