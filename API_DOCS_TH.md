# API Documentation สำหรับ Study Planner

## Authentication API (auth_api)
Base URL: `/api/auth`

### 1. ลงทะเบียนผู้ใช้ใหม่ 
POST `/api/auth/register`
```python
# Request Body
{
    "username": "testuser",  # ชื่อผู้ใช้ (ต้องไม่ซ้ำกับในระบบ)
    "email": "test@email.com",  # อีเมล (ต้องไม่ซ้ำกับในระบบ)
    "password": "password123"  # รหัสผ่าน
}

# Response (201 Created)
{
    "message": "Register complete"
}

# Error Response (400 Bad Request)
{
    "error": "Username or email already exists"  # กรณีมี username หรือ email ในระบบแล้ว
}
```

### 2. เข้าสู่ระบบ
POST `/api/auth/login`
```python
# Request Body
{
    "username": "testuser",  # ชื่อผู้ใช้
    "password": "password123"  # รหัสผ่าน
}

# Response (200 OK) - จะได้ session cookie กลับมาด้วย
{
    "message": "Login successful"
}

# Error Response (401 Unauthorized)
{
    "error": "Invalid username or password"
}
```

### 3. ออกจากระบบ
POST `/api/auth/logout`
```python
# ไม่ต้องส่ง body
# Response (200 OK)
{
    "message": "Logged out"
}
```

## แผนการอ่าน (plan_api)
Base URL: `/api/plans`

### 1. ดูแผนการอ่านทั้งหมด
GET `/api/plans`
```python
# Response (200 OK)
{
    "username": "testuser",  # ชื่อผู้ใช้
    "plans": [
        {
            "id": 1,  # ID ของแผน
            "exam_name": "Python Test",  # ชื่อการสอบ
            "exam_date": "2025-12-25",  # วันที่สอบ (ISO format)
            "level": 2  # ระดับความยาก (1-10)
        }
    ],
    "pending_count": 3,  # จำนวน feedback ที่ยังไม่ได้ตอบ
    "slots": {  # ข้อมูลช่วงเวลาอ่านหนังสือ
        "total": 10,  # จำนวนช่วงเวลาทั้งหมด
        "used": 5  # จำนวนช่วงเวลาที่ใช้ไปแล้ว
    }
}
```

### 2. เพิ่มแผนการอ่าน
POST `/api/plans`
```python
# Request Body
{
    "exam_name": "Python Test",  # ชื่อการสอบ (ต้องไม่ซ้ำกับที่มีอยู่)
    "exam_date": "2025-12-25",  # วันที่สอบ (ISO format)
    "level": 2  # ระดับความยาก 1-10 (1=ง่ายมาก, 10=ยากมาก)
}

# Response (201 Created)
{
    "message": "Added reading plan",
    "plan": {  # ข้อมูลแผนที่เพิ่ม
        "id": 1,
        "exam_name": "Python Test",
        "exam_date": "2025-12-25",
        "level": 2
    }
}
```

### 3. ตั้งค่าชั่วโมงอ่านต่อวัน
POST `/api/plans/daily-hours`
```python
# Request Body
{
    "daily_read_hours": 3.5  # จำนวนชั่วโมงที่อ่านต่อวัน (0-24)
}

# Response (200 OK)
{
    "message": "Updated daily reading hours"
}
```

### 4. ลบแผนการอ่าน
DELETE `/api/plans/<plan_id>`
```python
# ไม่ต้องส่ง body
# Response (200 OK)
{
    "message": "Deleted reading plan"
}

# Error (404 Not Found)
{
    "error": "Plan not found"
}
```

## ตารางการอ่าน (schedule_api)
Base URL: `/api/schedule`

### 1. ดูตารางการอ่าน
GET `/api/schedule`
```python
# Response (200 OK)
{
    "simulated_today": "2025-10-07",  # วันที่ปัจจุบัน (หรือวันที่จำลอง)
    "events": [
        {
            "day": "2025-10-07",  # วันที่
            "exam": "Python Test",  # ชื่อการสอบ
            "slots": 3,  # จำนวนช่วงเวลาที่ต้องอ่าน
            "is_exam_day": false,  # true ถ้าเป็นวันก่อนสอบ
            "feedback_done": false  # true ถ้าตอบ feedback แล้ว
        }
    ]
}
```

## Feedback API (feedback_api)
Base URL: `/api/feedback`

### 1. ดู feedback ที่ยังไม่ได้ตอบ
GET `/api/feedback/pending`
```python
# Response (200 OK)
{
    "allocations": [
        {
            "id": 1,  # ID ของ allocation
            "date": "2025-10-07",  # วันที่อ่าน
            "exam": "Python Test",  # ชื่อการสอบ
            "slots": 3  # จำนวนช่วงเวลาที่อ่าน
        }
    ]
}
```

### 2. ส่ง feedback
POST `/api/feedback`
```python
# Request Body
{
    "alloc_id": 1,  # ID ของ allocation
    "feedback_type": "too_much"  # ประเภท feedback (too_much, just_right, too_little)
}

# Response (200 OK)
{
    "message": "Feedback submitted"
}
```

## การใช้งาน API ใน Python

```python
import requests

# 1. เข้าสู่ระบบ
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'testuser',
    'password': 'password123'
})
cookies = response.cookies  # เก็บ cookies ไว้ใช้ในคำสั่งต่อไป

# 2. เพิ่มแผนการอ่าน
response = requests.post('http://localhost:5000/api/plans', 
    json={
        'exam_name': 'Python Test',
        'exam_date': '2025-12-25',
        'level': 2
    },
    cookies=cookies  # ใส่ cookies ทุกครั้งที่เรียก API
)

# 3. ดูตารางการอ่าน
response = requests.get('http://localhost:5000/api/schedule', cookies=cookies)
schedule = response.json()
```

## คำอธิบายเพิ่มเติม

1. **ระบบ Authentication**
   - ใช้ session-based authentication
   - ต้องเก็บ cookies จาก login ไว้ใช้กับทุก request
   - session จะหมดอายุใน 3 วัน

2. **แผนการอ่าน**
   - แต่ละคนสามารถมีได้หลายแผน
   - ชื่อการสอบต้องไม่ซ้ำกันในแผนของคนเดียวกัน
   - ระดับความยาก (1-10) มีผลต่อการจัดสรรเวลาอ่าน

3. **ตารางการอ่าน**
   - คำนวณจากแผนการอ่านทั้งหมด
   - จัดสรรช่วงเวลาตามระดับความยากและวันที่สอบ
   - วันก่อนสอบ (`is_exam_day=true`) จะไม่มีการจัดสรรเวลาอ่าน

4. **Feedback**
   - ต้องตอบ feedback สำหรับทุกวันที่มีการอ่าน
   - ใช้ปรับปรุงการจัดสรรเวลาในอนาคต