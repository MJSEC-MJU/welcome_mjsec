from flask import Flask, request, make_response, render_template_string
import json

app = Flask(__name__)
PORT = 8001

FLAG_PATH = os.path.join(os.path.dirname(__file__), 'FLAG.txt')
with open(FLAG_PATH) as f:
    FLAG = f.read().strip())
with open('path.txt') as f:
    correct_path = [line.strip() for line in f if line.strip()]

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Knight’s Journey</title>
  <style>
    body {
      background-color: #fffdfa;
      font-family: 'Times New Roman', serif;
      max-width: 700px;
      margin: 60px auto;
      padding: 30px;
      border: 1px solid #aaa;
      border-radius: 12px;
    }
    h1 {
      text-align: center;
      color: #3a3a3a;
    }
    p {
      line-height: 1.6;
    }
    code {
      background-color: #eee;
      padding: 3px 6px;
      border-radius: 4px;
      font-size: 1.05em;
    }
  </style>
</head>
<body>
  <h1>Knight’s Journey</h1>
  <p>
    The Knight begins his journey across the board.
    His steps must follow the sacred L-shape — two steps in one direction, one in another.
  </p>
  <p>
    Use this format to move:<br>
    <code>/knight?move=G1</code>
  </p>
  <p>
    Your path is remembered in silence.  
    The wrong move shall end your journey without mercy.
  </p>
  <p>
    Will you reach the final square?
  </p>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/knight")
def knight():
    move = request.args.get("move")
    if not move:
        return "Missing move parameter.", 400

    journey_cookie = request.cookies.get("journey")
    journey = []

    if journey_cookie:
        try:
            journey = json.loads(journey_cookie)
        except:
            return "Invalid journey cookie.", 400

    def is_valid_knight_move(from_pos, to_pos):
        if not from_pos or len(from_pos) != 2 or len(to_pos) != 2:
            return False
        fx, fy = ord(from_pos[0]), int(from_pos[1])
        tx, ty = ord(to_pos[0]), int(to_pos[1])
        dx, dy = abs(fx - tx), abs(fy - ty)
        return (dx == 2 and dy == 1) or (dx == 1 and dy == 2)

    if journey and not is_valid_knight_move(journey[-1], move):
        return "The Knight stumbles.", 403

    journey.append(move)
    resp = make_response()
    resp.set_cookie("journey", json.dumps(journey), httponly=True)

    if journey == correct_path:
        resp.set_data(f"The Knight has reached the end. FLAG: {FLAG}")
    else:
        resp.set_data(f"Moved to {move}. The path continues...")

    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
