import time
import random
import os
from datetime import datetime, timedelta

# Agar logs folder nahi hai toh bana dega
if not os.path.exists("../logs"):
    os.makedirs("../logs", exist_ok=True)

USERS = ["ayush_admin", "devine_analyst", "rohit_customer", "priya_hr", "karan_sales"]
ACTIVITIES = [
    "Login Success: Entered valid passcode",
    "Browsing: Viewed 'Rolex Submariner' Watch Page",
    "Cart: Added 'Omega Speedmaster' to shopping cart",
    "Checkout: Initiated secure payment process",
    "Account: Updated shipping address to Laxmangarh",
    "Authentication: 2FA verified successfully",
    "Logout: User session terminated safely"
]

print("🟢 GENERATING SAFE LOGS DIRECTLY TO FILE...")

# Seedha file banayega (API ko bypass karke)
file_path = "../logs/safe_logs.txt"

with open(file_path, "w", encoding="utf-8") as f:
    # 35 ekdum real lagne wale logs banayega
    for i in range(35):
        user = random.choice(USERS)
        activity = random.choice(ACTIVITIES)
        fake_ip = f"192.168.1.{random.randint(10, 99)}"
        
        # Thoda time aage-peeche karke real look dena
        log_time = (datetime.now() - timedelta(minutes=35-i)).strftime("%H:%M:%S")
        
        log_line = f"[{log_time}] IP: {fake_ip} | Status: INFO | Activity: User '{user}' -> {activity}\n"
        f.write(log_line)
        print(f"Added: {log_line.strip()}")
        time.sleep(0.05)

print("\n✅ JADOO HO GAYA! FILE CREATED SUCCESSFULLY!")
print("Apne VS Code mein 'logs/safe_logs.txt' check kar, wahan aa gayi hai!")