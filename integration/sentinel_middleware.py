# integration/sentinel_middleware.py
#
# SENTINEL SIEM - Website Integration Middleware
# Engineered by Abhay Singh Taknet
#
# HOW TO USE:
#   1. Copy this file into your project
#   2. In your app.py: from sentinel_middleware import SentinelMiddleware
#   3. Wrap your Flask app: app.wsgi_app = SentinelMiddleware(app.wsgi_app)
#   4. Make sure SENTINEL is running on port 5000
#
import requests
import threading


SENTINEL_URL = "http://127.0.0.1:5000/api/logs"
SENTINEL_KEY = "SENTINEL-9921"

# Paths we never bother scanning — static files, favicon, etc.
SKIP_PATHS = ['.js', '.css', '.png', '.ico', '.jpg', '.svg', '.woff', '.map']


def _send_to_sentinel(ip, payload):
    # Fire and forget — runs in background so your site doesn't slow down
    try:
        requests.post(
            SENTINEL_URL,
            json={"key": SENTINEL_KEY, "payload": payload},
            headers={"X-Forwarded-For": ip},
            timeout=1.5
        )
    except Exception:
        pass  # SENTINEL being down should never crash your app


class SentinelMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path   = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET')
        query  = environ.get('QUERY_STRING', '')
        ip     = environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR', '0.0.0.0'))

        # Skip static assets — not worth scanning
        if not any(path.endswith(ext) for ext in SKIP_PATHS):
            payload = f"{method} {path}"
            if query:
                payload += f"?{query}"

            # Read POST body for form/JSON data
            if method == 'POST':
                try:
                    length  = int(environ.get('CONTENT_LENGTH', 0) or 0)
                    body    = environ['wsgi.input'].read(length)
                    payload += f" | BODY: {body.decode('utf-8', errors='ignore')[:300]}"
                    # Rewind so Flask can still read it
                    import io
                    environ['wsgi.input'] = io.BytesIO(body)
                except:
                    pass

            # Background thread — non-blocking
            t = threading.Thread(target=_send_to_sentinel, args=(ip, payload), daemon=True)
            t.start()

        return self.app(environ, start_response)
