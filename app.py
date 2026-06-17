import http.server
import json
import sqlite3
import urllib.parse
from datetime import datetime

DB_FILE = "api_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM profiles")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO profiles (name, role, timestamp) VALUES (?, ?, ?)",
            ("Christian Dale Ferolino", "Coder", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    conn.commit()
    conn.close()

# Frontend HTML UI
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Profiles</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 20px; color: #333; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        h1, h2 { color: #007bff; }
        input, button { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
        .profile-item { background: #f8f9fa; padding: 12px; border-left: 4px solid #007bff; margin-bottom: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dashboard</h1>
        <div class="card">
            <h2>Add New Profile</h2>
            <input type="text" id="name" placeholder="Name">
            <input type="text" id="role" placeholder="Role">
            <button onclick="submitProfile()">Save Profile</button>
        </div>
        <div class="card">
            <h2>Current Profiles</h2>
            <div id="profiles-list">Loading profiles...</div>
        </div>
    </div>
    <script>
        async function loadProfiles() {
            const res = await fetch('/search');
            const data = await res.json();
            const list = document.getElementById('profiles-list');
            list.innerHTML = data.length ? '' : 'No profiles found.';
            data.forEach(p => {
                list.innerHTML += `<div class="profile-item"><strong>${p.name}</strong> - ${p.role} <br><small style="color:gray">${p.timestamp}</small></div>`;
            });
        }
        async function submitProfile() {
            const name = document.getElementById('name').value;
            const role = document.getElementById('role').value;
            if (!name || !role) return alert('Fill all fields');
            await fetch('/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, role })
            });
            document.getElementById('name').value = '';
            document.getElementById('role').value = '';
            loadProfiles();
        }
        loadProfiles();
    </script>
</body>
</html>
"""

class AdvancedAPIHandler(http.server.BaseHTTPRequestHandler):
    def _send_response(self, data, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        if isinstance(data, str):
            self.wfile.write(data.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/":
            self._send_response(FRONTEND_HTML, 200, "text/html")
        elif parsed_url.path == "/search":
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT name, role, timestamp FROM profiles")
            rows = cursor.fetchall()
            conn.close()
            results = [{"name": row[0], "role": row[1], "timestamp": row[2]} for row in rows]
            self._send_response(results)
        else:
            self._send_response({"error": "Not found"}, 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/submit":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                name, role = data.get("name"), data.get("role")
                if not name or not role:
                    self._send_response({"error": "Missing data"}, 400)
                    return
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO profiles (name, role, timestamp) VALUES (?, ?, ?)",
                               (name, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                self._send_response({"status": "success"})
            except json.JSONDecodeError:
                self._send_response({"error": "Invalid JSON"}, 400)

if __name__ == "__main__":
    init_db()
    print("Fullstack App running at http://localhost:8080")
    http.server.HTTPServer(("", 8080), AdvancedAPIHandler).serve_forever()
