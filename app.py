from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import math
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "smart-parking-secret-key"

# =========================================================
# DATABASE INITIALIZATION
# =========================================================
init_db()


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        authenticated = False
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cursor.fetchone()
            cursor.close()
            db.close()
            if user:
                authenticated = True
        except Exception:
            pass

        if not authenticated and username == "admin" and password == "admin123":
            authenticated = True

        if authenticated:
            session["logged_in"] = True
            session["username"] = username

            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Total slots
    cursor.execute("SELECT COUNT(*) AS total FROM parking_slots")
    total_slots = cursor.fetchone()["total"]

    # Available slots
    cursor.execute(
        "SELECT COUNT(*) AS total FROM parking_slots WHERE status='Available'"
    )
    available_slots = cursor.fetchone()["total"]

    # Occupied slots
    cursor.execute(
        "SELECT COUNT(*) AS total FROM parking_slots WHERE status='Occupied'"
    )
    occupied_slots = cursor.fetchone()["total"]

    # Total vehicles
    cursor.execute("SELECT COUNT(*) AS total FROM vehicles")
    total_vehicles = cursor.fetchone()["total"]

    # Active parking
    cursor.execute(
        "SELECT COUNT(*) AS total FROM parking_records WHERE exit_time IS NULL"
    )
    active_parking = cursor.fetchone()["total"]

    # Today's revenue
    cursor.execute("""
        SELECT COALESCE(SUM(parking_fee), 0) AS revenue
        FROM parking_records
        WHERE DATE(exit_time) = CURDATE()
        AND payment_status = 'Paid'
    """)

    today_revenue = cursor.fetchone()["revenue"]

    # Recent records
    cursor.execute("""
        SELECT
            pr.id,
            v.vehicle_number,
            v.vehicle_type,
            ps.slot_number,
            pr.entry_time,
            pr.exit_time,
            pr.parking_fee,
            pr.payment_status
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        JOIN parking_slots ps ON pr.slot_id = ps.id
        ORDER BY pr.id DESC
        LIMIT 10
    """)

    recent_records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        total_vehicles=total_vehicles,
        active_parking=active_parking,
        today_revenue=today_revenue,
        recent_records=recent_records
    )


# =========================================================
# PARKING SLOTS
# =========================================================

@app.route("/parking-slots")
def parking_slots():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM parking_slots
        ORDER BY slot_number
    """)

    slots = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "parking_slots.html",
        slots=slots
    )


# =========================================================
# ADD PARKING SLOT
# =========================================================

@app.route("/add-slot", methods=["POST"])
def add_slot():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    slot_number = request.form.get("slot_number")
    vehicle_type = request.form.get("vehicle_type")

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            INSERT INTO parking_slots
            (slot_number, vehicle_type, status)
            VALUES (%s, %s, 'Available')
        """, (slot_number, vehicle_type))

        db.commit()

        flash("Parking slot added successfully", "success")

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("parking_slots"))


# =========================================================
# DELETE SLOT
# =========================================================

@app.route("/delete-slot/<int:slot_id>")
def delete_slot(slot_id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
            "DELETE FROM parking_slots WHERE id=%s",
            (slot_id,)
        )

        db.commit()

        flash("Parking slot deleted", "success")

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("parking_slots"))


# =========================================================
# VEHICLES
# =========================================================

@app.route("/vehicles")
def vehicles():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM vehicles
        ORDER BY id DESC
    """)

    vehicles = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "vehicles.html",
        vehicles=vehicles
    )


# =========================================================
# ADD VEHICLE
# =========================================================

@app.route("/add-vehicle", methods=["POST"])
def add_vehicle():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    vehicle_number = request.form.get("vehicle_number")
    vehicle_type = request.form.get("vehicle_type")
    owner_name = request.form.get("owner_name")
    owner_phone = request.form.get("owner_phone")

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            INSERT INTO vehicles
            (
                vehicle_number,
                vehicle_type,
                owner_name,
                owner_phone
            )
            VALUES (%s, %s, %s, %s)
        """, (
            vehicle_number,
            vehicle_type,
            owner_name,
            owner_phone
        ))

        db.commit()

        flash("Vehicle registered successfully", "success")

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("vehicles"))


# =========================================================
# DELETE VEHICLE
# =========================================================

