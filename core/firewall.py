# core/firewall.py
import os
import json
from datetime import datetime


class Firewall:
    def __init__(self):
        self.blacklist_file = "logs/banned_ips.json"
        self.blocked_ips = self._load_blacklist()
        print("[SENTINEL FW] Firewall initialized. Loaded existing blocklist.")

    def _load_blacklist(self):
        if os.path.exists(self.blacklist_file):
            with open(self.blacklist_file, 'r') as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def _save_blacklist(self):
        os.makedirs("logs", exist_ok=True)
        with open(self.blacklist_file, 'w') as f:
            json.dump(self.blocked_ips, f, indent=4)

    def block_ip(self, ip, reason="Malicious Activity", severity="CRITICAL"):
        if ip not in self.blocked_ips:
            self.blocked_ips[ip] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": reason,
                "severity": severity
            }
            self._save_blacklist()
            print(f"[SENTINEL FW] BLOCKED: {ip} | Reason: {reason}")
            return True
        return False

    def is_blocked(self, ip):
        return ip in self.blocked_ips

    def unblock_ip(self, ip):
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            self._save_blacklist()
            print(f"[SENTINEL FW] UNBLOCKED: {ip}")
            return True
        return False

    def get_blocklist_details(self):
        # Returns full metadata for each blocked IP
        return self.blocked_ips

    def clear_all(self):
        self.blocked_ips = {}
        self._save_blacklist()
        print("[SENTINEL FW] Blocklist cleared by admin.")
