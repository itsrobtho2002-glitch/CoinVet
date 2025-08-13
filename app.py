from flask import Flask, render_template_string, request
from dotenv import load_dotenv
import os
from coin_vetter import analyze_contract

load_dotenv()

DEFAULT_CA = os.getenv("DEFAULT_CA", "").strip()

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Coin Vetter</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0d1117; color: #c9d1d9; text-align: center; }
        input, button { padding: 10px; margin: 5px; border-radius: 5px; }
        input { width: 350px; border: 1px solid #30363d; background:#161b22; color:#c9d1d9; }
        button { background: #238636; color: white; border: none; cursor: pointer; }
        button:hover { background: #2ea043; }
        table { margin: auto; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #30363d; padding: 10px; }
        th { background: #161b22; }
        .error { color: #ff7b72; }
    </style>
</head>
<body>
    <h1>Coin Vetter</h1>
    <form method="post">
        <input type="text" name="ca" placeholder="Enter Contract Address" value="{{ ca or '' }}" required>
        <button type="submit">Analyze</button>
    </form>
    {% if table %}
        <div>{{ table|safe }}</div>
    {% endif %}
</body>
</html>
"""

def render_table(result, ca):
    rows = [
        ["Contract Address", ca],
        ["Chain", result["chain_name"]],
        ["Buy-Zone", f"{result['buy_zone'][0]} — {result['buy_zone'][1]}"]
    ]
    if result["goplus"]:
        gp = result["goplus"]
        rows.extend([
            ["Liquidity (USD)", gp.get("liquidity_usd", "N/A")],
            ["Buy Tax (%)", gp.get("buy_tax", "N/A")],
            ["Sell Tax (%)", gp.get("sell_tax", "N/A")],
            ["Honeypot", gp.get("is_honeypot", "N/A")],
            ["Owner Renounced", gp.get("owner_renounced", "N/A")]
        ])
    if result["holders"]:
        top_holder = result["holders"][0]
        pct = top_holder.get("percentage") or top_holder.get("percent") or "N/A"
        rows.append(["Top Holder %", pct])

    table_html = "<table><tr><th>Metric</th><th>Value</th></tr>"
    for metric, value in rows:
        table_html += f"<tr><td>{metric}</td><td>{value}</td></tr>"
    table_html += "</table>"
    return table_html

@app.route("/", methods=["GET", "POST"])
def home():
    ca = ""
    table_html = None
    if request.method == "GET" and DEFAULT_CA:
        ca = DEFAULT_CA
        result = analyze_contract(ca)
        if isinstance(result, str):
            table_html = f"<p class='error'>{result}</p>"
        else:
            table_html = render_table(result, ca)
        return render_template_string(HTML_TEMPLATE, table=table_html, ca=ca)

    if request.method == "POST":
        ca = request.form["ca"].strip()
        try:
            result = analyze_contract(ca)
            if isinstance(result, str):
                table_html = f"<p class='error'>{result}</p>"
            else:
                table_html = render_table(result, ca)
        except Exception as e:
            table_html = f"<p class='error'>Error: {e}</p>"

    return render_template_string(HTML_TEMPLATE, table=table_html, ca=ca)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
