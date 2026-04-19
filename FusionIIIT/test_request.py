import requests
import json

urls = [
    "http://127.0.0.1:8000/scholarships/api/settings/",
    "http://127.0.0.1:8000/awards/api/student-profile/"
]
for url in urls:
    try:
        r = requests.get(url)
        print(f"URL: {url}")
        print(f"  Status: {r.status_code}")
        print(f"  Body: {r.text[:100]}")
    except Exception as e:
        print(f"Error for {url}: {e}")
