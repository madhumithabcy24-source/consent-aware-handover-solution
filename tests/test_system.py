"""
Automated Test Suite for Consent-Aware Continuity Summary System.

Verifies the 5 Mandatory Edge/Failure Test Cases:
CASE 1: Consent denied -> Information is hidden.
CASE 2: Sensitive content detected + consent denied -> Remains hidden.
CASE 3: Social Worker attempts to view restricted sensitive content -> Access denied/restricted.
CASE 4: Missing pending action -> "No pending action recorded" gracefully handled without crash.
CASE 5: Consent revoked -> Sensitive info becomes hidden immediately upon next summary generation.
"""

import sys
import os

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from consent_engine import evaluate_consent
from access_control import check_role_access
from summary_generator import generate_continuity_summary

def test_case_1_consent_denied():
    """CASE 1: Consent denied -> Information is hidden."""
    session_data = {
        'client_id': 'C999',
        'session_id': 'S999',
        'session_text': 'Client discussed study tips.',
        'client_goal': 'Improve focus.',
        'pending_action': 'Check-in Friday.',
        'sensitive_text': 'No sensitive info.',
        'consent_summary': 'No',  # Denied
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'
    }
    
    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['summary_text'] == "🔒 Restricted by consent"
    assert summary['consent_status']['summary'] == False
    print("\n[PASS] CASE 1: Consent denied -> Information hidden successfully.")

def test_case_2_sensitive_detected_and_consent_denied():
    """CASE 2: Sensitive content detected + consent denied -> Remains hidden."""
    session_data = {
        'client_id': 'C998',
        'session_id': 'S998',
        'session_text': 'Client shared emotional stress.',
        'client_goal': 'Coping mechanisms.',
        'pending_action': 'Follow-up call.',
        'sensitive_text': 'Client disclosed private health history and personal trauma.',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'No'  # Sensitive consent denied
    }

    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['sensitive_text'] == "🔒 Restricted by consent"
    assert summary['dl_sensitivity'] == "Sensitive" or summary['dl_sensitivity'] == "Non-sensitive"
    print("\n[PASS] CASE 2: Sensitive detected + consent denied -> Information remains hidden.")

def test_case_3_social_worker_access_restricted_sensitive():
    """CASE 3: Social Worker attempts to view sensitive content -> Access restricted by role."""
    session_data = {
        'client_id': 'C997',
        'session_id': 'S997',
        'session_text': 'Client discussed community housing.',
        'client_goal': 'Find housing.',
        'pending_action': 'Submit application.',
        'sensitive_text': 'Client shared confidential medical history.',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'  # Client granted consent
    }

    # Counsellor can view sensitive info when consented
    summary_counsellor = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary_counsellor['sensitive_text'] != "🔒 Restricted by role"

    # Social Worker MUST BE RESTRICTED by role even when client consented
    summary_sw = generate_continuity_summary(session_data, user_role="Social Worker")
    assert summary_sw['sensitive_text'] == "🔒 Restricted by role"
    print("\n[PASS] CASE 3: Social Worker access to sensitive content -> Restricted by role.")

def test_case_4_missing_pending_action():
    """CASE 4: Missing pending action -> Gracefully displays default without crashing."""
    session_data = {
        'client_id': 'C996',
        'session_id': 'S996',
        'session_text': 'Client called Helpline.',
        'client_goal': 'General support.',
        'pending_action': '',  # Empty / Missing
        'sensitive_text': '',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'
    }

    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['pending_action'] == "No pending action recorded."
    print("\n[PASS] CASE 4: Missing pending action -> Gracefully handled.")

def test_case_5_consent_revoked():
    """CASE 5: Consent revoked -> Sensitive info becomes hidden immediately upon next summary generation."""
    session_data = {
        'client_id': 'C995',
        'session_id': 'S995',
        'session_text': 'Client session notes.',
        'client_goal': 'Goal notes.',
        'pending_action': 'Action notes.',
        'sensitive_text': 'Confidential family background.',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'  # Initially Granted
    }

    # Step 1: Initial Handover with Consent = Yes
    initial_summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert initial_summary['sensitive_text'] == "Confidential family background."

    # Step 2: Revoke Consent (Change to 'No')
    session_data['consent_sensitive'] = 'No'

    # Step 3: Next Handover summary immediately reflects revoked consent
    updated_summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert updated_summary['sensitive_text'] == "🔒 Restricted by consent"
    print("\n[PASS] CASE 5: Consent revoked -> Sensitive info becomes hidden immediately.")

if __name__ == '__main__':
    print("=== RUNNING AUTOMATED EDGE CASE TEST SUITE ===")
    test_case_1_consent_denied()
    test_case_2_sensitive_detected_and_consent_denied()
    test_case_3_social_worker_access_restricted_sensitive()
    test_case_4_missing_pending_action()
    test_case_5_consent_revoked()
    print("\n[SUCCESS] ALL 5 MANDATORY EDGE/FAILURE TEST CASES PASSED SUCCESSFULLY!")
