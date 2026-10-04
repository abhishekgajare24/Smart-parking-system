import os
import re
import sqlite3
from datetime import datetime, date

try:
    import mysql.connector
except ImportError:
    mysql = None

DB_TYPE = os.environ.get("DB_TYPE", "auto").lower()  # 'auto', 'mysql', 'sqlite'
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "MyNewPassword@123")
DB_NAME = os.environ.get("DB_NAME", "smart_parking")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.environ.get("DB_SQLITE_PATH", os.path.join(BASE_DIR, "smart_parking.db"))

_ACTIVE_BACKEND = None


def detect_backend():
    """Detect whether to use MySQL or SQLite based on configuration and availability."""
    global _ACTIVE_BACKEND
    if _ACTIVE_BACKEND is not None:
        return _ACTIVE_BACKEND

    if DB_TYPE == "sqlite":
        _ACTIVE_BACKEND = "sqlite"
        print(f"[Database] Configured for SQLite: {SQLITE_DB_PATH}")
        return _ACTIVE_BACKEND

    if DB_TYPE in ("mysql", "auto"):
        if mysql is not None:
            try:
                # Test connection with a fast timeout (1 second)
                test_conn = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    connection_timeout=1
                )
                test_conn.close()
                _ACTIVE_BACKEND = "mysql"
                print(f"[Database] Connected to MySQL server at {DB_HOST}:{DB_PORT}")
                return _ACTIVE_BACKEND
            except Exception as e:
                if DB_TYPE == "mysql":
                    print(f"[Database] ERROR: MySQL connection failed: {e}")
                    raise
                print(f"[Database] MySQL not reachable on {DB_HOST}:{DB_PORT}. Falling back to SQLite.")
                _ACTIVE_BACKEND = "sqlite"
                return _ACTIVE_BACKEND
        else:
            if DB_TYPE == "mysql":
                raise ImportError("mysql-connector-python is not installed.")
            print("[Database] mysql-connector-python not available. Using SQLite.")
            _ACTIVE_BACKEND = "sqlite"
            return _ACTIVE_BACKEND

    _ACTIVE_BACKEND = "sqlite"
    return _ACTIVE_BACKEND


class SQLiteCursorAdapter:
    """Cursor adapter wrapping sqlite3.Cursor to provide a MySQL-compatible interface."""
    def __init__(self, cursor, as_dict=True):
        self.cursor = cursor
        self.as_dict = as_dict

    def execute(self, sql, params=None):
        # Translate %s placeholder to ? for sqlite3
        translated_sql = re.sub(r'%s', '?', sql)
        if params is not None:
            normalized_params = []
            for p in params:
                if isinstance(p, (datetime, date)):
                    normalized_params.append(
                        p.strftime("%Y-%m-%d %H:%M:%S") if isinstance(p, datetime) else p.isoformat()
                    )
                else:
                    normalized_params.append(p)
            self.cursor.execute(translated_sql, tuple(normalized_params))
        else:
            self.cursor.execute(translated_sql)
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()


class SQLiteConnectionAdapter:
    """Connection adapter wrapping sqlite3.Connection to provide a MySQL-compatible interface."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, dictionary=False):
        return SQLiteCursorAdapter(self.conn.cursor(), as_dict=dictionary)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db_connection():
    """Returns a database connection (MySQL if running, otherwise SQLite)."""
    backend = detect_backend()
    if backend == "mysql":
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        conn.create_function("CURDATE", 0, lambda: date.today().isoformat())
        return SQLiteConnectionAdapter(conn)


def init_db():
    """Initializes tables and seed data if they do not exist."""
    backend = detect_backend()
    if backend == "mysql":
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            conn.database = DB_NAME

            sql_file = os.path.join(BASE_DIR, "database.sql")
            if os.path.exists(sql_file):
                with open(sql_file, "r", encoding="utf-8") as f:
                    statements = f.read().split(";")
                    for stmt in statements:
                        cleaned = stmt.strip()
                        if cleaned and not cleaned.lower().startswith("create database") and not cleaned.lower().startswith("use "):
                            cursor.execute(cleaned)
                conn.commit()
            cursor.close()
            conn.close()
            print("[Database] MySQL schema verified.")
        except Exception as e:
            print(f"[Database] MySQL initialization warning: {e}")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT UNIQUE NOT NULL,
            vehicle_type TEXT NOT NULL DEFAULT 'Any',
            status TEXT NOT NULL DEFAULT 'Available'
        );

        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            vehicle_type TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            owner_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS parking_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            entry_time DATETIME NOT NULL,
            exit_time DATETIME NULL,
            duration TEXT,
            parking_fee REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'Pending',
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
            FOREIGN KEY (slot_id) REFERENCES parking_slots(id) ON DELETE CASCADE
        );

        INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'admin123');

        INSERT OR IGNORE INTO parking_slots (slot_number, vehicle_type, status) VALUES
        ('A01', 'Car', 'Available'),
        ('A02', 'Car', 'Available'),
        ('A03', 'Car', 'Available'),
        ('B01', 'Bike', 'Available'),
        ('B02', 'Bike', 'Available'),
        ('B03', 'Bike', 'Available'),
        ('C01', 'SUV', 'Available'),
        ('C02', 'Any', 'Available'),
        ('C03', 'Any', 'Available');
        """)
        conn.commit()
        conn.close()
        print("[Database] SQLite database schema initialized successfully.")
