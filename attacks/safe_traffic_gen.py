import requests
import time
import random

API_URL = "http://127.0.0.1:5000/api/logs"
API_KEY = "SENTINEL-9921"

USERS = ["ayush_admin", "devine_analyst", "rohit_customer", "priya_hr"]
ACTIVITIES = [
    "Login Success: Entered valid passcode",
    "Browsing: Viewed Rolex Submariner Watch Page",
    "Cart: Added Omega Speedmaster to shopping cart",
    "Checkout: Initiated secure payment process",
    "Logout: User session terminated safely"
]

print("🟢 STARTING SAFE TRAFFIC GENERATOR...")

for i in range(20):
    user = random.choice(USERS)
    activity = random.choice(ACTIVITIES)
    
    # Clean Payload (No single quotes to prevent false SQLi detection)
    payload_msg = f"User {user} : {activity}"
    fake_ip = f"192.168.1.{random.randint(10, 99)}"

    data = {"key": API_KEY, "payload": payload_msg}
    headers = {"X-Forwarded-For": fake_ip}

    try:
        response = requests.post(API_URL, json=data, headers=headers)
        
        # Ab humein terminal mein exact dikhega ki SENTINEL kya kar raha hai
        if response.status_code == 200:
            print(f"[✅ SAFE] Server Accepted: {fake_ip} -> {user}")
        else:
            print(f"[❌ BLOCKED] Server Rejected: Code {response.status_code} - Check Lockdown")
        time.sleep(1.5)
    except Exception as e:
        print("❌ Server Down: Please check if app.py is running!")