# integration/example_site/site_app.py
#
# Sample Flask website integrated with SENTINEL SIEM
# Run this AFTER SENTINEL is running (python app.py)
# Then open http://localhost:5050
#
from flask import Flask, request, render_template_string
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sentinel_middleware import SentinelMiddleware

app = Flask(__name__)

HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Demo Site — Protected by SENTINEL</title>
    <style>
        body { background:#0f172a; color:#e2e8f0; font-family:monospace; padding:60px; text-align:center; }
        h1   { color:#60a5fa; }
        .badge { display:inline-block; background:rgba(34,197,94,0.1); border:1px solid #22c55e;
                 color:#4ade80; padding:6px 18px; border-radius:6px; font-size:12px; margin-bottom:30px; }
        form  { margin-top:30px; }
        input { background:#1e293b; border:1px solid #334155; color:#e2e8f0;
                padding:10px 16px; border-radius:6px; width:260px; }
        button { background:#3b82f6; color:#fff; border:none; padding:10px 24px;
                 border-radius:6px; cursor:pointer; margin-left:8px; }
        .links { margin-top:40px; display:flex; gap:16px; justify-content:center; flex-wrap:wrap; }
        .links a { background:#1e293b; border:1px solid #334155; color:#94a3b8;
                   padding:10px 20px; border-radius:8px; text-decoration:none; font-size:13px; }
        .links a:hover { border-color:#60a5fa; color:#60a5fa; }
        .note { margin-top:40px; font-size:12px; color:#475569; }
    </style>
</head>
<body>
    <div class="badge">🛡 PROTECTED BY SENTINEL SIEM</div>
    <h1>Demo Website</h1>
    <p style="color:#64748b;">All traffic to this site is monitored by SENTINEL in real-time.</p>

    <form method="POST" action="/login">
        <input type="text" name="username" placeholder="Username" />
        <button type="submit">Login</button>
    </form>

    <div class="links">
        <a href="/products">Products Page</a>
        <a href="/search?q=laptop">Search Page</a>
        <a href="/admin">Admin Panel</a>
        <a href="/api/data">API Endpoint</a>
    </div>

    <div class="note">
        Try injecting attacks in the login form — watch SENTINEL dashboard react in real-time.<br>
        Example: <code>admin' OR 1=1 --</code> or <code>&lt;script&gt;alert(1)&lt;/script&gt;</code>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_PAGE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    return f"""
    <html><body style='background:#0f172a;color:#e2e8f0;font-family:monospace;padding:60px;text-align:center;'>
        <h2>Login attempt: <span style='color:#f87171;'>{username}</span></h2>
        <p style='color:#64748b;'>SENTINEL has already analyzed this payload.</p>
        <a href='/' style='color:#60a5fa;'>← Back</a>
    </body></html>
    """

@app.route('/products')
@app.route('/search')
@app.route('/admin')
@app.route('/api/data')
def dummy_pages():
    return f"""
    <html><body style='background:#0f172a;color:#94a3b8;font-family:monospace;padding:60px;text-align:center;'>
        <h2>Page: {request.path}</h2>
        <p>This visit was logged by SENTINEL.</p>
        <a href='/' style='color:#60a5fa;'>← Back</a>
    </body></html>
    """

# ── Apply SENTINEL middleware ──────────────────────────────────
app.wsgi_app = SentinelMiddleware(app.wsgi_app)

if __name__ == '__main__':
    print("=" * 50)
    print("  DEMO SITE running at http://localhost:5050")
    print("  SENTINEL monitoring at http://localhost:5000")
    print("=" * 50)
    app.run(port=5050, debug=False)
