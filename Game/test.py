import requests

BASE_URL = "http://127.0.0.1:8000"

def test():
    r = requests.post(f"{BASE_URL}/test")
    print(r.json())

print(test())