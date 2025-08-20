import os
import hashlib
import uuid
import json
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, render_template, make_response, abort

# ====================================================
# CONFIGURATION
# ====================================================
class Config:
    ADMIN_PATH = "/admin-HASSAN"
    ADMIN_PASSWORD_HASH = hashlib.sha256(b"HR3828").hexdigest()  # Change this!
    DATA_FILE = "approved_data.json"
    START_URL = "https://loading-tau-bay.vercel.app/"
    APPROVAL_FILE_URL = "https://raw.githubusercontent.com/linelightinfo-commits/Test/main/approvel.txt"


# ====================================================
# APP SETUP
# ====================================================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ====================================================
# DATA HANDLING
# ====================================================
def load_data():
    if os.path.exists(Config.DATA_FILE):
        try:
            with open(Config.DATA_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data.get("approved"), list):
                    data["approved"] = {d: None for d in data["approved"]}
                return data
        except Exception as e:
            logging.error(f"Error loading data: {e}")

    return {"approved": {}, "pending": [], "rejected": []}


def save_data():
    try:
        with open(Config.DATA_FILE, "w") as f:
            json.dump(approved_data, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving data: {e}")


approved_data = load_data()


# ====================================================
# HELPERS
# ====================================================
def fetch_approved_ids():
    """Fetch approved IDs directly from GitHub approvel.txt"""
    try:
        r = requests.get(Config.APPROVAL_FILE_URL, timeout=5)
        if r.status_code == 200:
            return {line.strip() for line in r.text.splitlines() if line.strip()}
    except Exception as e:
        logging.error(f"Error fetching approval file: {e}")
    return set()


def get_permanent_device_id():
    """Always return cookie-based device ID (does not change with IP/Network)."""
    device_id = request.cookies.get("device_id")
    if device_id:
        return device_id

    new_id = str(uuid.uuid4())
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("device_id", new_id, max_age=60*60*24*365*10)  # 10 years
    return new_id


def is_admin(password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == Config.ADMIN_PASSWORD_HASH


# ====================================================
# ROUTES
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    try:
        device_id = request.cookies.get("device_id")
        if not device_id:
            # create new ID if not exists
            device_id = str(uuid.uuid4())

        # fetch live approved list
        approved_ids = fetch_approved_ids()

        if device_id in approved_ids:
            status = "approved"
        else:
            status = "rejected"

        resp = make_response(render_template("home.html",
                               device_id=device_id,
                               status=status,
                               start_url=Config.START_URL))
        resp.set_cookie("device_id", device_id, max_age=60*60*24*365*10)
        return resp
    except Exception as e:
        logging.error(f"Index error: {e}")
        abort(500)


@app.route(Config.ADMIN_PATH, methods=["GET", "POST"])
def admin_panel():
    try:
        if request.method == "POST":
            if not is_admin(request.form.get("password", "")):
                return render_template("admin.html", logged_in=False)

            approved_ids = fetch_approved_ids()
            return render_template("admin.html",
                                   logged_in=True,
                                   pending=approved_data["pending"],
                                   approved=list(approved_ids),
                                   rejected=approved_data["rejected"],
                                   admin_password=request.form.get("password"))
        return render_template("admin.html", logged_in=False)
    except Exception as e:
        logging.error(f"Admin panel error: {e}")
        abort(500)


@app.route("/admin/approve", methods=["POST"])
def admin_approve():
    return "Approval is now managed only via approvel.txt file on GitHub.", 403


@app.route("/admin/reject", methods=["POST"])
def admin_reject():
    return "Rejection is now managed only via approvel.txt file on GitHub.", 403


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
