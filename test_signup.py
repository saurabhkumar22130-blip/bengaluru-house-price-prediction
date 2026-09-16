import requests

session = requests.Session()

# 1. Get signup page to ensure app is up
try:
    r = session.get("http://127.0.0.1:5000/signup")
    print("GET /signup status:", r.status_code)

    # 2. Post to signup as broker
    data = {
        "username": "test_broker",
        "password": "password123",
        "confirm_password": "password123",
        "role": "broker"
    }
    r = session.post("http://127.0.0.1:5000/signup", data=data, allow_redirects=False)
    print("POST /signup status:", r.status_code)
    print("Redirect location:", r.headers.get("Location"))

except Exception as e:
    print("Error:", e)
