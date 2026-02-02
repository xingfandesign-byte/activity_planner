"""
SQLite persistence for Weekend Planner.
Replaces in-memory dicts with a single weekend_planner.db file.
"""

import os
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# Database file path (default: same directory as this file)
DB_PATH = os.environ.get('DATABASE_URL', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weekend_planner.db'))

# Thread-local connection would be better for Flask; for single-threaded dev we use one connection per request
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                identifier TEXT NOT NULL,
                identifier_type TEXT NOT NULL,
                password_hash TEXT,
                created_at TEXT NOT NULL,
                email_digest INTEGER DEFAULT 1,
                name TEXT,
                picture TEXT,
                email_verified INTEGER NOT NULL DEFAULT 0,
                UNIQUE(identifier)
            );
            CREATE INDEX IF NOT EXISTS idx_users_identifier ON users(identifier);

            CREATE TABLE IF NOT EXISTS preferences (
                user_id TEXT PRIMARY KEY,
                prefs_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS visited_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                place_id TEXT NOT NULL,
                visited_at TEXT NOT NULL,
                signal_type TEXT DEFAULT 'manual',
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_visited_user ON visited_history(user_id);

            CREATE TABLE IF NOT EXISTS saved_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                place_id TEXT NOT NULL,
                saved_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_saved_user ON saved_places(user_id);

            CREATE TABLE IF NOT EXISTS recent_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                place_id TEXT NOT NULL,
                rec_id TEXT NOT NULL,
                recommended_at TEXT NOT NULL,
                week TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_recent_user ON recent_recommendations(user_id);

            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS verification_tokens (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
        """)
    # Add email_verified column if missing (migration for existing DBs)
    with get_conn() as c:
        try:
            c.execute("SELECT email_verified FROM users LIMIT 1")
        except sqlite3.OperationalError:
            c.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
    print(f"[DB] Initialized SQLite at {DB_PATH}")


# ---------- Users ----------

def get_user_by_identifier(identifier):
    """Get user by email or phone. Returns dict or None."""
    with get_conn() as c:
        row = c.execute(
            "SELECT user_id, identifier, identifier_type, password_hash, created_at, email_digest, name, picture, COALESCE(email_verified, 0) AS email_verified FROM users WHERE identifier = ?",
            (identifier,)
        ).fetchone()
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "email": row["identifier"] if row["identifier_type"] in ("email", "google") else None,
        "phone": row["identifier"] if row["identifier_type"] == "phone" else None,
        "password": row["password_hash"],
        "created_at": row["created_at"],
        "email_digest": bool(row["email_digest"]),
        "name": row["name"],
        "picture": row["picture"],
        "email_verified": bool(row["email_verified"]),
    }


def get_user_by_user_id(user_id):
    """Get user by user_id. Returns dict or None."""
    with get_conn() as c:
        row = c.execute(
            "SELECT user_id, identifier, identifier_type, password_hash, created_at, email_digest, name, picture, COALESCE(email_verified, 0) AS email_verified FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "email": row["identifier"] if row["identifier_type"] in ("email", "google") else None,
        "phone": row["identifier"] if row["identifier_type"] == "phone" else None,
        "password": row["password_hash"],
        "created_at": row["created_at"],
        "email_digest": bool(row["email_digest"]),
        "name": row["name"],
        "picture": row["picture"],
        "email_verified": bool(row["email_verified"]),
    }


def create_user_email(email, user_id, password_hash, email_digest=True):
    with get_conn() as c:
        c.execute(
            "INSERT INTO users (user_id, identifier, identifier_type, password_hash, created_at, email_digest, email_verified) VALUES (?, ?, 'email', ?, ?, ?, 0)",
            (user_id, email.lower(), password_hash, datetime.now().isoformat(), 1 if email_digest else 0)
        )


def create_user_phone(phone, user_id):
    with get_conn() as c:
        c.execute(
            "INSERT INTO users (user_id, identifier, identifier_type, password_hash, created_at, email_digest) VALUES (?, ?, 'phone', NULL, ?, 0)",
            (user_id, phone, datetime.now().isoformat())
        )


def upsert_user_google(user_id, email, name=None, picture=None):
    """Insert or update user for Google sign-in. Google users are considered email-verified."""
    with get_conn() as c:
        existing = c.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
        now = datetime.now().isoformat()
        if existing:
            c.execute(
                "UPDATE users SET identifier = ?, name = ?, picture = ?, identifier_type = 'google', email_verified = 1 WHERE user_id = ?",
                (email.lower(), name or "", picture or "", user_id)
            )
        else:
            c.execute(
                "INSERT INTO users (user_id, identifier, identifier_type, password_hash, created_at, email_digest, name, picture, email_verified) VALUES (?, ?, 'google', NULL, ?, 1, ?, ?, 1)",
                (user_id, email.lower(), now, name or "", picture or "", 1)
            )


def user_exists_by_identifier(identifier):
    return get_user_by_identifier(identifier) is not None


def update_user_password(identifier, password_hash):
    """Update password for user identified by email (identifier)."""
    with get_conn() as c:
        c.execute("UPDATE users SET password_hash = ? WHERE identifier = ?", (password_hash, identifier.lower()))


def count_users():
    with get_conn() as c:
        return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]


# ---------- Preferences ----------

def get_preferences(user_id):
    row = None
    with get_conn() as c:
        row = c.execute("SELECT prefs_json FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["prefs_json"])
    except (json.JSONDecodeError, TypeError):
        return None


def set_preferences(user_id, prefs):
    now = datetime.now().isoformat()
    prefs_json = json.dumps(prefs) if isinstance(prefs, dict) else json.dumps({})
    with get_conn() as c:
        c.execute(
            "INSERT INTO preferences (user_id, prefs_json, updated_at) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET prefs_json = ?, updated_at = ?",
            (user_id, prefs_json, now, prefs_json, now)
        )


# ---------- Visited history ----------

def get_visited_list(user_id):
    with get_conn() as c:
        rows = c.execute(
            "SELECT place_id, visited_at, signal_type, confidence FROM visited_history WHERE user_id = ? ORDER BY visited_at DESC",
            (user_id,)
        ).fetchall()
    return [
        {"place_id": r["place_id"], "visited_at": r["visited_at"], "signal_type": r["signal_type"], "confidence": r["confidence"]}
        for r in rows
    ]


def add_visited(user_id, place_id, visited_at=None, signal_type="manual", confidence=1.0):
    visited_at = visited_at or datetime.now().isoformat()
    with get_conn() as c:
        c.execute(
            "INSERT INTO visited_history (user_id, place_id, visited_at, signal_type, confidence) VALUES (?, ?, ?, ?, ?)",
            (user_id, place_id, visited_at, signal_type, confidence)
        )


def remove_visited(user_id, place_id):
    with get_conn() as c:
        c.execute("DELETE FROM visited_history WHERE user_id = ? AND place_id = ?", (user_id, place_id))


def visited_contains(user_id, place_id):
    with get_conn() as c:
        return c.execute("SELECT 1 FROM visited_history WHERE user_id = ? AND place_id = ?", (user_id, place_id)).fetchone() is not None


# ---------- Saved places ----------

def get_saved_list(user_id):
    with get_conn() as c:
        rows = c.execute(
            "SELECT place_id, saved_at FROM saved_places WHERE user_id = ? ORDER BY saved_at DESC",
            (user_id,)
        ).fetchall()
    return [{"place_id": r["place_id"], "saved_at": r["saved_at"]} for r in rows]


def add_saved(user_id, place_id, saved_at=None):
    saved_at = saved_at or datetime.now().isoformat()
    with get_conn() as c:
        c.execute(
            "INSERT INTO saved_places (user_id, place_id, saved_at) VALUES (?, ?, ?)",
            (user_id, place_id, saved_at)
        )


def remove_saved(user_id, place_id):
    with get_conn() as c:
        c.execute("DELETE FROM saved_places WHERE user_id = ? AND place_id = ?", (user_id, place_id))


def saved_contains(user_id, place_id):
    with get_conn() as c:
        return c.execute("SELECT 1 FROM saved_places WHERE user_id = ? AND place_id = ?", (user_id, place_id)).fetchone() is not None


# ---------- Recent recommendations ----------

def get_recent_recommendations_list(user_id):
    with get_conn() as c:
        rows = c.execute(
            "SELECT place_id, rec_id, recommended_at, week FROM recent_recommendations WHERE user_id = ? ORDER BY recommended_at DESC",
            (user_id,)
        ).fetchall()
    return [
        {"place_id": r["place_id"], "rec_id": r["rec_id"], "recommended_at": r["recommended_at"], "week": r["week"]}
        for r in rows
    ]


def add_recent_recommendation(user_id, place_id, rec_id, week):
    now = datetime.now().isoformat()
    with get_conn() as c:
        c.execute(
            "INSERT INTO recent_recommendations (user_id, place_id, rec_id, recommended_at, week) VALUES (?, ?, ?, ?, ?)",
            (user_id, place_id, rec_id, now, week)
        )


# ---------- Auth tokens ----------

def get_user_id_from_token(token):
    with get_conn() as c:
        row = c.execute("SELECT user_id FROM auth_tokens WHERE token = ?", (token,)).fetchone()
    return row["user_id"] if row else None


def set_auth_token(token, user_id):
    now = datetime.now().isoformat()
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO auth_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, now)
        )


def delete_auth_token(token):
    with get_conn() as c:
        c.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))


# ---------- Password reset tokens ----------

def get_reset_token(token):
    with get_conn() as c:
        row = c.execute("SELECT email, expires_at FROM password_reset_tokens WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def set_reset_token(token, email, expires_at):
    expires_at_str = expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at)
    with get_conn() as c:
        c.execute(
            "INSERT INTO password_reset_tokens (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email.lower(), expires_at_str)
        )


def delete_reset_token(token):
    with get_conn() as c:
        c.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))


def reset_token_exists(token):
    return get_reset_token(token) is not None


def user_exists_by_email_for_reset(email):
    return user_exists_by_identifier(email.lower())


# ---------- Email verification tokens ----------

VERIFICATION_TOKEN_EXPIRY_HOURS = 24


def get_verification_token(token):
    with get_conn() as c:
        row = c.execute("SELECT email, expires_at FROM verification_tokens WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def set_verification_token(token, email, expires_at):
    expires_at_str = expires_at.isoformat() if hasattr(expires_at, "isoformat") else str(expires_at)
    with get_conn() as c:
        c.execute(
            "INSERT INTO verification_tokens (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email.lower(), expires_at_str)
        )


def delete_verification_token(token):
    with get_conn() as c:
        c.execute("DELETE FROM verification_tokens WHERE token = ?", (token,))


def set_user_email_verified(identifier):
    """Mark user as email-verified by identifier (email)."""
    with get_conn() as c:
        c.execute("UPDATE users SET email_verified = 1 WHERE identifier = ?", (identifier.lower(),))


# ---------- Debug / list users for get_user_preferences ----------

def list_users_by_user_id():
    """Return dict of user_id -> user info for compatibility with old loop."""
    with get_conn() as c:
        rows = c.execute(
            "SELECT user_id, identifier, identifier_type, name, picture FROM users"
        ).fetchall()
    return {
        row["user_id"]: {
            "user_id": row["user_id"],
            "email": row["identifier"] if row["identifier_type"] in ("email", "google") else None,
            "phone": row["identifier"] if row["identifier_type"] == "phone" else None,
            "name": row["name"],
            "picture": row["picture"],
        }
        for row in rows
    }
