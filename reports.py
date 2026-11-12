"""
ECG report + report history queries.
"""

from datetime import datetime

from database.connection import get_connection


def _next_report_code(cur):
    cur.execute("SELECT COUNT(*) AS n FROM ecg_reports")
    n = cur.fetchone()["n"] + 1
    year = datetime.now().year
    return f"RPT-{year}-{n:04d}"


def create_report(patient_id, dataset_filename, params, finding, status,
                   clinician_notes="", waveform_chart_path=None, created_by=None):
    """
    params is a dict with keys: heart_rate, rr_interval, pr_interval,
    qrs_duration, qt_interval, qtc_interval, beat_count, signal_duration
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            code = _next_report_code(cur)
            cur.execute("""
                INSERT INTO ecg_reports (
                    report_code, patient_id, dataset_filename,
                    heart_rate, rr_interval, pr_interval, qrs_duration,
                    qt_interval, qtc_interval, beat_count, signal_duration,
                    finding, status, clinician_notes, waveform_chart_path, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                code, patient_id, dataset_filename,
                params.get("heart_rate"), params.get("rr_interval"), params.get("pr_interval"),
                params.get("qrs_duration"), params.get("qt_interval"), params.get("qtc_interval"),
                params.get("beat_count"), params.get("signal_duration"),
                finding, status, clinician_notes, waveform_chart_path, created_by,
            ))
            report_id = cur.lastrowid
            cur.execute(
                "INSERT INTO report_history (report_id, status, note) VALUES (%s, %s, %s)",
                (report_id, status, "Report created"),
            )
        conn.commit()
        return code, report_id
    finally:
        conn.close()


def get_report_by_id(report_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, p.name AS patient_name, p.patient_code
                FROM ecg_reports r JOIN patients p ON r.patient_id = p.id
                WHERE r.id = %s
            """, (report_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_all_reports():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, p.name AS patient_name, p.patient_code
                FROM ecg_reports r JOIN patients p ON r.patient_id = p.id
                ORDER BY r.created_at DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_reports_for_patient(patient_id, ascending=False):
    order = "ASC" if ascending else "DESC"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT r.*, p.name AS patient_name, p.patient_code
                FROM ecg_reports r JOIN patients p ON r.patient_id = p.id
                WHERE r.patient_id = %s
                ORDER BY r.created_at {order}
            """, (patient_id,))
            return cur.fetchall()
    finally:
        conn.close()


def search_reports(term=None, status=None, date_from=None, date_to=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT r.*, p.name AS patient_name, p.patient_code
                FROM ecg_reports r JOIN patients p ON r.patient_id = p.id
                WHERE 1=1
            """
            args = []
            if term:
                query += " AND (p.name LIKE %s OR r.report_code LIKE %s)"
                args += [f"%{term}%", f"%{term}%"]
            if status and status != "All":
                query += " AND r.status = %s"
                args.append(status)
            if date_from:
                query += " AND r.created_at >= %s"
                args.append(date_from)
            if date_to:
                query += " AND r.created_at <= %s"
                args.append(date_to)
            query += " ORDER BY r.created_at DESC"
            cur.execute(query, args)
            return cur.fetchall()
    finally:
        conn.close()


def update_report_status(report_id, status, note=""):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE ecg_reports SET status = %s WHERE id = %s", (status, report_id))
            cur.execute(
                "INSERT INTO report_history (report_id, status, note) VALUES (%s, %s, %s)",
                (report_id, status, note),
            )
        conn.commit()
    finally:
        conn.close()


def delete_report(report_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ecg_reports WHERE id = %s", (report_id,))
        conn.commit()
    finally:
        conn.close()


def get_latest_report():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.*, p.name AS patient_name, p.patient_code
                FROM ecg_reports r JOIN patients p ON r.patient_id = p.id
                ORDER BY r.created_at DESC LIMIT 1
            """)
            return cur.fetchone()
    finally:
        conn.close()


def count_reports():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM ecg_reports")
            return cur.fetchone()["n"]
    finally:
        conn.close()


def count_reports_needing_review():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM ecg_reports WHERE status = 'Review needed'")
            return cur.fetchone()["n"]
    finally:
        conn.close()
