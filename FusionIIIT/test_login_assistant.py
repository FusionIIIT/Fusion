import requests
url = "http://127.0.0.1:8000/api/auth/login/"
payload = {"username": "spacs_asst_login", "password": "user@123"}
r = requests.post(url, json=payload)
print(f"Login Assistant: {r.status_code}")
print(r.text)
