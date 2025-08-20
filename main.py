import os
import hashlib
import uuid
import logging
import requests
from flask import Flask, request, redirect, url_for, render_template, make_response, abort

# ====================================================
# CONFIGURATION
# ====================================================
class Config:
    ADMIN_PATH = "/admin-HASSAN"
    ADMIN_PASSWORD_HASH = hashlib.sha256(b"HR3828").hexdigest()  # Change this!
    APPROVAL_URL = "https://raw.githubusercontent.com/linelightinfo-commits/Test/main/approvel.txt"
    START_URL = "https://loading-tau-bay.vercel.app/"


# ====================================================
# APP SETUP
# ====================================================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ====================================================
# DATA HANDLING (Load approved list from GitHub)
# ====================================================
def load_approved_ids():
    try:
        r = requests.get(Config.APPROVAL_URL, timeout=5)
        if r.status_code == 200:
            return set(line.strip() for line in r.text.splitlines() if line.strip())
    except Exception as e:
        logging.error(f"Error fetching approvals: {e}")
    return set()


def is_admin(password: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == Config.ADMIN_PASSWORD_HASH


# ====================================================
# HELPERS
# ====================================================
def get_device_id():
    device_id = request.cookies.get("device_id")
    if device_id:
        return device_id

    new_id = str(uuid.uuid4())
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie("device_id", new_id, max_age=60*60*24*365*10)  # 10 years
    return new_id


# ====================================================
# ROUTES
# ====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    try:
        device_id = request.cookies.get("device_id")
        if not device_id:
            device_id = str(uuid.uuid4())

        # Get latest approved list from GitHub
        approved_ids = load_approved_ids()

        if device_id in approved_ids:
            status = "approved"
        else:
            status = "rejected"  # sirf GitHub wali list se approval milega

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

            approved_ids = load_approved_ids()
            return render_template("admin.html",
                                   logged_in=True,
                                   approved=list(approved_ids),
                                   admin_password=request.form.get("password"))
        return render_template("admin.html", logged_in=False)
    except Exception as e:
        logging.error(f"Admin panel error: {e}")
        abort(500)


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
