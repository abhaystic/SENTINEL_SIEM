# core/database.py
import sqlite3
import os
import threading


class SentinelDB:
    def __init__(self, db_name="sentinel.db"):
        if not os.path.exists("db"):
            os.makedirs("db")

        self.db_path = f"db/{db_name}"
        self._local = threading.local()
        self._lock = threading.Lock()
        self._setup()
        print("[SENTINEL DB] Database engine ready.")

    def _get_conn(self):
        # Each thread gets its own connection — avoids SQLite threading issues
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
        return self._local.conn

    def _setup(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT,
                ip             TEXT,
                location       TEXT,
                message        TEXT,
                severity       TEXT,
                risk_score     INTEGER,
                payload_length INTEGER DEFAULT 0,
                action         TEXT,
                is_threat      BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()

    def save_log(self, log_entry, is_threat):
        payload = log_entry.get('msg', '')
        with self._lock:
            conn = self._get_conn()
            conn.execute('''
                INSERT INTO security_logs
                    (timestamp, ip, location, message, severity, risk_score, payload_length, action, is_threat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.get('time', ''),
                log_entry.get('ip', 'SYS'),
                log_entry.get('loc', 'N/A'),
                payload,
                log_entry.get('severity', 'INFO'),
                log_entry.get('score', 0),
                len(payload),
                log_entry.get('action', 'LOGGED'),
                is_threat
            ))
            conn.commit()

    def get_dashboard_analytics(self):
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM security_logs WHERE is_threat = 1")
            total_threats = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM security_logs WHERE severity = 'CRITICAL'")
            critical_threats = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM security_logs WHERE is_threat = 0")
            safe_traffic = cur.fetchone()[0]

            cur.execute("""
                SELECT ip, COUNT(*) as cnt FROM security_logs
                WHERE is_threat = 1
                GROUP BY ip ORDER BY cnt DESC LIMIT 5
            """)
            top_ips = [{"ip": r[0], "count": r[1]} for r in cur.fetchall()]

            cur.execute("""
                SELECT severity, COUNT(*) FROM security_logs
                WHERE is_threat = 1
                GROUP BY severity
            """)
            severity_breakdown = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) FROM security_logs
                WHERE is_threat = 1
                GROUP BY hour ORDER BY hour
                LIMIT 24
            """)
            hourly = [{"hour": r[0], "count": r[1]} for r in cur.fetchall()]

            return {
                "total_threats":     total_threats,
                "critical_alerts":   critical_threats,
                "safe_connections":  safe_traffic,
                "top_attackers":     top_ips,
                "severity_breakdown": severity_breakdown,
                "hourly_activity":   hourly
            }
        except Exception as e:
            print(f"[SENTINEL DB] Analytics error: {e}")
            return {
                "total_threats": 0, "critical_alerts": 0,
                "safe_connections": 0, "top_attackers": [],
                "severity_breakdown": {}, "hourly_activity": []
            }
