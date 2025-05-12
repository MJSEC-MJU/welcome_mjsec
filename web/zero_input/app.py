from flask import Flask, request, make_response, render_template
import hashlib
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def load_secret_salt():
    try:
        with open("secret_salt.txt") as f:
            return f.read().strip()
    except:
        return None

SECRET_SALT = load_secret_salt()

def gen_random_id(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def hash_id(id_val):
    return hashlib.sha256((id_val + SECRET_SALT).encode()).hexdigest()

@app.route("/")
def index():
    user_id = request.cookies.get("id")
    if not user_id:
        user_id = gen_random_id()
    resp = make_response(render_template("index.html"))
    resp.set_cookie("id", user_id)
    return resp

@app.route("/reveal")
def reveal():
    user_id = request.cookies.get("id", "")
    if hash_id(user_id).endswith("00"):
        try:
            with open("flag.txt") as f:
                return f.read().strip()
        except:
            return "Flag unavailable on this server."
    return "You are not the chosen one."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
