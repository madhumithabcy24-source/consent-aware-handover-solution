import os
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'youth_helpline.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'synthetic_sessions.csv')

def get_db_connection():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes SQLite database tables, performs auto-migrations, and seeds demo users & synthetic sessions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 2. Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            session_id TEXT UNIQUE NOT NULL,
            session_text TEXT NOT NULL,
            client_goal TEXT,
            pending_action TEXT,
            sensitive_text TEXT,
            consent_summary TEXT DEFAULT 'Yes',
            consent_goal TEXT DEFAULT 'Yes',
            consent_pending_action TEXT DEFAULT 'Yes',
            consent_sensitive TEXT DEFAULT 'No',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Handover & Security Audit Logs Table (NO raw sensitive text stored)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS handover_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_role TEXT NOT NULL,
            event_type TEXT DEFAULT 'handover_access',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            information_shared TEXT NOT NULL,
            information_restricted TEXT NOT NULL
        )
    ''')

    # Auto-migration: Ensure event_type column exists on pre-existing database tables
    cursor.execute("PRAGMA table_info(handover_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'event_type' not in columns:
        try:
            cursor.execute("ALTER TABLE handover_logs ADD COLUMN event_type TEXT DEFAULT 'handover_access'")
            print("[INFO] Migrated database schema: Added 'event_type' column to 'handover_logs'")
        except Exception as e:
            print(f"[WARNING] Table migration skipped or failed: {e}")

    conn.commit()

    # Seed Demo Users with Secure Password Hashes
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ('counsellor', generate_password_hash('1234'), 'Counsellor'),
            ('socialworker', generate_password_hash('1234'), 'Social Worker')
        ]
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", demo_users)
        conn.commit()
        print("[SUCCESS] Seeded demo users with hashed passwords: 'counsellor' and 'socialworker'")

    # Seed Synthetic Sessions from CSV
    cursor.execute("SELECT COUNT(*) FROM sessions")
    if cursor.fetchone()[0] == 0 and os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO sessions (
                    client_id, session_id, session_text, client_goal, pending_action,
                    sensitive_text, consent_summary, consent_goal, consent_pending_action, consent_sensitive
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(row['client_id']),
                str(row['session_id']),
                str(row['session_text']),
                str(row['client_goal']),
                str(row['pending_action']),
                str(row['sensitive_text']),
                str(row['consent_summary']),
                str(row['consent_goal']),
                str(row['consent_pending_action']),
                str(row['consent_sensitive'])
            ))
        conn.commit()
        print(f"[SUCCESS] Seeded {len(df)} synthetic session records into SQLite")

    conn.close()

def get_user(username):
    """Fetches user record by username."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def verify_user_password(stored_password, provided_password):
    """Verifies password using Werkzeug check_password_hash with fallback for plain text."""
    if stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:'):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password

def get_all_sessions():
    """Fetches all session records ordered by session_id."""
    conn = get_db_connection()
    sessions = conn.execute("SELECT * FROM sessions ORDER BY session_id ASC").fetchall()
    conn.close()
    return sessions

def get_session_by_id(session_id):
    """Fetches a single session record by session_id."""
    conn = get_db_connection()
    session = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    return session

def add_session(session_data):
    """Inserts a new session record into SQLite using parameterized queries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (
            client_id, session_id, session_text, client_goal, pending_action,
            sensitive_text, consent_summary, consent_goal, consent_pending_action, consent_sensitive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_data['client_id'],
        session_data['session_id'],
        session_data['session_text'],
        session_data['client_goal'],
        session_data['pending_action'],
        session_data['sensitive_text'],
        session_data['consent_summary'],
        session_data['consent_goal'],
        session_data['consent_pending_action'],
        session_data['consent_sensitive']
    ))
    conn.commit()
    conn.close()

def update_session_consent(session_id, consent_summary, consent_goal, consent_pending_action, consent_sensitive):
    """Updates client consent preferences in real-time."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sessions
        SET consent_summary = ?,
            consent_goal = ?,
            consent_pending_action = ?,
            consent_sensitive = ?
        WHERE session_id = ?
    ''', (consent_summary, consent_goal, consent_pending_action, consent_sensitive, session_id))
    conn.commit()
    conn.close()

def log_audit_event(session_id, user_role, event_type, shared_info, restricted_info):
    """
    Creates an audit log entry for security and privacy events.
    CRITICAL: NO raw sensitive session text is EVER recorded. Only metadata and status summaries.
    Events: 'login', 'logout', 'handover_access', 'restricted_access_attempt', 'consent_filtering', 'role_denial'
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO handover_logs (session_id, user_role, event_type, information_shared, information_restricted)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, user_role, event_type, str(shared_info), str(restricted_info)))
    conn.commit()
    conn.close()

def log_handover_access(session_id, user_role, shared_categories, restricted_categories):
    """Backward-compatible audit logger for handover access."""
    event_type = 'handover_access'
    if any('Restricted' in r for r in restricted_categories):
        event_type = 'consent_or_role_filtering'
    log_audit_event(
        session_id=session_id,
        user_role=user_role,
        event_type=event_type,
        shared_info=", ".join(shared_categories) if shared_categories else "None",
        restricted_info=", ".join(restricted_categories) if restricted_categories else "None"
    )

def get_all_handover_logs():
    """Fetches recent audit logs."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM handover_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return logs

if __name__ == '__main__':
    print("=== DATABASE INITIALIZATION & MIGRATION ===")
    init_db()
