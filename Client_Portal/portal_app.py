# Client_Portal/portal_app.py
from flask import Flask, render_template, request
import requests
import time 

app = Flask(__name__)

# SENTINEL INTEGRATION AGENT 
SENTINEL_SIEM_URL = "http://127.0.0.1:5000/api/logs"
API_KEY = "SENTINEL-8842"

def verify_with_sentinel(payload_data, client_ip):
    """Yeh function chupchap data SENTINEL ko bhejega analyze karne ke liye"""
    try:
        headers = {'X-Forwarded-For': client_ip}
        data = {"payload": payload_data, "key": API_KEY}
        
       
        response = requests.post(SENTINEL_SIEM_URL, json=data, headers=headers, timeout=2)
        return response.status_code, response.json() if response.status_code == 200 else {}
    except requests.exceptions.ConnectionError:
        print("[!] SENTINEL SIEM UNREACHABLE! Running without protection...")
        
        
        time.sleep(2) 
        
        return 200, {"status": "safe"} 

@app.route('/', methods=['GET', 'POST'])
def login():
   
    client_ip = request.remote_addr 
    error_msg = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
      
        payload_string = f"[{username}] attempted login."
       
        check_string = username + password 
        
        status_code, siem_response = verify_with_sentinel(check_string, client_ip)
        
       
        if status_code == 403 or (status_code == 200 and siem_response.get("status") == "danger"):
           
            return render_template('blocked.html', ip=client_ip), 403
            
     
        if username == "admin" and password == "secure123":
            return "<h1 style='color:green; text-align:center; margin-top:50px;'> Welcome to Aegis Corp Internal Network!</h1>"
        else:
            error_msg = "Invalid Credentials. Event Logged."

    return render_template('login.html', error=error_msg)

if __name__ == '__main__':
    print("🌐 ORION LUXURY PORTAL STARTED ON PORT 8080")
    print("🛡️  SENTINEL API HOOK: ACTIVE")
    app.run(port=8080, debug=True, threaded=False)