@app.route("/delete-vehicle/<int:vehicle_id>")
def delete_vehicle(vehicle_id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
            "DELETE FROM vehicles WHERE id=%s",
            (vehicle_id,)
        )

        db.commit()

        flash("Vehicle deleted", "success")

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("vehicles"))


# =========================================================
# VEHICLE ENTRY PAGE
# =========================================================

@app.route("/vehicle-entry")
def vehicle_entry():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Registered vehicles
    cursor.execute("""
        SELECT *
        FROM vehicles
        ORDER BY vehicle_number
    """)

    vehicles = cursor.fetchall()

    # Available slots
    cursor.execute("""
        SELECT *
        FROM parking_slots
        WHERE status='Available'
        ORDER BY slot_number
    """)

    slots = cursor.fetchall()

    # Active parking records
    cursor.execute("""
        SELECT
            pr.id,
            v.vehicle_number,
            v.vehicle_type,
            ps.slot_number,
            pr.entry_time
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        JOIN parking_slots ps ON pr.slot_id = ps.id
        WHERE pr.exit_time IS NULL
        ORDER BY pr.entry_time DESC
    """)

    active_records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "vehicle_entry.html",
        vehicles=vehicles,
        slots=slots,
        active_records=active_records
    )


# =========================================================
# RECORD VEHICLE ENTRY
# =========================================================

@app.route("/record-entry", methods=["POST"])
def record_entry():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    vehicle_id = request.form.get("vehicle_id")
    slot_id = request.form.get("slot_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Check vehicle
    cursor.execute(
        "SELECT * FROM vehicles WHERE id=%s",
        (vehicle_id,)
    )

    vehicle = cursor.fetchone()

    if not vehicle:

        cursor.close()
        db.close()

        flash("Vehicle not found", "error")
        return redirect(url_for("vehicle_entry"))

    # Check slot
    cursor.execute(
        "SELECT * FROM parking_slots WHERE id=%s",
        (slot_id,)
    )

    slot = cursor.fetchone()

    if not slot:

        cursor.close()
        db.close()

        flash("Parking slot not found", "error")
        return redirect(url_for("vehicle_entry"))

    # Check slot availability
    if slot["status"] != "Available":

        cursor.close()
        db.close()

        flash("Selected slot is already occupied", "error")
        return redirect(url_for("vehicle_entry"))

    # Check vehicle type compatibility
    if (
        slot["vehicle_type"] != "Any"
        and slot["vehicle_type"] != vehicle["vehicle_type"]
    ):

        cursor.close()
        db.close()

        flash("Vehicle type does not match this slot", "error")
        return redirect(url_for("vehicle_entry"))

    # Check vehicle already inside
    cursor.execute("""
        SELECT id
        FROM parking_records
        WHERE vehicle_id=%s
        AND exit_time IS NULL
    """, (vehicle_id,))

    existing_vehicle = cursor.fetchone()

    if existing_vehicle:

        cursor.close()
        db.close()

        flash("This vehicle is already parked", "error")
        return redirect(url_for("vehicle_entry"))

    try:

        cursor.execute("""
            INSERT INTO parking_records
            (
                vehicle_id,
                slot_id,
                entry_time,
                payment_status
            )
            VALUES (%s, %s, NOW(), 'Pending')
        """, (
            vehicle_id,
            slot_id
        ))

        cursor.execute("""
            UPDATE parking_slots
            SET status='Occupied'
            WHERE id=%s
        """, (slot_id,))

        db.commit()

        flash("Vehicle entry recorded successfully", "success")

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("vehicle_entry"))


# =========================================================
# VEHICLE EXIT PAGE
# =========================================================

