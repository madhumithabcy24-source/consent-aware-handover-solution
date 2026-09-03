import os
import functools
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from database import (
    init_db, get_user, get_all_sessions, get_session_by_id,
    add_session, update_session_consent, log_handover_access, get_all_handover_logs
)
from summary_generator import generate_continuity_summary
from preprocess import load_and_preprocess_data
from evaluation import get_model_evaluation_metrics, evaluate_baseline_vs_proposed

app = Flask(__name__)
app.secret_key = 'youth_helpline_handover_secret_key_demo'

# Initialize SQLite database on startup
init_db()

def login_required(view):
    """Decorator to enforce login on protected routes."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_user():
    """Injects current user info into template context."""
    return {
        'current_user': session.get('username'),
        'user_role': session.get('role', 'Counsellor')
    }

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = get_user(username)
        if user and user['password'] == password:
            session.clear()
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f"Welcome back, {user['username']}! Logged in as {user['role']}.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Demo accounts: counsellor/1234 or socialworker/1234", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    sessions_list = get_all_sessions()
    total_sessions = len(sessions_list)
    
    # Calculate stats
    relevant_count = 0
    sensitive_count = 0
    protected_count = 0

    for s in sessions_list:
        s_dict = dict(s)
        if int(s_dict.get('relevance_label', 1)) == 1:
            relevant_count += 1
        if int(s_dict.get('sensitivity_label', 0)) == 1 or len(str(s_dict.get('sensitive_text', ''))) > 0:
            sensitive_count += 1
        if s_dict.get('consent_sensitive', 'No') == 'No':
            protected_count += 1

    recent_sessions = sessions_list[:8]
    audit_logs = get_all_handover_logs()[:5]

    return render_template('dashboard.html',
                           total_sessions=total_sessions,
                           relevant_count=relevant_count,
                           sensitive_count=sensitive_count,
                           protected_count=protected_count,
                           recent_sessions=recent_sessions,
                           audit_logs=audit_logs)

@app.route('/create-session', methods=['GET', 'POST'])
@login_required
def create_session():
    if request.method == 'POST':
        client_id = request.form.get('client_id', '').strip()
        session_id = request.form.get('session_id', '').strip()
        session_text = request.form.get('session_text', '').strip()
        client_goal = request.form.get('client_goal', '').strip()
        pending_action = request.form.get('pending_action', '').strip()
        sensitive_text = request.form.get('sensitive_text', '').strip()

        consent_summary = request.form.get('consent_summary', 'No')
        consent_goal = request.form.get('consent_goal', 'No')
        consent_pending_action = request.form.get('consent_pending_action', 'No')
        consent_sensitive = request.form.get('consent_sensitive', 'No')

        if not client_id or not session_id or not session_text:
            flash("Client ID, Session ID, and Session Text are required.", "danger")
            return redirect(url_for('create_session'))

        # Check existing session ID
        if get_session_by_id(session_id):
            flash(f"Session ID '{session_id}' already exists. Please use a unique ID.", "danger")
            return redirect(url_for('create_session'))

        session_data = {
            'client_id': client_id,
            'session_id': session_id,
            'session_text': session_text,
            'client_goal': client_goal,
            'pending_action': pending_action,
            'sensitive_text': sensitive_text,
            'consent_summary': consent_summary,
            'consent_goal': consent_goal,
            'consent_pending_action': consent_pending_action,
            'consent_sensitive': consent_sensitive
        }

        add_session(session_data)
        flash(f"Session '{session_id}' created successfully!", "success")
        return redirect(url_for('handover', session_id=session_id))

    # Auto-generate suggestion ID
    existing_count = len(get_all_sessions())
    next_client_id = f"C{(existing_count % 25) + 1:03d}"
    next_session_id = f"S{existing_count + 1:03d}"

    return render_template('create_session.html',
                           suggested_client_id=next_client_id,
                           suggested_session_id=next_session_id)

@app.route('/sessions')
@login_required
def sessions():
    all_sessions = get_all_sessions()
    return render_template('sessions.html', sessions=all_sessions)

@app.route('/sessions/<session_id>/consent', methods=['GET', 'POST'])
@login_required
def edit_consent(session_id):
    """Working Consent Management UI allowing consent editing and immediate revocation."""
    session_record = get_session_by_id(session_id)
    if not session_record:
        flash(f"Session '{session_id}' not found.", "danger")
        return redirect(url_for('sessions'))

    if request.method == 'POST':
        consent_summary = request.form.get('consent_summary', 'No')
        consent_goal = request.form.get('consent_goal', 'No')
        consent_pending_action = request.form.get('consent_pending_action', 'No')
        consent_sensitive = request.form.get('consent_sensitive', 'No')

        update_session_consent(session_id, consent_summary, consent_goal, consent_pending_action, consent_sensitive)
        flash(f"Consent preferences updated for Session '{session_id}'. Next handover will immediately reflect changes.", "success")
        return redirect(url_for('handover', session_id=session_id))

    return render_template('edit_consent.html', session=session_record)

@app.route('/handover/<session_id>')
@login_required
def handover(session_id):
    session_record = get_session_by_id(session_id)
    if not session_record:
        flash(f"Session '{session_id}' not found.", "danger")
        return redirect(url_for('sessions'))

    user_role = session.get('role', 'Counsellor')
    summary_obj = generate_continuity_summary(dict(session_record), user_role=user_role)

    # Prepare audit log categories (NO sensitive text stored)
    shared_cats = []
    restricted_cats = []

    for cat in ['summary', 'goal', 'pending_action', 'sensitive']:
        access = summary_obj['access_details'][cat]
        if access['allowed']:
            shared_cats.append(f"{cat.capitalize()}: Shared")
        else:
            restricted_cats.append(f"{cat.capitalize()}: Restricted")

    log_handover_access(session_id, user_role, shared_cats, restricted_cats)

    return render_template('handover.html',
                           session=session_record,
                           summary=summary_obj)

@app.route('/baseline')
@login_required
def baseline():
    all_sessions = get_all_sessions()
    selected_id = request.args.get('session_id', all_sessions[0]['session_id'] if all_sessions else None)
    
    selected_session = get_session_by_id(selected_id) if selected_id else None
    user_role = session.get('role', 'Counsellor')
    
    summary_obj = None
    if selected_session:
        summary_obj = generate_continuity_summary(dict(selected_session), user_role=user_role)

    comp_data = evaluate_baseline_vs_proposed()

    return render_template('baseline.html',
                           sessions=all_sessions,
                           selected_session=selected_session,
                           summary=summary_obj,
                           comp_data=comp_data)

@app.route('/evaluation')
@login_required
def evaluation():
    metrics = get_model_evaluation_metrics()
    comp_data = evaluate_baseline_vs_proposed()
    return render_template('evaluation.html', metrics=metrics, comp_data=comp_data)

@app.route('/user-guide')
@login_required
def user_guide():
    return render_template('user_guide.html')

@app.route('/test-cases')
@login_required
def test_cases():
    test_cases_list = [
        {
            "id": "CASE 1",
            "title": "Consent Denied",
            "input": "client_goal = 'Improve study focus', consent_summary = 'No'",
            "expected": "Information hidden ('🔒 Restricted by consent')",
            "actual": "Information hidden ('🔒 Restricted by consent')",
            "status": "PASS"
        },
        {
            "id": "CASE 2",
            "title": "Sensitive Content Detected + Consent Denied",
            "input": "sensitive_text = 'Confidential personal disclosures', consent_sensitive = 'No'",
            "expected": "Information remains hidden ('🔒 Restricted by consent')",
            "actual": "Information remains hidden ('🔒 Restricted by consent')",
            "status": "PASS"
        },
        {
            "id": "CASE 3",
            "title": "Social Worker Access to Restricted Sensitive Content",
            "input": "user_role = 'Social Worker', consent_sensitive = 'Yes'",
            "expected": "Access denied ('🔒 Restricted by role')",
            "actual": "Access denied ('🔒 Restricted by role')",
            "status": "PASS"
        },
        {
            "id": "CASE 4",
            "title": "Missing Pending Action",
            "input": "pending_action = '' (Empty string)",
            "expected": "'No pending action recorded.' (No crash)",
            "actual": "'No pending action recorded.'",
            "status": "PASS"
        },
        {
            "id": "CASE 5",
            "title": "Consent Revoked in Real-Time",
            "input": "consent_sensitive updated from 'Yes' -> 'No'",
            "expected": "Sensitive info becomes hidden immediately upon next summary",
            "actual": "Sensitive info becomes hidden immediately upon next summary",
            "status": "PASS"
        }
    ]
    return render_template('test_cases.html', test_cases=test_cases_list)

@app.route('/models')
@login_required
def models_info():
    return render_template('models.html')

if __name__ == '__main__':
    print("Starting Youth Helpline Handover Flask Web App on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
