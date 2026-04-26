# core/reporter.py
import sqlite3
import csv
import json
import os
from datetime import datetime


class Reporter:
    def __init__(self, db_path="db/sentinel.db"):
        self.db_path = db_path
        os.makedirs("exports", exist_ok=True)

    def _fetch_logs(self, threats_only=False):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if threats_only:
                cur.execute("SELECT * FROM security_logs WHERE is_threat=1 ORDER BY id DESC")
            else:
                cur.execute("SELECT * FROM security_logs ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print(f"[REPORTER] Fetch error: {e}")
            return []

    def export_csv(self, threats_only=False):
        rows = self._fetch_logs(threats_only)
        if not rows:
            return None

        fname = f"exports/sentinel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fname, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"[REPORTER] CSV exported: {fname}")
        return fname

    def export_json(self, threats_only=False):
        rows = self._fetch_logs(threats_only)
        fname = f"exports/sentinel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=4, default=str)

        print(f"[REPORTER] JSON exported: {fname}")
        return fname

    def get_attack_type_stats(self):
        # Breaks down threat count by detected attack pattern
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT message FROM security_logs WHERE is_threat=1")
            rows = cur.fetchall()
            conn.close()

            counts = {}
            attack_types = [
                "SQL_Injection", "XSS_Attack", "Command_Injection",
                "Path_Traversal", "SSRF_Attack", "Log4Shell",
                "XXE_Attack", "Brute_Force_Pattern", "HONEYPOT"
            ]
            for row in rows:
                msg = row[0] or ""
                matched = False
                for atype in attack_types:
                    if atype.replace("_", " ").lower() in msg.lower() or atype.lower() in msg.lower():
                        counts[atype] = counts.get(atype, 0) + 1
                        matched = True
                        break
                if not matched:
                    counts["Other"] = counts.get("Other", 0) + 1

            return counts
        except Exception as e:
            print(f"[REPORTER] Stats error: {e}")
            return {}

    def get_summary(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM security_logs WHERE is_threat=1")
            total_threats = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM security_logs WHERE is_threat=0")
            total_safe = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM security_logs WHERE severity='CRITICAL'")
            critical = cur.fetchone()[0]
            cur.execute("SELECT ip, COUNT(*) as c FROM security_logs WHERE is_threat=1 GROUP BY ip ORDER BY c DESC LIMIT 1")
            row = cur.fetchone()
            top_ip = row[0] if row else "N/A"
            conn.close()
            return {
                "total_threats": total_threats,
                "total_safe": total_safe,
                "critical_count": critical,
                "top_attacker_ip": top_ip
            }
        except:
            return {}
