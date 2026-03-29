"""
auth.py — User Authentication + Subscription System
Handles: signup, login, email subscriptions, user preferences
"""
import os, json, hashlib, secrets, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create user tables if they don't exist"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        password_hash TEXT,
        plan TEXT DEFAULT 'free',
        favourite_driver TEXT,
        favourite_team TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        subscribed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        notify_prediction INTEGER DEFAULT 1,
        notify_results INTEGER DEFAULT 1,
        notify_weekly INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT
    )""")

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except Exception:
        return False


def signup(email: str, name: str, password: str,
           favourite_driver: str = "", favourite_team: str = "") -> dict:
    """Register a new user"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        pw_hash = hash_password(password)
        c.execute("""INSERT INTO users
            (email, name, password_hash, favourite_driver, favourite_team)
            VALUES (?,?,?,?,?)""",
            (email.lower().strip(), name, pw_hash, favourite_driver, favourite_team))
        user_id = c.lastrowid

        # Auto-subscribe to emails
        c.execute("""INSERT OR IGNORE INTO subscribers (email, name)
            VALUES (?,?)""", (email.lower().strip(), name))

        conn.commit()

        # Save to subscribers.json for email scheduler
        _sync_subscribers_json()

        return {"success": True, "user_id": user_id, "message": "Account created!"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Email already registered"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def login(email: str, password: str) -> dict:
    """Authenticate user and return session token"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND is_active=1",
                  (email.lower().strip(),))
        user = c.fetchone()

        if not user:
            return {"success": False, "message": "Email not found"}

        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Incorrect password"}

        # Create session token
        token = secrets.token_urlsafe(32)
        expires = (datetime.now() + timedelta(days=30)).isoformat()
        c.execute("""INSERT INTO sessions (user_id, token, expires_at)
            VALUES (?,?,?)""", (user["id"], token, expires))

        # Update last login
        c.execute("UPDATE users SET last_login=? WHERE id=?",
                  (datetime.now().isoformat(), user["id"]))
        conn.commit()

        return {
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "plan": user["plan"],
                "favourite_driver": user["favourite_driver"],
                "favourite_team": user["favourite_team"],
            }
        }
    finally:
        conn.close()


def get_user_by_token(token: str) -> dict:
    """Get user from session token"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("""SELECT u.* FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token=? AND s.expires_at > ?""",
            (token, datetime.now().isoformat()))
        user = c.fetchone()
        if user:
            return dict(user)
        return None
    finally:
        conn.close()


def subscribe_email(email: str, name: str = "") -> dict:
    """Subscribe email without full signup"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("""INSERT OR IGNORE INTO subscribers (email, name)
            VALUES (?,?)""", (email.lower().strip(), name))
        conn.commit()
        _sync_subscribers_json()
        return {"success": True, "message": "Subscribed successfully!"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()


def unsubscribe_email(email: str) -> dict:
    """Unsubscribe from emails"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("UPDATE subscribers SET is_active=0 WHERE email=?",
                  (email.lower().strip(),))
        conn.commit()
        _sync_subscribers_json()
        return {"success": True, "message": "Unsubscribed"}
    finally:
        conn.close()


def get_all_subscribers() -> list:
    """Get all active subscribers"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM subscribers WHERE is_active=1")
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


def get_user_count() -> dict:
    """Get platform stats"""
    init_db()
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM users WHERE is_active=1")
        users = c.fetchone()["total"]
        c.execute("SELECT COUNT(*) as total FROM subscribers WHERE is_active=1")
        subs = c.fetchone()["total"]
        c.execute("SELECT COUNT(*) as total FROM users WHERE plan='pro' AND is_active=1")
        pro = c.fetchone()["total"]
        return {"users": users, "subscribers": subs, "pro_users": pro}
    finally:
        conn.close()


def _sync_subscribers_json():
    """Keep subscribers.json in sync with DB for email scheduler"""
    subs = get_all_subscribers()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "subscribers.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(subs, f, indent=2)


# Init on import
init_db()
