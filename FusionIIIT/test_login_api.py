import requests

url = "http://127.0.0.1:8000/api/auth/login/"
payload = {
    "username": "23BCS010",
    "password": "user@123"
}

print(f"Testing POST to {url} with {payload}...")
try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