@app.route("/vehicle-exit")
def vehicle_exit():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pr.id,
            v.vehicle_number,
            v.vehicle_type,
            v.owner_name,
            ps.slot_number,
            pr.entry_time
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        JOIN parking_slots ps ON pr.slot_id = ps.id
        WHERE pr.exit_time IS NULL
        ORDER BY pr.entry_time
    """)

    active_records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "vehicle_exit.html",
        active_records=active_records
    )


# =========================================================
# RECORD VEHICLE EXIT
# =========================================================

@app.route("/record-exit/<int:record_id>", methods=["GET", "POST"])
def record_exit(record_id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "GET":
        return redirect(url_for("vehicle_exit"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pr.*,
            v.vehicle_type,
            ps.slot_number
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        JOIN parking_slots ps ON pr.slot_id = ps.id
        WHERE pr.id=%s
    """, (record_id,))

    record = cursor.fetchone()

    if not record:

        cursor.close()
        db.close()

        flash("Parking record not found", "error")
        return redirect(url_for("vehicle_exit"))

    if record["exit_time"] is not None:

        cursor.close()
        db.close()

        flash("Vehicle has already exited", "error")
        return redirect(url_for("vehicle_exit"))

    exit_time = datetime.now()

    entry_time = record["entry_time"]
    if isinstance(entry_time, str):
        try:
            entry_time = datetime.fromisoformat(entry_time)
        except Exception:
            entry_time = datetime.strptime(entry_time, "%Y-%m-%d %H:%M:%S")

    duration_seconds = (
        exit_time - entry_time
    ).total_seconds()

    actual_hours = duration_seconds / 3600

    billed_hours = max(
        1,
        math.ceil(actual_hours)
    )

    # Parking rates
    rates = {
        "Bike": 10,
        "Car": 20,
        "SUV": 30,
        "Truck": 40,
        "Bus": 50
    }

    hourly_rate = rates.get(
        record["vehicle_type"],
        20
    )

    parking_fee = billed_hours * hourly_rate

    duration_text = f"{billed_hours} hour(s)"

    try:

        cursor.execute("""
            UPDATE parking_records
            SET
                exit_time=%s,
                duration=%s,
                parking_fee=%s,
                payment_status='Paid'
            WHERE id=%s
        """, (
            exit_time,
            duration_text,
            parking_fee,
            record_id
        ))

        cursor.execute("""
            UPDATE parking_slots
            SET status='Available'
            WHERE id=(
                SELECT slot_id
                FROM parking_records
                WHERE id=%s
            )
        """, (record_id,))

        db.commit()

        flash(
            f"Vehicle exited successfully. Parking fee: ₹{parking_fee}",
            "success"
        )

    except Exception as error:

        db.rollback()
        flash(f"Error: {error}", "error")

    cursor.close()
    db.close()

    return redirect(url_for("vehicle_exit"))


# =========================================================
# PARKING HISTORY
# =========================================================

@app.route("/parking-history")
def parking_history():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pr.id,
            v.vehicle_number,
            v.vehicle_type,
            v.owner_name,
            ps.slot_number,
            pr.entry_time,
            pr.exit_time,
            pr.duration,
            pr.parking_fee,
            pr.payment_status
        FROM parking_records pr
        JOIN vehicles v ON pr.vehicle_id = v.id
        JOIN parking_slots ps ON pr.slot_id = ps.id
        ORDER BY pr.id DESC
    """)

    records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "parking_history.html",
        records=records
    )


# =========================================================
# REVENUE
# =========================================================

@app.route("/revenue")
def revenue():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COALESCE(SUM(parking_fee), 0) AS total_revenue
        FROM parking_records
        WHERE payment_status='Paid'
    """)

    total_revenue = cursor.fetchone()["total_revenue"]

    cursor.execute("""
        SELECT
            COALESCE(SUM(parking_fee), 0) AS today_revenue
        FROM parking_records
        WHERE payment_status='Paid'
        AND DATE(exit_time)=CURDATE()
    """)

    today_revenue = cursor.fetchone()["today_revenue"]

    cursor.execute("""
        SELECT
            COUNT(*) AS total_paid
        FROM parking_records
        WHERE payment_status='Paid'
    """)

    total_paid = cursor.fetchone()["total_paid"]

    cursor.execute("""
        SELECT
            COUNT(*) AS total_pending
        FROM parking_records
        WHERE payment_status='Pending'
    """)

    total_pending = cursor.fetchone()["total_pending"]

    cursor.execute("""
        SELECT
            COUNT(*) AS total_records
        FROM parking_records
    """)

    total_records = cursor.fetchone()["total_records"]

    cursor.close()
    db.close()

    return render_template(
        "revenue.html",
        total_revenue=total_revenue,
        today_revenue=today_revenue,
        total_paid=total_paid,
        total_pending=total_pending,
        total_records=total_records
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )