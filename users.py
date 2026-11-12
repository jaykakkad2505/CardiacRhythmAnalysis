"""
User (clinician) account queries. Passwords hashed with bcrypt, matching
the architecture spec's Authentication module (Login - bcrypt - Session).
"""

import bcrypt

from database.connection import get_connection


def create_user(username, password, full_name=""):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, full_name, password_hash) VALUES (%s, %s, %s)",
                (username, full_name, password_hash),
            )
        conn.commit()
    finally:
        conn.close()


def username_exists(username):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def verify_login(username, password):
    """Returns the user record (dict) if credentials are correct, else None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        return None
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return user
    return None


def get_user_by_id(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_profile(user_id, full_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET full_name = %s WHERE id = %s", (full_name, user_id))
        conn.commit()
    finally:
        conn.close()


def change_password(user_id, current_password, new_password):
    """Returns True if changed, False if current_password was wrong."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user or not bcrypt.checkpw(current_password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                return False

            new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def any_user_exists():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users LIMIT 1")
            return cur.fetchone() is not None
    finally:
        conn.close()
