from . import db
from app import login_manager
from datetime import date
from flask_login import UserMixin
from sqlalchemy import CheckConstraint


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = "users"

    # basic attbruite
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # record attbruite
    daily_read_hours = db.Column(db.Integer, default=3)
    latest_exam_date = db.Column(db.Date, default=None)
    # bind plans
    reading_plans = db.relationship('ReadingPlans', backref='user', lazy=True)

    # check data(level, hours_per_day)
    __table_args__ = ( 
        CheckConstraint('daily_read_hours >= 0 AND daily_read_hours <= 24', name='daily_read_hours_range'), 
    )


class ReadingPlans(db.Model):
    __tablename__ = "reading_plans"

    # exam info
    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.Date, default=date.today, nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=5, nullable=False)
    hours_per_day = db.Column(db.Integer, default=1, nullable=False)
    # get User and daily plan
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    daily_allocations = db.relationship(
        "DailyAllocations",
        back_populates="plan",
        cascade="save-update, merge"
    )
    # calculate
    allocated_slot = db.Column(db.Integer, default=0, nullable=False)
    weight = db.Column(db.Float, default=0.0, nullable=False)

    # check data(level, hours_per_day)
    __table_args__ = (
        CheckConstraint('level >= 1 AND level <= 10', name='level_range'), 
        CheckConstraint('hours_per_day >= 0 AND hours_per_day <= 24', name='hours_per_day_range'), 
        db.UniqueConstraint('user_id', 'exam_name', name='unique_user_exam'), 
    )


class DailyAllocations(db.Model): 
    __tablename__ = "daily_allocations"

    # allocations info
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    slots = db.Column(db.Integer, nullable=False, default=0)
    feedback_done = db.Column(db.Boolean, default=False, nullable=False)
    # get user and plan
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(
        db.Integer, 
        db.ForeignKey("reading_plans.id", ondelete="SET NULL"), 
        nullable=True
    )

    plan = db.relationship("ReadingPlans", back_populates="daily_allocations")

    exam_name_snapshot = db.Column(db.String(100))
    

    # bind plan
    # plan = db.relationship(
    #     "ReadingPlans",
    #     backref=db.backref("daily_allocations", cascade="all, delete-orphan")
    # )







# cal
# 10 days read 10 hours_per_day (10 * 10 = 100 slot)
# add 1 level 5
# 1 : 100(slot) * 5(level) = 500 (weight)
# 1 : 500(weight) / 500(sum_weight) * 100(slot) = 100

# 1 : 100 slot

# add 2 level 10
# 2 : 100(slot) * 10(level) = 1000 (weight)
# 1 : 500(weight) / 1500(sum_weight) * 100(slot) = 33.33
# 2 : 1000(weight) / 1500(sum_weight) * 100(slot) = 66.67

# 1 : 33 slot
# 2 : 67 slot

# sub route if  9 day left with two subject
# read_weight : 15(sum_level) * 10(hours_per_day) = 150(read_weight)
# 2 : (minus with highest weight first until it 0) 1000(weight) - 150(read_weight) = 850
# 1 : 500(weight) / 1350(sum_weight) * 90(slot) = 33.33
# 2 : 850(weight) / 1350(sum_weight) * 90(slot) = 56.67
# 1 : 33 slot
# 2 : 57 slot
# end sub route if  9 day left with two subject

# back to route 10 day left
# add 3 level 3
# 3 : 100(slot) * 3(level) = 300(weight)
# 1 : 500(weight) / 1800(sum_weight) * 100(slot) = 27.78
# 2 : 1000(weight) / 1800(sum_weight) * 100(slot) = 55.56
# 3 : 300(weight) / 1800(sum_weight) * 100(slot) = 16.67

# 1 : 28 slot
# 2 : 55 slot
# 3 : 17 slot

# 9 days left(90 slot)
# read_weight : 18(sum_level) * 10(hours_per_day) = 180(read_weight)
# sum_weight : 1800(sum_weight) - 180(read_weight) = 1620(sum_weight)
# 2 : 1000(weight) - 180(read_weight) = 820(weight)
# 1 : 500 / 1620 * 90(slot) = 27.78
# 2 : 820 / 1620 * 90(slot) = 45
# 3 : 300 / 1620 * 90(slot) = 16.67

# 1 : 28 slot
# 2 : 45 slot
# 3 : 17 slot

# add 4 level 5
# 4 : 90 * 5 = 450
# 1 : 500 / 2070 * 90 = 21.74
# 2 : 820 / 2070 * 90 = 35.65
# 3 : 300 / 2070 * 90 = 13.04
# 4 : 450 / 2070 * 90 = 19.57

# 1 : 22 slot
# 2 : 36 slot
# 3 : 13 slot
# 4 : 19 slot

# 8 days left(80 slot)
# read_weight : 23(sum_level) * 10(hours_per_day) = 230(read_weight)
# sum_weight : 2070(sum_weight) - 230(read_weight) = 1840(sum_weight)
# 2 : 820(weight) - 230(read_weight) = 590(weight)
# 1 : 500 / 1840 * 80 = 21.74
# 2 : 590 / 1840 * 80 = 25.65
# 3 : 300 / 1840 * 80 = 13.04
# 4 : 450 / 1840 * 80 = 19.57

# 1 : 22 slot
# 2 : 26 slot
# 3 : 13 slot
# 4 : 19 slot

# 7 days left(70 slot)
# read_weight : 23(sum_level) * 10(hours_per_day) = 230(read_weight)
# sum_weight : 1840(sum_weight) - 230(read_weight) = 1610(sum_weight)
# 2 : 590(weight) - 230(read_weight) = 360(weight)
# 1 : 500 / 1610 * 70 = 21.74
# 2 : 360 / 1610 * 70 = 15.65
# 3 : 300 / 1610 * 70 = 13.04
# 4 : 450 / 1610 * 70 = 19.57

# 1 : 22 slot
# 2 : 16 slot
# 3 : 13 slot
# 4 : 19 slot

# 6 days left(60 slot)
# read_weight : 23(sum_level) * 10(hours_per_day) = 230(read_weight)
# sum_weight : 1610(sum_weight) - 230(read_weight) = 1380(sum_weight)
# 2 : 360(weight) - 230(read_weight) = 130(weight)
# 1 : 500 / 1380 * 60 = 21.74
# 2 : 130 / 1380 * 60 = 5.65
# 3 : 300 / 1380 * 60 = 13.04
# 4 : 450 / 1380 * 60 = 19.57

# 1 : 22 slot
# 2 : 6 slot
# 3 : 13 slot
# 4 : 19 slot

# 5 days left(50 slot)
# read_weight : 23(sum_level) * 10(hours_per_day) = 230(read_weight)
# sum_weight : 1380(sum_weight) - 230(read_weight) = 1150(sum_weight)
# 2 : 130(weight) - 230(read_weight) = -100(weight)
# cuz of read all num 2 subject, so next is consider to pick highest weight
# 1 : 500(weight) - 100(left_read_weight) = 400(weight)
# 1 : 400 / 1150 * 50 = 17.39
# 2 : 0 / 1150 * 50 = 0
# 3 : 300 / 1150 * 50 = 13.04
# 4 : 450 / 1150 * 50 = 19.57

# 1 : 18 slot (use 18 cuz it read 6 slot for num 2 subject and read this 4 slot)
# 2 : 0 slot (clear)
# 3 : 13 slot
# 4 : 19 slot


