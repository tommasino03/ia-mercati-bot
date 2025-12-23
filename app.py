from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route("/")
def home():
    try:
        with open("signals.json", "r") as f:
            report = json.load(f)
    except:
        report = {"error": "Nessun report disponibile"}
    return render_template("index.html", report=report)

@app.route("/api")
def api():
    try:
        with open("signals.json", "r") as f:
            report = json.load(f)
    except:
        report = {"error": "Nessun report disponibile"}
    return jsonify(report)

if __name__ == "__main__":
    app.run(debug=True)
