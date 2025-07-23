import os
import hashlib
import uuid
from flask import Flask, request, redirect, url_for, render_template_string, make_response
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# ================= CONFIGURATION =================
ADMIN_PATH = "/admin-faizi-panel-1000000100003737"
ADMIN_PASSWORD = "TH3 L3G3ND GABGST3R AND STUN3R"  # Change this!
DATA_FILE = "approved_data.json"
START_URL = "https://faiizuapk.unaux.com/"

# ================= HTML TEMPLATES =================
# [Previous HOME_PAGE template remains exactly the same...]

ADMIN_PANEL = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TERROR APK - Admin Panel</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #ff3366;
            --secondary: #f85a40;
            --dark: #111;
            --light: #f8f9fa;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--dark);
            color: white;
            margin: 0;
            padding: 20px;
            background-image: radial-gradient(circle at 10% 20%, rgba(248, 90, 64, 0.1) 0%, rgba(17, 17, 17, 1) 90%);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        h1 {
            color: var(--primary);
            margin-bottom: 10px;
        }
        .logout {
            float: right;
            color: #aaa;
            text-decoration: none;
            font-size: 0.9rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(30, 30, 30, 0.7);
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        th {
            background: rgba(248, 90, 64, 0.2);
            color: var(--primary);
            font-weight: 600;
        }
        tr:hover {
            background: rgba(255, 255, 255, 0.03);
        }
        .status {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-pending {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
        }
        .status-approved {
            background: rgba(40, 167, 69, 0.2);
            color: #28a745;
        }
        .status-rejected {
            background: rgba(220, 53, 69, 0.2);
            color: #dc3545;
        }
        .action-btn {
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 3px;
            font-size: 0.8rem;
            transition: all 0.2s;
        }
        .approve-btn {
            background: #28a745;
            color: white;
        }
        .reject-btn {
            background: #dc3545;
            color: white;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }
        .login-form {
            max-width: 400px;
            margin: 50px auto;
            background: rgba(30, 30, 30, 0.9);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }
        .login-form input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            color: white;
        }
        .login-form button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        .count {
            font-size: 0.9rem;
            color: #aaa;
            margin: 5px 0;
        }
        .time-selection {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .time-option {
            flex: 1;
        }
        .time-option input {
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            color: white;
        }
        .expires {
            font-size: 0.8rem;
            color: #aaa;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-form">
        <h2><i class="fas fa-lock"></i> Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter admin password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    {% else %}
    <div class="header">
        <a href="/" class="logout"><i class="fas fa-sign-out-alt"></i> Back to Home</a>
        <h1><i class="fas fa-user-shield"></i> TERROR APK ADMIN PANEL</h1>
        <p>Manage device approvals and access</p>
    </div>

    <h2><i class="fas fa-clock"></i> Pending Approvals</h2>
    <p class="count">{{ pending|length }} devices waiting</p>
    <table>
        <thead>
            <tr>
                <th>Device ID</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for device in pending %}
            <tr>
                <td>{{ device }}</td>
                <td><span class="status status-pending">PENDING</span></td>
                <td>
                    <form method="POST" action="/admin/approve" style="display: inline;">
                        <input type="hidden" name="device_id" value="{{ device }}">
                        <input type="hidden" name="password" value="{{ admin_password }}">
                        <div class="time-selection">
                            <div class="time-option">
                                <label>Minutes</label>
                                <input type="number" name="minutes" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Hours</label>
                                <input type="number" name="hours" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Days</label>
                                <input type="number" name="days" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Months</label>
                                <input type="number" name="months" placeholder="0" min="0">
                            </div>
                        </div>
                        <button type="submit" class="action-btn approve-btn"><i class="fas fa-check"></i> Approve</button>
                    </form>
                    <form method="POST" action="/admin/reject" style="display: inline;">
                        <input type="hidden" name="device_id" value="{{ device }}">
                        <input type="hidden" name="password" value="{{ admin_password }}">
                        <button type="submit" class="action-btn reject-btn"><i class="fas fa-times"></i> Reject</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" style="text-align: center;">No pending devices</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2><i class="fas fa-check-circle"></i> Approved Devices</h2>
    <p class="count">{{ approved|length }} approved devices</p>
    <table>
        <thead>
            <tr>
                <th>Device ID</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for device, expires in approved.items() %}
            <tr>
                <td>{{ device }}</td>
                <td><span class="status status-approved">APPROVED</span></td>
                <td class="expires">
                    {% if expires %}
                        {{ expires }}
                    {% else %}
                        Never
                    {% endif %}
                </td>
                <td>
                    <form method="POST" action="/admin/reject" style="display: inline;">
                        <input type="hidden" name="device_id" value="{{ device }}">
                        <input type="hidden" name="password" value="{{ admin_password }}">
                        <button type="submit" class="action-btn reject-btn"><i class="fas fa-times"></i> Revoke</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="4" style="text-align: center;">No approved devices</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <h2><i class="fas fa-times-circle"></i> Rejected Devices</h2>
    <p class="count">{{ rejected|length }} rejected devices</p>
    <table>
        <thead>
            <tr>
                <th>Device ID</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for device in rejected %}
            <tr>
                <td>{{ device }}</td>
                <td><span class="status status-rejected">REJECTED</span></td>
                <td>
                    <form method="POST" action="/admin/approve" style="display: inline;">
                        <input type="hidden" name="device_id" value="{{ device }}">
                        <input type="hidden" name="password" value="{{ admin_password }}">
                        <div class="time-selection">
                            <div class="time-option">
                                <label>Minutes</label>
                                <input type="number" name="minutes" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Hours</label>
                                <input type="number" name="hours" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Days</label>
                                <input type="number" name="days" placeholder="0" min="0">
                            </div>
                            <div class="time-option">
                                <label>Months</label>
                                <input type="number" name="months" placeholder="0" min="0">
                            </div>
                        </div>
                        <button type="submit" class="action-btn approve-btn"><i class="fas fa-check"></i> Approve</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" style="text-align: center;">No rejected devices</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</body>
