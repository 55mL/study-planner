from datetime import date, timedelta
from flask import session
def get_today():
    """คืนวันที่จำลอง ถ้าไม่มีให้ใช้วันจริง"""
    if "simulated_date" in session:
        return date.fromisoformat(session["simulated_date"])
    return date.today()


import inspect
import os
def log(text="", name="myapp"):
    # ดึง caller frame (1 ระดับบน)
    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno

    # พิมพ์ log พร้อมไฟล์+บรรทัด
    print(f"[{name}] {filename}:{lineno} - {text}")


