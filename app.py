# app.py — SENTINEL SIEM Pro | Main Server
import psutil
import time
import random
import os
import json
from flask import Flask, render_template, jsonify, request, send_file

from core.detection import DetectionEngine
from core.firewall import Firewall
from core.database import SentinelDB
from core.ai_engine import SentinelAI
from core.reporter import Reporter

app = Flask(__name__)
reporter = Reporter()

# init all modules
firewall  = Firewall()
detector  = DetectionEngine()
db        = SentinelDB()
ai        = SentinelAI()
ai.train_model()

API_KEY = "SENTINEL-9921"

# in-memory log buffers for live dashboard
safe_logs    = []
threat_logs  = []
threat_count = 0
system_lockdown = False
last_location   = "N/A"

os.makedirs("logs", exist_ok=True)

# geo pools for simulating attacker origin
GEO_GLOBAL = [
    {"city": "Moscow, Russia"},
    {"city": "Shanghai, China"},
    {"city": "Pyongyang, North Korea"},
    {"city": "Sao Paulo, Brazil"},
    {"city": "Tehran, Iran"},
    {"city": "Bucharest, Romania"},
]
GEO_LOCAL = [
    {"city": "Delhi, India"},
    {"city": "Sikar, Rajasthan"},
    {"city": "Mumbai, India"},
]


def save_log(log_entry, is_threat=False):
    try:
        risk_score     = log_entry.get('score', 0)
        payload_length = len(log_entry.get('msg', ''))

        ai_result = ai.analyze_behavior(risk_score, is_threat, payload_length)

        # AI override — if it flags something we didn't catch, escalate it
        if ai_result == "ANOMALY_DETECTED" and not is_threat:
            is_threat = True
            log_entry['severity'] = 'HIGH'
            log_entry['msg']    = "[AI ANOMALY] " + log_entry.get('msg', '')
            log_entry['action'] = "BLOCKED BY AI"
            log_entry['score']  = 75

        db.save_log(log_entry, is_threat)

        # also write to flat text files — useful for quick tail/grep
        fname = "logs/threat_events.txt" if is_threat else "logs/safe_logs.txt"
        with open(fname, "a", encoding="utf-8") as f:
            line = (
                f"[{log_entry.get('time','N/A')}] "
                f"IP:{log_entry.get('ip','?')} | "
                f"{log_entry.get('severity','INFO')} | "
                f"{log_entry.get('msg','')}\n"
            )
            f.write(line)

    except Exception as e:
        print(f"[SENTINEL] Log save error: {e}")


# ──────────────────────────────────────────
# HONEYPOT TRAPS — fake paths only an attacker would probe
# ──────────────────────────────────────────
@app.route('/phpmyadmin')
@app.route('/admin_bypass')
@app.route('/db_backup.zip')
@app.route('/secret_keys')
@app.route('/.env')
@app.route('/wp-admin')
def honeypot_trap():
    global threat_count, system_lockdown, threat_logs

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    timestamp = time.strftime("%H:%M:%S")

    trap_log = {
        'time':     timestamp,
        'ip':       client_ip,
        'loc':      "HONEYPOT ZONE",
        'msg':      f"HONEYPOT TRIGGERED: {request.path}",
        'severity': 'CRITICAL',
        'score':    100,
        'action':   'AUTO-BLOCKED'
    }

    threat_logs.append(trap_log)
    save_log(trap_log, is_threat=True)

    threat_count += 1
    if threat_count >= 5:
        system_lockdown = True

    firewall.block_ip(client_ip, reason="Honeypot Triggered", severity="CRITICAL")

    return "<h1>403 Forbidden</h1>", 403


