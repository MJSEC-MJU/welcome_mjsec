from flask import Flask, request, make_response, render_template
import time

app = Flask(__name__)

access_log = {}

with open('FLAG.txt') as f:
    FLAG = f.read().strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/silent')
def silent():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    ref = request.headers.get("Referer", "")
    
    if ip in access_log or ua.strip() or ref.strip():
        return "You made a noise. Try again, silently.", 403

    return f"<h1>{FLAG}</h1>"

@app.route('/favicon.ico')
@app.route('/static/bait.js')
def bait():
    ip = request.remote_addr
    access_log[ip] = time.time()
    return "", 204

def clear_access_log_periodically():
    while True:
        time.sleep(60)
        access_log.clear()
        print("[INFO] access_log cleared.")

threading.Thread(target=clear_access_log_periodically, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8001)
