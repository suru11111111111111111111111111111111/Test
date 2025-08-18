import os
import hashlib
import uuid
import json
import logging
from datetime import datetime, timedelta

from flask import Flask, request, redirect, url_for, render_template, make_response, abort

# ====================================================
# CONFIGURATION
# ====================================================
class Config:
    ADMIN_PATH = "/admin"
    ADMIN_PASSWORD_HASH = hashlib.sha256(b"FFF").hexdigest()  # Change this!
    DATA_FILE = "approved_data.json"
    START_URL = "https://faiizuapk.unaux.com/"


# ====================================================
# APP SETUP
# ====================================================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ====================================================
# DATA HANDLING
# ====================================================
def load_data():
    """Load approval data from JSON file."""
    if os.path.exists(Config.DATA_FILE):
        try:
            with open(Config.DATA_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data.get("approved"), list):
                    data["approved"] = {d: None for d in data["approved"]}
                return data
        except Exception as e:
            logging.error(f"Error loading data: {e}")

    return {"approved": {}, "pending": [], "rejected": [], "permanent_ids": {}}


def save_data():
    """Save approval data to JSON file."""
    try:
        with open(Config.DATA_FILE, "w") as f:
            json.dump(approved_data, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving data: {e}")


# Load initial data
approved_data = load_data()


# ====================================================
# HELPERS
# ====================================================
def get_permanent_device_id():
    """Generate a persistent device ID."""
    try:
        fingerprint_parts = [
            request.headers.get("User-Agent", ""),
            request.headers.get("Accept-Language", ""),
            str(uuid.getnode())
        ]
        fingerprint = "|".join(filter(None, fingerprint_parts))
        fingerprint_hash = hashlib.sha256(fingerprint.encode()).hexdigest()

        if fingerprint_hash in approved_data["permanent_ids"]:
            return approved_data["permanent_ids"][fingerprint_hash]

        new_id = str(uuid.uuid4())
        approved_data["permanent_ids"][fingerprint_hash] = new_id
        save_data()
        return new_id
    except Exception as e:
        logging.error(f"Error generating device ID: {e}")
        return str(uuid.uuid4())


def check_expirations():
    """Revoke expired approvals automatically."""
    try:
        now = datetime.now().isoformat()
        expired = [
            dev for dev, expires in approved_data["approved"].items()
            if expires and expires < now
        ]

        for dev in expired:
            approved_data["approved"].pop(dev, None)
            if dev not in approved_data["rejected"]:
                approved_data["rejected"].append(dev)

        if expired:
            save_data()
            logging.info(f"Expired devices revoked: {expired}")

    except Exception as e:
        logging.error(f"Error checking expirations: {e}")


def is_admin(password: str) -> bool:
    """Check if provided password matches admin password hash."""
    return hashlib.sha256(password.encode()).hexdigest() == Config.ADMIN_PASSWORD_HASH


# ====================================================
# ROUTES
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    """Main page: Show approval status or request approval."""
    try:
        check_expirations()
        device_id = request.cookies.get("device_id") or get_permanent_device_id()

        if request.method == "POST":
            if (device_id not in approved_data["approved"] and
                device_id not in approved_data["pending"] and
                device_id not in approved_data["rejected"]):
                approved_data["pending"].append(device_id)
                save_data()

            resp = make_response(redirect(url_for("index")))
            resp.set_cookie("device_id", device_id, max_age=60*60*24*365*10)
            return resp

        if device_id in approved_data["approved"]:
            status = "approved"
        elif device_id in approved_data["pending"]:
            status = "pending"
        elif device_id in approved_data["rejected"]:
            status = "rejected"
        else:
            status = "new"

        return render_template("home.html",
                               device_id=device_id,
                               status=status,
                               start_url=Config.START_URL)
    except Exception as e:
        logging.error(f"Index error: {e}")
        abort(500)


@app.route(Config.ADMIN_PATH, methods=["GET", "POST"])
def admin_panel():
    """Admin panel: login and manage approvals."""
    try:
        if request.method == "POST":
            if not is_admin(request.form.get("password", "")):
                return render_template("admin.html", logged_in=False)

            return render_template("admin.html",
                                   logged_in=True,
                                   pending=approved_data["pending"],
                                   approved=approved_data["approved"],
                                   rejected=approved_data["rejected"],
                                   admin_password=request.form.get("password"))
        return render_template("admin.html", logged_in=False)
    except Exception as e:
        logging.error(f"Admin panel error: {e}")
        abort(500)


@app.route("/admin/approve", methods=["POST"])
def admin_approve():
    """Approve a device with optional expiration."""
    try:
        if not is_admin(request.form.get("password", "")):
            return "Invalid password", 403

        device_id = request.form.get("device_id", "").strip()
        if not device_id:
            return redirect(url_for("admin_panel"))

        minutes = int(request.form.get("minutes", 0) or 0)
        hours = int(request.form.get("hours", 0) or 0)
        days = int(request.form.get("days", 0) or 0)
        months = int(request.form.get("months", 0) or 0)

        expires_str = None
        if any([minutes, hours, days, months]):
            expires = datetime.now() + timedelta(
                minutes=minutes, hours=hours, days=days + months * 30
            )
            expires_str = expires.isoformat()

        approved_data["pending"] = [d for d in approved_data["pending"] if d != device_id]
        approved_data["rejected"] = [d for d in approved_data["rejected"] if d != device_id]
        approved_data["approved"][device_id] = expires_str

        save_data()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        logging.error(f"Approve error: {e}")
        abort(500)


@app.route("/admin/reject", methods=["POST"])
def admin_reject():
    """Reject (or revoke) a device."""
    try:
        if not is_admin(request.form.get("password", "")):
            return "Invalid password", 403

        device_id = request.form.get("device_id", "").strip()
        if not device_id:
            return redirect(url_for("admin_panel"))

        approved_data["pending"] = [d for d in approved_data["pending"] if d != device_id]
        approved_data["approved"].pop(device_id, None)
        if device_id not in approved_data["rejected"]:
            approved_data["rejected"].append(device_id)

        save_data()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        logging.error(f"Reject error: {e}")
        abort(500)


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
