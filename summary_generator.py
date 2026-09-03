"""
Summary Generator Module for Consent-Aware Continuity Summary System.

Assembles structured handover summaries using:
1. ML Relevance Model predictions
2. DL Sensitivity Model predictions
3. Consent Engine evaluations
4. Role-Based Access Control (RBAC)
5. Low-confidence Human Review Flags (< 70% threshold)
"""

from ml_model import predict_relevance
from dl_model import predict_sensitivity
from consent_engine import evaluate_consent
from access_control import check_role_access

CONFIDENCE_THRESHOLD = 70.0

def generate_continuity_summary(session_data, user_role="Counsellor"):
    """
    Generates a structured, safe continuity summary for a session record.
    
    Args:
        session_data (dict): Session record dictionary containing text fields and consent strings/booleans.
        user_role (str): 'Counsellor' or 'Social Worker'
        
    Returns:
        dict: Complete structured summary object ready for dashboard display.
    """
    session_id = session_data.get('session_id', 'Unknown')
    client_id = session_data.get('client_id', 'Unknown')
    
    # Raw input text fields
    session_text = str(session_data.get('session_text', '') or '').strip()
    client_goal = str(session_data.get('client_goal', '') or '').strip()
    pending_action = str(session_data.get('pending_action', '') or '').strip()
    sensitive_text = str(session_data.get('sensitive_text', '') or '').strip()

    # Fallback for missing/empty fields (Edge Case 4)
    if not session_text:
        session_text = "No previous session notes recorded."
    if not client_goal:
        client_goal = "No specific goal recorded."
    if not pending_action:
        pending_action = "No pending action recorded."
    if not sensitive_text:
        sensitive_text = "No sensitive details recorded."

    # 1. Run ML Relevance Prediction
    ml_res = predict_relevance(session_text)
    
    # 2. Run DL Sensitivity Prediction
    dl_res = predict_sensitivity(sensitive_text + " " + session_text)

    # 3. Check Low Confidence Flag for Human Review
    ml_low_conf = ml_res.get('confidence', 100.0) < CONFIDENCE_THRESHOLD
    dl_low_conf = dl_res.get('confidence', 100.0) < CONFIDENCE_THRESHOLD
    human_review_required = ml_low_conf or dl_low_conf

    review_reason = []
    if ml_low_conf:
        review_reason.append(f"ML Relevance confidence ({ml_res['confidence']}%) is below threshold ({CONFIDENCE_THRESHOLD}%)")
    if dl_low_conf:
        review_reason.append(f"DL Sensitivity confidence ({dl_res['confidence']}%) is below threshold ({CONFIDENCE_THRESHOLD}%)")

    # 4. Consent Engine Evaluation
    consent_flags = {
        'consent_summary': session_data.get('consent_summary', 'No'),
        'consent_goal': session_data.get('consent_goal', 'No'),
        'consent_pending_action': session_data.get('consent_pending_action', 'No'),
        'consent_sensitive': session_data.get('consent_sensitive', 'No')
    }
    consent_eval = evaluate_consent(consent_flags)

    # 5. Access Control (RBAC) & Masking
    # Session Summary Content
    summary_access = check_role_access(user_role, 'summary', consent_eval['summary']['permitted'])
    if summary_access['allowed']:
        display_summary = session_text if ml_res['prediction'] == 1 else "Session content classified as non-relevant for handover."
    else:
        display_summary = summary_access['display_text']

    # Goal Content
    goal_access = check_role_access(user_role, 'goal', consent_eval['goal']['permitted'])
    display_goal = client_goal if goal_access['allowed'] else goal_access['display_text']

    # Pending Action Content
    pending_access = check_role_access(user_role, 'pending_action', consent_eval['pending_action']['permitted'])
    display_pending = pending_action if pending_access['allowed'] else pending_access['display_text']

    # Sensitive Information Content
    sensitive_access = check_role_access(user_role, 'sensitive', consent_eval['sensitive']['permitted'])
    display_sensitive = sensitive_text if sensitive_access['allowed'] else sensitive_access['display_text']

    # Privacy Protection Decision Summary
    is_protected = not (summary_access['allowed'] and goal_access['allowed'] and pending_access['allowed'] and sensitive_access['allowed'])

    return {
        "client_id": client_id,
        "session_id": session_id,
        "user_role": user_role,
        "summary_text": display_summary,
        "client_goal": display_goal,
        "pending_action": display_pending,
        "sensitive_text": display_sensitive,
        
        "ml_relevance": ml_res['label'],
        "ml_confidence": ml_res['confidence'],
        "dl_sensitivity": dl_res['label'],
        "dl_confidence": dl_res['confidence'],
        
        "human_review_required": human_review_required,
        "human_review_reasons": review_reason,
        
        "consent_status": {
            "summary": consent_eval['summary']['permitted'],
            "goal": consent_eval['goal']['permitted'],
            "pending_action": consent_eval['pending_action']['permitted'],
            "sensitive": consent_eval['sensitive']['permitted']
        },
        
        "access_details": {
            "summary": summary_access,
            "goal": goal_access,
            "pending_action": pending_access,
            "sensitive": sensitive_access
        },
        
        "privacy_status": "Protected" if is_protected else "Full Access Granted"
    }

if __name__ == '__main__':
    # Test sample run
    test_session = {
        'client_id': 'C001',
        'session_id': 'S001',
        'session_text': '[Voice Transcript] Client called Helpline regarding severe exam anxiety and requested study plan support.',
        'client_goal': 'Develop study schedule and mindfulness routine.',
        'pending_action': 'Follow-up call next Tuesday.',
        'sensitive_text': 'Client shared private disclosures regarding past stress treatment.',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'No'  # Sensitive consent denied
    }

    res_counsellor = generate_continuity_summary(test_session, user_role="Counsellor")
    print("=== CONTINUITY SUMMARY GENERATOR TEST (Counsellor) ===")
    print(f"Client ID: {res_counsellor['client_id']}")
    print(f"Summary: {res_counsellor['summary_text']}")
    print(f"Sensitive: {res_counsellor['sensitive_text']}")
    print(f"Privacy Status: {res_counsellor['privacy_status']}")
    print(f"Human Review Required: {res_counsellor['human_review_required']}")
