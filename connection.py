"""
MySQL connection handling + schema creation for Cardiac Rhythm Analysis System.
Uses PyMySQL, matching the tech stack in the architecture spec.
"""

import pymysql
import pymysql.cursors

from config import DB_CONFIG


def get_connection(with_database=True):
    """Opens a new PyMySQL connection. Set with_database=False when the
    target database itself may not exist yet (used once at first-run)."""
    kwargs = dict(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    if with_database:
        kwargs["database"] = DB_CONFIG["database"]
    return pymysql.connect(**kwargs)


def init_db():
    """Creates the database (if missing) and all tables (if missing)."""
    # Step 1: ensure the database itself exists
    conn = get_connection(with_database=False)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    # Step 2: create tables
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    full_name VARCHAR(200),
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_code VARCHAR(30) NOT NULL UNIQUE,
                    name VARCHAR(200) NOT NULL,
                    age INT,
                    gender VARCHAR(20),
                    contact VARCHAR(100),
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS ecg_reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    report_code VARCHAR(30) NOT NULL UNIQUE,
                    patient_id INT NOT NULL,
                    dataset_filename VARCHAR(255),
                    heart_rate FLOAT,
                    rr_interval FLOAT,
                    pr_interval FLOAT,
                    qrs_duration FLOAT,
                    qt_interval FLOAT,
                    qtc_interval FLOAT,
                    beat_count INT,
                    signal_duration FLOAT,
                    finding VARCHAR(255),
                    status VARCHAR(30),
                    clinician_notes TEXT,
                    waveform_chart_path VARCHAR(500),
                    created_by INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # Report History is a lightweight audit/query view over ecg_reports,
            # but the architecture spec calls it out as its own store - kept as
            # a separate table so report status can change after creation
            # (e.g. "Review needed" -> "Stable") without touching the original
            # analysis record.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS report_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    report_id INT NOT NULL,
                    status VARCHAR(30) NOT NULL,
                    note TEXT,
                    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES ecg_reports(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

        conn.commit()
    finally:
        conn.close()