# ──────────────────────────────────────────
# MAIN SIEM LOG INGESTION API
# ──────────────────────────────────────────
@app.route('/api/logs', methods=['GET', 'POST'])
def logs_api():
    global threat_count, last_location, system_lockdown, safe_logs, threat_logs

    if request.method == 'GET':
        combined = []

        for log in safe_logs[-25:]:
            combined.append({
                "severity":  "INFO",
                "message":   f"[SRC:{log.get('ip','?')}] {log.get('msg','Normal Traffic')} (ACT:ALLOWED)",
                "timestamp": log.get('time', time.strftime("%H:%M:%S"))
            })

        for log in threat_logs[-25:]:
            combined.append({
                "severity":  log.get('severity', 'CRITICAL'),
                "message":   f"[SRC:{log.get('ip','?')}] {log.get('msg','Malicious')} (ACT:{log.get('action','BLOCKED')})",
                "timestamp": log.get('time', time.strftime("%H:%M:%S")),
                "location":  log.get('loc', 'Unknown')
            })

        combined.sort(key=lambda x: x['timestamp'])

        blocked = list(firewall.blocked_ips.keys())
        blocked_details = firewall.get_blocklist_details()

        return jsonify({
            "logs":            combined,
            "banned_ips":      blocked,
            "banned_details":  blocked_details,
            "lockdown":        system_lockdown
        })

    # POST — external clients send payloads here for analysis
    if request.method == 'POST':
        data = request.json
        if not data or data.get("key") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

        payload   = data.get("payload", "")
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        timestamp = time.strftime("%H:%M:%S")

        # rate limit check via AI module
        rate_exceeded, req_count = ai.check_rate_limit(client_ip)

        if firewall.is_blocked(client_ip) or system_lockdown:
            return jsonify({"status": "danger", "reason": "blocked"}), 403

        if rate_exceeded:
            firewall.block_ip(client_ip, reason=f"Rate limit exceeded ({req_count} req/min)", severity="HIGH")
            log_entry = {
                'time': timestamp, 'ip': client_ip,
                'loc': 'RATE LIMIT', 'msg': f"Rate limit exceeded — {req_count} requests in 60s",
                'severity': 'HIGH', 'score': 70, 'action': 'AUTO-BLOCKED'
            }
            threat_logs.append(log_entry)
            save_log(log_entry, is_threat=True)
            threat_count += 1
            return jsonify({"status": "danger", "reason": "rate_limit"}), 429

        is_malicious, message, risk_score, severity = detector.analyze_request(payload)

        if is_malicious:
            threat_count += 1
            loc = random.choice(GEO_GLOBAL)['city']
            last_location = loc

            firewall.block_ip(client_ip, reason=message, severity=severity)

            if risk_score >= 90 or severity == "CRITICAL":
                system_lockdown = True

            log_entry = {
                'time': timestamp, 'ip': client_ip, 'loc': loc,
                'msg': f"{message} | {payload[:120]}", 'severity': severity,
                'score': risk_score, 'action': 'AUTO-BLOCKED'
            }
            threat_logs.append(log_entry)
            save_log(log_entry, is_threat=True)
            return jsonify({"status": "danger", "mitigation": "AUTO-BLOCKED"}), 403

        else:
            log_entry = {
                'time': timestamp, 'ip': client_ip, 'loc': 'CLIENT',
                'msg': payload, 'severity': 'INFO', 'score': 0, 'action': 'ALLOWED'
            }
            safe_logs.append(log_entry)
            save_log(log_entry, is_threat=False)
            return jsonify({"status": "safe"}), 200


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/get_stats')
def get_stats():
    global threat_count, last_location, system_lockdown
    return jsonify({
        'cpu':           psutil.cpu_percent(),
        'ram':           psutil.virtual_memory().percent,
        'disk':          psutil.disk_usage('/').percent,
        'safe_logs':     safe_logs[-20:],
        'threat_logs':   threat_logs[-20:],
        'threats':       threat_count,
        'last_location': last_location,
        'lockdown':      system_lockdown,
        'blocked_ips':   list(firewall.blocked_ips.keys())
    })


@app.route('/api/analytics')
def get_analytics():
    return jsonify(db.get_dashboard_analytics())


@app.route('/login_attempt', methods=['POST'])
def login_attempt():
    global threat_count, last_location, system_lockdown

    ip        = request.headers.get('X-Forwarded-For', request.remote_addr)
    username  = request.form.get('username', '')
    timestamp = time.strftime("%H:%M:%S")

    if firewall.is_blocked(ip):
        return "BLOCKED BY SENTINEL FIREWALL", 403

    is_malicious, message, risk_score, severity = detector.analyze_request(username)

    if is_malicious:
        threat_count += 1
        loc = random.choice(GEO_LOCAL)['city']
        last_location = loc

        action = "FLAGGED"
        if risk_score >= 70:
            firewall.block_ip(ip, reason="Login Intrusion Attempt", severity=severity)
            action = "AUTO-BLOCKED"
            system_lockdown = True

        log_entry = {
            'time': timestamp, 'ip': ip, 'loc': loc,
            'msg': message, 'severity': severity,
            'score': risk_score, 'action': action
        }
        threat_logs.append(log_entry)
        save_log(log_entry, is_threat=True)
        return "Login Failed - Flagged by SENTINEL", 200

    return "Login Failed - Invalid Credentials", 200


