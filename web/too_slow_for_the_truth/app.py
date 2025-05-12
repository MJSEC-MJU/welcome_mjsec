from flask import Flask, request, make_response
import time
import functools
import os

app = Flask(__name__)

FLAG_PATH = os.path.join(os.path.dirname(__file__), 'FLAG.txt')
with open(FLAG_PATH) as f:
    FLAG = f.read().strip()

def timeout(seconds=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            if time.time() - start > seconds:
                return "Too slow... (timeout simulated)", 500
            return result
        return wrapper
    return decorator

@app.route("/")
def index():
    return '''
<html>
  <body>
    <h2>Too Slow for the Truth</h2>
    <p>어떤 조건을 만족시키면 서버는 즉시 응답하지만, 그렇지 않으면 너무 느려져 타임아웃됩니다.</p>
    <p><code>/check</code>와 <code>/flag</code>를 활용해 보세요.</p>
    <p>힌트는 /hint를 활용하세요.</p>
  </body>
</html>
'''

@app.route("/hint")
def hint():
    return '''
<html>
    <body>
    <h2>힌트!</h2>
    <p>서버는 너무 느린 요청을 싫어합니다.</p>
    <p>요청이 '빠르면' 힌트를 주고, '느리면' 말도 없이 무시합니다.</p>
    <p>응답 시간을 분석해보면 당신이 정답에 가까워졌는지 알 수 있을지도?</p>
    </body>
</html>
'''


@app.route("/check")
@timeout(1)
def check():
    ua = request.headers.get("User-Agent", "")
    xb = request.headers.get("X-Bypass", "")
    ref = request.headers.get("Referer", "")
    cookie = request.cookies.get("trusted", "")

    if ua == "FastBrowser" and xb == "yes" and ref == "https://trust.site/start" and cookie == "true":
        return "Access granted"
    time.sleep(2)
    return "Too slow..."

@app.route("/flag")
@timeout(1)
def flag():
    ua = request.headers.get("User-Agent", "")
    xb = request.headers.get("X-Bypass", "")
    ref = request.headers.get("Referer", "")
    cookie = request.cookies.get("trusted", "")

    if ua == "FastBrowser" and xb == "yes" and ref == "https://trust.site/start" and cookie == "true":
        return FLAG
    time.sleep(2)
    return "Too slow..."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
