import os
import hashlib
import uuid
import json
import logging
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
    """Load approval data from JSON file and migrate old format."""
    if os.path.exists(Config.DATA_FILE):
        try:
            with open(Config.DATA_FILE, "r") as f:
                data = json.load(f)

            # --- Migrate old formats ---
            if isinstance(data.get("approved"), list):
                data["approved"] = {d: True for d in data["approved"]}

            if isinstance(data.get("approved"), dict):
                for dev, val in list(data["approved"].items()):
                    if val is None or isinstance(val, str):
                        data["approved"][dev] = True  # permanent

            if "pending" not in data: data["pending"] = []
            if "rejected" not in data: data["rejected"] = []
            if "permanent_ids" not in data: data["permanent_ids"] = {}

            with open(Config.DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

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


def is_admin(password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == Config.ADMIN_PASSWORD_HASH


# ====================================================
# ROUTES
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    try:
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

            # Build list of approved devices with status text
            approved_list = []
            for dev, val in approved_data["approved"].items():
                if val is True:
                    approved_list.append((dev, "Permanent ✅"))
                elif val is None:
                    approved_list.append((dev, "Permanent ✅"))
                else:
                    approved_list.append((dev, f"Expires: {val}"))

            return render_template("admin.html",
                                   logged_in=True,
                                   pending=approved_data["pending"],
                                   approved=approved_list,
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

        approved_data["pending"] = [d for d in approved_data["pending"] if d != device_id]
        approved_data["rejected"] = [d for d in approved_data["rejected"] if d != device_id]
        approved_data["approved"][device_id] = True

        save_data()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        logging.error(f"Approve error: {e}")
        abort(500)


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
                data["approved"] = {d: True for d in data["approved"]}

            if isinstance(data.get("approved"), dict):
                for dev, val in list(data["approved"].items()):
                    if val is None or isinstance(val, str):
                        data["approved"][dev] = True  # permanent

            if "pending" not in data: data["pending"] = []
            if "rejected" not in data: data["rejected"] = []
            if "permanent_ids" not in data: data["permanent_ids"] = {}

            with open(Config.DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

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


def is_admin(password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == Config.ADMIN_PASSWORD_HASH


# ====================================================
# ROUTES
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    try:
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
    try:
        if request.method == "POST":
            if not is_admin(request.form.get("password", "")):
                return render_template("admin.html", logged_in=False)

            approved_list = []
            for dev, val in approved_data["approved"].items():
                if val is True:
                    approved_list.append((dev, "Permanent ✅"))
                elif val is None:
                    approved_list.append((dev, "Permanent ✅"))
                else:
                    approved_list.append((dev, f"Expires: {val}"))

            return render_template("admin.html",
                                   logged_in=True,
                                   pending=approved_data["pending"],
                                   approved=approved_list,
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

        approved_data["pending"] = [d for d in approved_data["pending"] if d != device_id]
        approved_data["rejected"] = [d for d in approved_data["rejected"] if d != device_id]
        approved_data["approved"][device_id] = True

        save_data()
        return redirect(url_for("admin_panel"))
    except Exception as e:
        logging.error(f"Approve error: {e}")
        abort(500)


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
