from flask import Flask, render_template, request, abort

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/secret-area")
def secret_area():
    return render_template("secret.html")

@app.route("/real-way-here/flag")
def final_flag():
    code = request.args.get("code", "")
    if code == "123":
        return "MJSEC{c0mm3nts_r3v34l_m0r3}"
    return {"status": "wrong code", "hint": "follow the trail exactly"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
