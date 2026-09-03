import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), 'youth_helpline.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'synthetic_sessions.csv')

def get_db_connection():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes SQLite database tables and seeds demo users & synthetic session dataset.
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

    # 3. Handover Audit Logs Table (NO raw sensitive text stored)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS handover_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_role TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            information_shared TEXT NOT NULL,
            information_restricted TEXT NOT NULL
        )
    ''')

    conn.commit()

    # Seed Demo Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ('counsellor', '1234', 'Counsellor'),
            ('socialworker', '1234', 'Social Worker')
        ]
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", demo_users)
        conn.commit()
        print("[SUCCESS] Seeded demo users: 'counsellor' and 'socialworker'")

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
    """Inserts a new session record into SQLite."""
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

def log_handover_access(session_id, user_role, shared_categories, restricted_categories):
    """
    Creates an audit log for handover access.
    NOTE: Only category status names (e.g. 'Summary: Shared', 'Sensitive: Restricted') are stored.
    NO raw sensitive text is ever written to audit logs.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO handover_logs (session_id, user_role, information_shared, information_restricted)
        VALUES (?, ?, ?, ?)
    ''', (session_id, user_role, ", ".join(shared_categories), ", ".join(restricted_categories)))
    conn.commit()
    conn.close()

def get_all_handover_logs():
    """Fetches recent audit logs."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM handover_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return logs

if __name__ == '__main__':
    print("=== DATABASE INITIALIZATION ===")
    init_db()
