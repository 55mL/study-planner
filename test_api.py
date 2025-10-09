import requests
import json

# กำหนด base URL ของ API
BASE_URL = 'http://127.0.0.1:5000/api'

def test_auth():
    # 1. ทดสอบ Login
    login_data = {
        'username': 'testuser',
        'password': 'testpass'
    }
    
    response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
    print("\n=== Login Test ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # เก็บ cookies จาก response เพื่อใช้ในคำสั่งต่อไป
    cookies = response.cookies
    
    # 2. ดูแผนการอ่านทั้งหมด
    response = requests.get(f'{BASE_URL}/plans', cookies=cookies)
    print("\n=== Get Plans ===")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # 3. เพิ่มแผนการอ่านใหม่
    new_plan = {
        'exam_name': 'Python Test',
        'exam_date': '2025-12-25',
        'level': 2
    }
    
    response = requests.post(f'{BASE_URL}/plans', json=new_plan, cookies=cookies)
    print("\n=== Add New Plan ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 4. ตั้งค่าชั่วโมงอ่านต่อวัน
    hours_data = {
        'daily_read_hours': 4
    }
    
    response = requests.post(f'{BASE_URL}/plans/daily-hours', json=hours_data, cookies=cookies)
    print("\n=== Set Daily Hours ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 5. ดูตารางการอ่าน
    response = requests.get(f'{BASE_URL}/schedule', cookies=cookies)
    print("\n=== Get Schedule ===")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == '__main__':
    test_auth()