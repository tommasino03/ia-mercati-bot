from flask import Flask, render_template_string, jsonify
import json

app = Flask(__name__)

# HTML direttamente dentro il codice
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Segnali Mercati</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .compra { color: green; font-weight: bold; }
        .vendi { color: red; font-weight: bold; }
        .neutro { color: gray; }
        .asset { border-bottom: 1px solid #ccc; margin-bottom: 10px; padding-bottom: 5px; }
    </style>
</head>
<body>
    <h1>Segnali Mercati</h1>
    {% for a in report %}
        <div class="asset">
            <h3>{{ a.ticker }}</h3>
            <p>Breve: <span class="{{ 'compra' if a.breve=='✅ COMPRA' else 'vendi' if a.breve=='❌ VENDI' else 'neutro' }}">{{ a.breve }}</span></p>
            <p>Medio: <span class="{{ 'compra' if a.medio=='✅ COMPRA' else 'vendi' if a.medio=='❌ VENDI' else 'neutro' }}">{{ a.medio }}</span></p>
            <p>Lungo: <span class="{{ 'compra' if a.lungo=='✅ INVESTI' else 'vendi' if a.lungo=='❌ VENDI' else 'neutro' }}">{{ a.lungo }}</span></p>
            <p>Motivo: {{ a.motivo }}</p>
        </div>
    {% endfor %}
</body>
</html>
"""

@app.route("/")
def home():
    try:
        with open("signals.json", "r") as f:
            report = json.load(f)
    except:
        report = []
    return render_template_string(HTML, report=report)

@app.route("/api")
def api():
    try:
        with open("signals.json", "r") as f:
            report = json.load(f)
    except:
        report = []
    return jsonify(report)

if __name__ == "__main__":
    app.run(debug=True)
