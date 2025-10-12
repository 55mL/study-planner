# core-api/routes/api/study.py
from datetime import date
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app.extensions import db
from app.models import DailyAllocations
from app.utils.utils import get_today, log

study_api = Blueprint("study_api", __name__, url_prefix="/api/study")

def get_daily_summary(user_id, target_date=None):
    if target_date is None:
        target_date = get_today()

    allocations = (
        db.session.query(
            DailyAllocations.exam_name_snapshot,
            func.sum(DailyAllocations.slots).label("total_hours")
        )
        .filter(DailyAllocations.user_id == user_id)
        .filter(DailyAllocations.date == target_date)
        .group_by(DailyAllocations.exam_name_snapshot)
        .all()
    )

    total_hours = sum(a.total_hours for a in allocations)

    log(f"user_id: {user_id}, total_hours: {total_hours}")

    return {
        "date": target_date.isoformat(),
        "total_hours": total_hours,
        "subjects": [
            {"name": a.exam_name_snapshot, "hours": a.total_hours} for a in allocations
        ]
    }

@study_api.route("/daily-summary", methods=["GET"])
def daily_summary():
    user_id = request.args.get("user_id", type=int)
    date_str = request.args.get("date")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    if date_str:
        target_date = date.fromisoformat(date_str)
    else:
        target_date = get_today()

    summary = get_daily_summary(user_id, target_date)
    return jsonify(summary)