# ──────────────────────────────────────────
# SOC ADMIN CONTROLS
# ──────────────────────────────────────────
@app.route('/api/block_ip', methods=['POST'])
def manual_block():
    data = request.json or {}
    target_ip = data.get('ip')
    if not target_ip:
        return jsonify({"status": "error", "msg": "No IP provided"}), 400

    firewall.block_ip(target_ip, reason="Manual block by SOC Admin", severity="HIGH")
    log_entry = {
        'time': time.strftime("%H:%M:%S"),
        'msg':  f"SOC MANUAL BLOCK: {target_ip}"
    }
    safe_logs.append(log_entry)
    save_log(log_entry, is_threat=False)
    return jsonify({"status": "success", "msg": f"IP {target_ip} blocked"})


@app.route('/api/unblock_ip', methods=['POST'])
def manual_unblock():
    data = request.json or {}
    target_ip = data.get('ip')
    if not target_ip:
        return jsonify({"status": "error", "msg": "No IP provided"}), 400

    result = firewall.unblock_ip(target_ip)
    return jsonify({"status": "success" if result else "not_found"})


@app.route('/api/restore_system', methods=['POST'])
def restore_system():
    global threat_count, system_lockdown
    threat_count    = 0
    system_lockdown = False
    log_entry = {
        'time': time.strftime("%H:%M:%S"),
        'msg':  "SYSTEM RESTORED BY ADMIN — LOCKDOWN LIFTED"
    }
    safe_logs.append(log_entry)
    save_log(log_entry, is_threat=False)
    return jsonify({"status": "success", "msg": "System restored"})


@app.route('/view_secrets')
def view_secrets():
    if system_lockdown:
        return """
        <html><body style='background:#1a0000;color:red;font-family:monospace;padding:100px;text-align:center;'>
            <h1>🔴 VAULT SEALED — SYSTEM IN LOCKDOWN</h1>
            <p>Active threat detected. Data exfiltration prevention active.</p>
        </body></html>
        """, 403

    try:
        if not os.path.exists('secure_data/company_secrets.txt'):
            return "<h3>ERROR: secure_data/company_secrets.txt not found</h3>", 404

        with open('secure_data/company_secrets.txt', 'r') as f:
            content = f.read()

        return f"""
        <html>
        <body style='background:#030712;color:#00ff88;font-family:monospace;padding:50px;text-align:center;'>
            <div style='border:1px solid #00ff88;padding:30px;display:inline-block;max-width:700px;'>
                <h1 style='letter-spacing:4px;'>🔓 SENTINEL SECURE VAULT</h1>
                <p style='color:#94a3b8;'>Status: DECRYPTED — Access Granted</p>
                <pre style='background:#0f172a;padding:20px;text-align:left;border-radius:8px;overflow:auto;'>{content}</pre>
                <button onclick="window.close()"
                    style='background:#dc2626;color:#fff;border:none;padding:10px 24px;margin-top:16px;cursor:pointer;border-radius:4px;'>
                    CLOSE VAULT
                </button>
            </div>
        </body></html>
        """
    except Exception as e:
        return f"<h3>Vault Error: {e}</h3>", 500


@app.route('/api/export_csv')
def export_csv():
    fname = reporter.export_csv(threats_only=False)
    if not fname:
        return jsonify({"error": "No data to export"}), 404
    return send_file(fname, as_attachment=True)


@app.route('/api/export_threats_csv')
def export_threats_csv():
    fname = reporter.export_csv(threats_only=True)
    if not fname:
        return jsonify({"error": "No threat data yet"}), 404
    return send_file(fname, as_attachment=True)


@app.route('/api/attack_stats')
def attack_stats():
    counts = reporter.get_attack_type_stats()
    summary = reporter.get_summary()
    return jsonify({"attack_types": counts, "summary": summary})


@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    global safe_logs, threat_logs, threat_count, system_lockdown
    safe_logs    = []
    threat_logs  = []
    threat_count = 0
    system_lockdown = False
    # clear flat log files too
    open("logs/safe_logs.txt", "w").close()
    open("logs/threat_events.txt", "w").close()
    return jsonify({"status": "success", "msg": "All in-memory logs cleared"})


if __name__ == '__main__':
    print("=" * 55)
    print("  SENTINEL SIEM — ENTERPRISE THREAT DETECTION")
    print("  Engineered by Abhay Singh Taknet")
    print("=" * 55)
    app.run(debug=True, port=5000)
