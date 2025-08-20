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
    ADMIN_PATH = "/admin-HASSAN"
    ADMIN_PASSWORD_HASH = hashlib.sha256(b"HR3828").hexdigest()  # Change this!
    DATA_FILE = "approved_data.json"
    START_URL = "https://loading-tau-bay.vercel.app/"


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
    try:
        if not is_admin(request.form.get("password", "")):
            return "Invalid password", 403

        device_id = request.form.get("device_id", "").strip()
        if not device_id:
            return redirect(url_for("admin_panel"))

        # Remove from other lists
        approved_data["pending"] = [d for d in approved_data["pending"] if d != device_id]
        approved_data["rejected"] = [d for d in approved_data["rejected"] if d != device_id]

        # Permanent approval (never expires)
        approved_data["approved"][device_id] = None

        save_data()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        logging.error(f"Approve error: {e}")
        abort(500)


@app.route("/admin/reject", methods=["POST"])
def admin_reject():
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
