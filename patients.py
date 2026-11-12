"""
Patient Module: Add - Update - Search - Delete, matching the architecture
spec's "Patient Module" backend block.
"""

from database.connection import get_connection


def _next_patient_code(cur):
    cur.execute("SELECT COUNT(*) AS n FROM patients")
    n = cur.fetchone()["n"] + 1
    from datetime import datetime
    year = datetime.now().year
    return f"PT-{year}-{n:04d}"


def add_patient(name, age=None, gender="", contact="", notes=""):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            code = _next_patient_code(cur)
            cur.execute(
                "INSERT INTO patients (patient_code, name, age, gender, contact, notes) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (code, name, age, gender, contact, notes),
            )
        conn.commit()
        return code
    finally:
        conn.close()


def update_patient(patient_id, name, age=None, gender="", contact="", notes=""):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE patients SET name=%s, age=%s, gender=%s, contact=%s, notes=%s WHERE id=%s",
                (name, age, gender, contact, notes, patient_id),
            )
        conn.commit()
    finally:
        conn.close()


def delete_patient(patient_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM patients WHERE id=%s", (patient_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_patients():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM patients ORDER BY name ASC")
            return cur.fetchall()
    finally:
        conn.close()


def search_patients(term):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM patients WHERE name LIKE %s OR patient_code LIKE %s ORDER BY name ASC",
                (f"%{term}%", f"%{term}%"),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_patient_by_id(patient_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_patient_by_name(name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM patients WHERE name = %s", (name,))
            return cur.fetchone()
    finally:
        conn.close()


def patient_name_exists(name):
    return get_patient_by_name(name) is not None
