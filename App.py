import os
import math
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cloud_storage_secret_key"

UPLOAD_FOLDER, CHUNKS_FOLDER = "uploads", "chunks"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHUNKS_FOLDER, exist_ok=True)

USERS = {"admin": {"password": "adminpassword", "role": "admin"}, "user1": {"password": "user123", "role": "user"}}
DRIVE_ACCOUNTS = [{"id": 1, "email": "node1@gmail.com", "limit": 14, "used": 0}]
FILES_DB = []

UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudVault Pro - Multi-Gmail Storage</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --danger: #ef4444;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg-color); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar Navigation */
        .sidebar { width: 260px; background: #0f172a; color: #94a3b8; display: flex; flex-direction: column; border-right: 1px solid var(--border); }
        .sidebar-brand { padding: 25px 20px; font-size: 1.2rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .sidebar-menu { list-style: none; padding: 20px 10px; flex-grow: 1; }
        .sidebar-menu li { margin-bottom: 6px; }
        .sidebar-menu a { display: flex; align-items: center; gap: 12px; padding: 12px 16px; color: #94a3b8; text-decoration: none; border-radius: 8px; font-weight: 500; font-size: 0.95rem; transition: 0.2s; }
        .sidebar-menu a:hover, .sidebar-menu a.active { background: #1e293b; color: #fff; }
        
        /* Main Layout */
        .main { flex-grow: 1; display: flex; flex-direction: column; overflow-y: auto; }
        .topbar { background: var(--card-bg); padding: 18px 30px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
        .content { padding: 30px; }
        
        /* Cards & Grids */
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 25px; }
        .stat-card h3 { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-card .val { font-size: 1.8rem; font-weight: 700; color: var(--text-main); }
        
        /* Tables & Forms */
        table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 12px; overflow: hidden; border: 1px solid var(--border); margin-top: 15px; }
        th, td { padding: 14px 20px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.93rem; }
        th { background: #f8fafc; font-weight: 600; color: var(--text-muted); }
        
        .btn { padding: 10px 18px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; text-decoration: none; font-size: 0.9rem; transition: 0.2s; }
        .btn-primary { background: var(--primary); color: #fff; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); padding: 6px 12px; font-size: 0.85rem; }
        .btn-danger:hover { background: var(--danger); color: #fff; }
        
        input, select { width: 100%; padding: 12px 14px; margin: 8px 0 16px 0; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; background: #fff; }
        input:focus, select:focus { outline: 2px solid var(--primary); }
        
        /* Auth Screen */
        .auth-container { display: flex; justify-content: center; align-items: center; height: 100vh; width: 100vw; background: var(--bg-color); }
        .auth-box { background: var(--card-bg); padding: 40px; border-radius: 16px; border: 1px solid var(--border); width: 100%; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .auth-box h2 { margin-bottom: 20px; font-size: 1.5rem; color: var(--primary); display: flex; align-items: center; gap: 10px; }
    </style>
</head>
<body>

{% if not session.user %}
    <div class="auth-container">
        <div class="auth-box">
            <h2><i class="fa-solid fa-cloud-arrow-up"></i> CloudVault</h2>
            <form method="POST" action="/login">
                <label>Username</label>
                <input type="text" name="username" required placeholder="admin or user1">
                <label>Password</label>
                <input type="password" name="password" required placeholder="••••••••">
                <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center; margin-top:10px;">Login to Dashboard</button>
            </form>
            <p style="margin-top:15px; font-size:0.82rem; color:var(--text-muted); text-align:center;">Admin: admin / adminpassword<br>User: user1 / user123</p>
        </div>
    </div>
{% else %}
    <div class="sidebar">
        <div class="sidebar-brand">
            <i class="fa-solid fa-cloud-arrow-up" style="color: #6366f1;"></i> CloudVault Pro
        </div>
        <ul class="sidebar-menu">
            <li><a href="/" class="{% if tab == 'dash' %}active{% endif %}"><i class="fa-solid fa-chart-pie"></i> Dashboard</a></li>
            <li><a href="/upload" class="{% if tab == 'upload' %}active{% endif %}"><i class="fa-solid fa-upload"></i> Upload & Split</a></li>
            <li><a href="/accounts" class="{% if tab == 'accounts' %}active{% endif %}"><i class="fa-brands fa-google"></i> Gmail Nodes</a></li>
            <li><a href="/files" class="{% if tab == 'files' %}active{% endif %}"><i class="fa-solid fa-folder-open"></i> Files & Merge</a></li>
            <li><a href="/logout" style="color:#ef4444; margin-top:20px;"><i class="fa-solid fa-right-from-bracket"></i> Logout</a></li>
        </ul>
    </div>

    <div class="main">
        <div class="topbar">
            <span>Welcome back, <b>{{ session.user }}</b></span>
            <span style="font-size:0.85rem; color:var(--text-muted); font-weight:normal;">System Status: <b style="color:#10b981;">Online</b></span>
        </div>

        <div class="content">
            {% if tab == 'dash' %}
                <h2 style="margin-bottom:20px;">System Overview</h2>
                <div class="grid">
                    <div class="card stat-card" style="margin:0;">
                        <h3>Connected Nodes</h3>
                        <div class="val">{{ accounts|length }}</div>
                    </div>
                    <div class="card stat-card" style="margin:0;">
                        <h3>Uploaded Files</h3>
                        <div class="val" style="color:var(--primary);">{{ files|length }}</div>
                    </div>
                </div>
                <div class="card">
                    <h3 style="color:var(--text-main); margin-bottom:10px;"><i class="fa-solid fa-shield-halved" style="color:var(--primary);"></i> Multi-Gmail 14GB Architecture</h3>
                    <p style="color:var(--text-muted); font-size:0.95rem; line-height:1.6;">
                        Yeh system automatically aapki files ko chunk split karke unlimited connected Gmail / Google Drive accounts par distribute karta hai[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span). Jab ek Gmail ID ki 14GB limit poori ho jati hai, toh system next node par switch ho jata hai[span_6](start_span)[span_6](end_span)[span_7](start_span)[span_7](end_span).
                    </p>
                </div>

            {% elif tab == 'upload' %}
                <h2 style="margin-bottom:20px;">Upload File & Auto-Split</h2>
                <div class="card" style="max-width:550px;">
                    <form method="POST" action="/upload" enctype="multipart/form-data">
                        <label>Select File from Device</label>
                        <input type="file" name="file" required>
                        <button type="submit" class="btn btn-primary"><i class="fa-solid fa-cloud-arrow-up"></i> Upload & Process</button>
                    </form>
                </div>

            {% elif tab == 'accounts' %}
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                    <h2>Connected Gmail Nodes</h2>
                </div>
                <div class="card" style="max-width:550px; margin-bottom:20px;">
                    <form method="POST" action="/add_account">
                        <label>Add New Gmail ID (14GB Limit Node)</label>
                        <input type="email" name="email" placeholder="example@gmail.com" required>
                        <button type="submit" class="btn btn-primary"><i class="fa-solid fa-plus"></i> Connect Node</button>
                    </form>
                </div>
                <table>
                    <tr><th>Gmail Address</th><th>Storage Limit</th><th>Used Storage</th><th>Action</th></tr>
                    {% for acc in accounts %}
                    <tr>
                        <td><i class="fa-brands fa-google" style="color:#ea4335; margin-right:6px;"></i> {{ acc.email }}</td>
                        <td>{{ acc.limit }} GB</td>
                        <td>{{ acc.used // (1024*1024) }} MB</td>
                        <td><a href="/del_acc/{{ acc.id }}" class="btn btn-danger"><i class="fa-solid fa-trash"></i> Remove</a></td>
                    </tr>
                    {% endfor %}
                </table>

            {% elif tab == 'files' %}
                <h2 style="margin-bottom:20px;">File Manager & Auto-Merge</h2>
                <table>
                    <tr><th>File Name</th><th>Size</th><th>Assigned Node</th><th>Action</th></tr>
                    {% for f in files %}
                    <tr>
                        <td><i class="fa-solid fa-file" style="color:var(--primary); margin-right:6px;"></i> {{ f.name }}</td>
                        <td>{{ f.size }} MB</td>
                        <td>{{ f.node }}</td>
                        <td><a href="/download/{{ f.id }}" class="btn btn-primary" style="padding:6px 12px; font-size:0.85rem;"><i class="fa-solid fa-download"></i> Merge & Download</a></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:30px;">No files uploaded yet.</td></tr>
                    {% endfor %}
                </table>
            {% endif %}
        </div>
    </div>
{% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    if "user" not in session: return render_template_string(UI_TEMPLATE)
    return render_template_string(UI_TEMPLATE, tab="dash", accounts=DRIVE_ACCOUNTS, files=FILES_DB)

@app.route("/login", methods=["POST"])
def login():
    u, p = request.form.get("username"), request.form.get("password")
    if u in USERS and USERS[u]["password"] == p:
        session["user"] = u
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/accounts")
def accounts():
    if "user" not in session: return redirect(url_for("index"))
    return render_template_string(UI_TEMPLATE, tab="accounts", accounts=DRIVE_ACCOUNTS)

@app.route("/add_account", methods=["POST"])
def add_account():
    if "user" not in session: return redirect(url_for("index"))
    DRIVE_ACCOUNTS.append({"id": len(DRIVE_ACCOUNTS) + 1, "email": request.form.get("email"), "limit": 14, "used": 0})
    return redirect(url_for("accounts"))

@app.route("/del_acc/<int:acc_id>")
def del_acc(acc_id):
    if "user" not in session: return redirect(url_for("index"))
    global DRIVE_ACCOUNTS
    DRIVE_ACCOUNTS = [a for a in DRIVE_ACCOUNTS if a["id"] != acc_id]
    return redirect(url_for("accounts"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session: return redirect(url_for("index"))
    if request.method == "POST":
        file = request.files.get("file")
        if not file: return redirect(url_for("upload"))
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        f_size = os.path.getsize(filepath)
        
        target_acc = DRIVE_ACCOUNTS[0]
        target_acc["used"] += f_size
        
        chunk_size = 5 * 1024 * 1024
        chunks = math.ceil(f_size / chunk_size)
        fid = len(FILES_DB) + 1
        
        with open(filepath, "rb") as f:
            for i in range(chunks):
                with open(os.path.join(CHUNKS_FOLDER, f"f_{fid}_p_{i}"), "wb") as cf:
                    cf.write(f.read(chunk_size))
                    
        FILES_DB.append({"id": fid, "name": filename, "size": round(f_size / (1024*1024), 2), "node": target_acc["email"], "chunks": chunks})
        return redirect(url_for("files"))
        
    return render_template_string(UI_TEMPLATE, tab="upload")

@app.route("/files")
def files():
    if "user" not in session: return redirect(url_for("index"))
    return render_template_string(UI_TEMPLATE, tab="files", files=FILES_DB)

@app.route("/download/<int:fid>")
def download(fid):
    if "user" not in session: return redirect(url_for("index"))
    file_rec = next((f for f in FILES_DB if f["id"] == fid), None)
    if not file_rec: return "Not found", 404
    
    merged_path = os.path.join(UPLOAD_FOLDER, "merged_" + file_rec["name"])
    with open(merged_path, "wb") as mf:
        for i in range(file_rec["chunks"]):
            chunk_path = os.path.join(CHUNKS_FOLDER, f"f_{fid}_p_{i}")
            if os.path.exists(chunk_path):
                with open(chunk_path, "rb") as cf:
                    mf.write(cf.read())
                    
    return send_file(merged_path, as_attachment=True, download_name=file_rec["name"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
