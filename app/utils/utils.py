from datetime import date, timedelta
from flask import session
def get_today():
    """คืนวันที่จำลอง ถ้าไม่มีให้ใช้วันจริง"""
    if "simulated_date" in session:
        return date.fromisoformat(session["simulated_date"])
    return date.today()


import inspect
import os

DEBUG_MODE = os.getenv("MYAPP_DEBUG", "0") == "1"

def log(text="", name="myapp", debug=False):
    if debug and not DEBUG_MODE:
        return
    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    prefix = f"[DEBUG][{name}]" if debug else f"[{name}]"
    print(f"{prefix} {filename}:{lineno} - {text}")


