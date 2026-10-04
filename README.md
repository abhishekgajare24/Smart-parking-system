# Smart Parking Management System

A web-based Smart Parking Management application built with Python (Flask) and a flexible database layer supporting both SQLite (zero-configuration out of the box) and MySQL.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+ (Python 3.14 installed)
- Virtual environment (already configured in `venv/`)

### 2. Run the Application
You can run the application directly using the virtual environment:
```powershell
.\venv\Scripts\python.exe app.py
```
Or activate the virtual environment first:
```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` |

---

## 🛠️ Features

- **Dashboard**: Live metrics on total slots, available slots, occupied slots, registered vehicles, active parking sessions, and today's revenue, plus a live activity table.
- **Parking Slots**: View slot statuses, add new slots (Car, Bike, SUV, Any), or remove slots.
- **Vehicles Registry**: Register vehicles with type, owner name, and contact details.
- **Vehicle Entry**: Check-in vehicles into compatible available parking slots.
- **Vehicle Exit & Automated Billing**: Instant billing calculation based on vehicle type and duration:
  - *Bike*: ₹10 / hour
  - *Car*: ₹20 / hour
  - *SUV*: ₹30 / hour
  - *Truck*: ₹40 / hour
  - *Bus*: ₹50 / hour
- **Parking History**: Complete audit trail of past and ongoing parking records.
- **Revenue Analytics**: Summary of lifetime revenue, daily revenue, paid vs. pending transactions, and total session counts.

---

## 🗄️ Database Architecture

The application includes an automated dual database backend (`db.py`):
1. **SQLite (Default fallback)**: Automatically creates and seeds `smart_parking.db` on first run. Requires zero installation or external services.
2. **MySQL**: If MySQL server is installed and running on `localhost:3306`, the application can connect directly to MySQL.

### Custom Database Configuration (Optional)
Configure via environment variables:
- `DB_TYPE`: `auto` (default), `mysql`, or `sqlite`
- `DB_HOST`: Database host (default: `localhost`)
- `DB_PORT`: Database port (default: `3306`)
- `DB_USER`: Database username (default: `root`)
- `DB_PASSWORD`: Database password (default: `MyNewPassword@123`)
- `DB_NAME`: Database schema name (default: `smart_parking`)

---

## 📁 Project Structure

```
smart-parking-system/
├── app.py              # Main Flask web application routes & views
├── db.py               # Unified database connection & abstraction layer
├── database.sql        # MySQL schema definition and seed data
├── requirements.txt    # Project dependencies (Flask, mysql-connector-python)
├── smart_parking.db    # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   ├── dashboard.css   # Main dashboard and interior styling
│   │   └── style.css       # Login and landing styles
│   └── js/
│       └── script.js
├── templates/          # Jinja2 HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── parking_slots.html
│   ├── vehicles.html
│   ├── vehicle_entry.html
│   ├── vehicle_exit.html
│   ├── parking_history.html
│   └── revenue.html
└── venv/               # Python virtual environment
```
