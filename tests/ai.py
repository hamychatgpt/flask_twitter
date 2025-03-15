import requests
import json

# آدرس سرور
url = 'http://localhost:5000/api/analyzer/sentiment'

# داده ارسالی
data = {
    'text': 'عجب رئیس جمهوری داریم'
}

# ارسال درخواست
response = requests.post(url, json=data)

# نمایش پاسخ
print(json.dumps(response.json(), indent=2, ensure_ascii=False))