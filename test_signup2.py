import requests
r = requests.post("http://127.0.0.1:5000/signup", data={"username": "test_broker", "password": "123", "confirm_password": "123", "role": "broker"})
print(r.text)