</html>
"""

# ================= APPLICATION CODE =================
# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        approved_data = json.load(f)
else:
    approved_data = {
        "approved": {},  # Now a dict with device_id: expiration_time
        "pending": [],
        "rejected": [],
        "permanent_ids": {}
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(approved_data, f, indent=4)

def get_permanent_device_id():
    """Generate a device ID that persists across browsers/reinstalls"""
    # Create a fingerprint from available hardware/browser data
    fingerprint_parts = [
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
        str(uuid.getnode())  # MAC address (works on Android)
    ]
    fingerprint = "|".join(filter(None, fingerprint_parts))
    fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()
    
    # Return existing ID or create new one
    if fingerprint_hash in approved_data["permanent_ids"]:
        return approved_data["permanent_ids"][fingerprint_hash]
    
    new_id = str(uuid.uuid4())
    approved_data["permanent_ids"][fingerprint_hash] = new_id
    save_data()
    return new_id

def check_expirations():
    """Check and remove expired approvals"""
    current_time = datetime.now().isoformat()
    expired_devices = []
    
    for device_id, expires in approved_data["approved"].items():
        if expires and expires < current_time:
            expired_devices.append(device_id)
    
    for device_id in expired_devices:
        approved_data["approved"].pop(device_id)
        if device_id not in approved_data["rejected"]:
            approved_data["rejected"].append(device_id)
    
    if expired_devices:
        save_data()

@app.route("/", methods=["GET", "POST"])
def index():
    check_expirations()  # Check for expired approvals on each request
    
    device_id = request.cookies.get("device_id") or get_permanent_device_id()
    
    if request.method == "POST":
        if (device_id not in approved_data["approved"] and 
            device_id not in approved_data["pending"] and 
            device_id not in approved_data["rejected"]):
            approved_data["pending"].append(device_id)
            save_data()
        
        resp = make_response(redirect(url_for("index")))
        resp.set_cookie("device_id", device_id, max_age=60*60*24*365*10)  # 10 years
        return resp

    # Determine status
    if device_id in approved_data["approved"]:
        status = "approved"
    elif device_id in approved_data["pending"]:
        status = "pending"
    elif device_id in approved_data["rejected"]:
        status = "rejected"
    else:
        status = "new"

    return render_template_string(HOME_PAGE, 
                               device_id=device_id,
                               status=status,
                               start_url=START_URL)

@app.route(ADMIN_PATH, methods=["GET", "POST"])
def admin_panel():
    # Password protection
    if request.method == "POST" and "password" in request.form:
        password = request.form.get("password")
        if password != ADMIN_PASSWORD:
            return render_template_string(ADMIN_PANEL, logged_in=False)
        
        # If password correct, show admin panel
        return render_template_string(ADMIN_PANEL,
                                   logged_in=True,
                                   pending=approved_data["pending"],
                                   approved=approved_data["approved"],
                                   rejected=approved_data["rejected"],
                                   admin_password=ADMIN_PASSWORD)
    
    # For GET requests, show login form
    return render_template_string(ADMIN_PANEL, logged_in=False)

@app.route("/admin/approve", methods=["POST"])
def admin_approve():
    if request.form.get("password") != ADMIN_PASSWORD:
        return "Invalid password", 403
        
    device_id = request.form.get("device_id", "").strip()
    if device_id:
        # Calculate expiration time
        minutes = int(request.form.get("minutes", 0))
        hours = int(request.form.get("hours", 0))
        days = int(request.form.get("days", 0))
        months = int(request.form.get("months", 0))
        
        if minutes or hours or days or months:
            expires = datetime.now() + timedelta(
                minutes=minutes,
                hours=hours,
                days=days + (months * 30)  # Approximate months to days
            )
            expires_str = expires.isoformat()
        else:
            expires_str = None  # Permanent approval
        
        # Move between lists
        if device_id in approved_data["pending"]:
            approved_data["pending"].remove(device_id)
        if device_id in approved_data["rejected"]:
            approved_data["rejected"].remove(device_id)
        
        approved_data["approved"][device_id] = expires_str
        save_data()
    return redirect(url_for("admin_panel"))

@app.route("/admin/reject", methods=["POST"])
def admin_reject():
    if request.form.get("password") != ADMIN_PASSWORD:
        return "Invalid password", 403
        
    device_id = request.form.get("device_id", "").strip()
    if device_id:
        # Move between lists
        if device_id in approved_data["pending"]:
            approved_data["pending"].remove(device_id)
        if device_id in approved_data["approved"]:
            approved_data["approved"].pop(device_id)
        if device_id not in approved_data["rejected"]:
            approved_data["rejected"].append(device_id)
        save_data()
    return redirect(url_for("admin_panel"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
