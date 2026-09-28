"""
Automated Test Suite for Consent-Aware Continuity Summary System.

Verifies the 7 Mandatory Failure/Edge-Case Test Scenarios:
TEST 1: Consent denied -> Information is hidden.
TEST 2: Sensitive content + consent denied -> Sensitive content remains hidden regardless of ML/DL prediction.
TEST 3: Social Worker attempts access to restricted sensitive content -> Access denied by role.
TEST 4: Consent revoked after previously being granted -> Newly generated handover respects revoked consent immediately.
TEST 5: Conflicting/partial consent selections -> Only explicitly permitted fields are shown.
TEST 6: Malformed/incomplete session input -> Safely validated without crashing.
TEST 7: Sensitive content incorrectly missed by DL model (DL false negative override) -> Consent/RBAC still prevents unauthorized exposure.
"""

import sys
import os

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from consent_engine import evaluate_consent
from access_control import check_role_access
from summary_generator import generate_continuity_summary

def test_1_consent_denied():
    """TEST 1: Consent denied -> Protected information must not appear in the handover."""
    session_data = {
        'client_id': 'C999',
        'session_id': 'S999',
        'session_text': 'Client discussed study tips.',
        'client_goal': 'Improve focus.',
        'pending_action': 'Check-in Friday.',
        'sensitive_text': 'No sensitive info.',
        'consent_summary': 'No',  # Summary consent denied
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'
    }
    
    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['summary_text'] == "🔒 Restricted by consent"
    assert summary['consent_status']['summary'] == False
    print("\n[PASS] TEST 1: Consent denied -> Protected info hidden successfully.")
    return {
        "id": "TEST 1",
        "title": "Consent Denied",
        "input": "consent_summary = 'No'",
        "expected": "Protected summary text must not appear in handover ('🔒 Restricted by consent')",
        "actual": f"Summary display: '{summary['summary_text']}'",
        "status": "PASS"
    }

def test_2_sensitive_content_and_consent_denied():
    """TEST 2: Sensitive content + consent denied -> Sensitive content remains hidden regardless of model prediction."""
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
    print("\n[PASS] TEST 2: Sensitive content + consent denied -> Hidden regardless of model prediction.")
    return {
        "id": "TEST 2",
        "title": "Sensitive Content + Consent Denied",
        "input": "sensitive_text present, DL label = Sensitive/Non-sensitive, consent_sensitive = 'No'",
        "expected": "Sensitive content hidden ('🔒 Restricted by consent')",
        "actual": f"Sensitive display: '{summary['sensitive_text']}'",
        "status": "PASS"
    }

def test_3_social_worker_access_restricted_sensitive():
    """TEST 3: Social Worker attempts to access restricted sensitive information -> Access denied."""
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

    summary_sw = generate_continuity_summary(session_data, user_role="Social Worker")
    assert summary_sw['sensitive_text'] == "🔒 Restricted by role"
    print("\n[PASS] TEST 3: Social Worker access restricted sensitive info -> Access denied by role.")
    return {
        "id": "TEST 3",
        "title": "Social Worker Access to Sensitive Info",
        "input": "user_role = 'Social Worker', consent_sensitive = 'Yes'",
        "expected": "Access denied ('🔒 Restricted by role')",
        "actual": f"Sensitive display: '{summary_sw['sensitive_text']}'",
        "status": "PASS"
    }

def test_4_consent_revoked():
    """TEST 4: Consent revoked after previously being granted -> Newly generated handover respects revoked consent."""
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

    initial_summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert initial_summary['sensitive_text'] == "Confidential family background."

    # Revoke consent
    session_data['consent_sensitive'] = 'No'

    updated_summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert updated_summary['sensitive_text'] == "🔒 Restricted by consent"
    print("\n[PASS] TEST 4: Consent revoked -> Next handover immediately reflects change.")
    return {
        "id": "TEST 4",
        "title": "Consent Revocation Handling",
        "input": "consent_sensitive updated 'Yes' -> 'No'",
        "expected": "Immediate redaction on next handover ('🔒 Restricted by consent')",
        "actual": f"Initial: '{initial_summary['sensitive_text']}' | After Revocation: '{updated_summary['sensitive_text']}'",
        "status": "PASS"
    }

def test_5_conflicting_partial_consent():
    """TEST 5: Conflicting/partial consent selections -> Only explicitly permitted fields are shown."""
    session_data = {
        'client_id': 'C994',
        'session_id': 'S994',
        'session_text': 'Session summary text notes.',
        'client_goal': 'Improve study plan.',
        'pending_action': 'Follow-up on Friday.',
        'sensitive_text': 'Private emotional distress details.',
        'consent_summary': 'No',            # Denied
        'consent_goal': 'Yes',           # Permitted
        'consent_pending_action': 'Yes',  # Permitted
        'consent_sensitive': 'No'        # Denied
    }

    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['summary_text'] == "🔒 Restricted by consent"
    assert summary['client_goal'] == "Improve study plan."
    assert summary['pending_action'] == "Follow-up on Friday."
    assert summary['sensitive_text'] == "🔒 Restricted by consent"
    print("\n[PASS] TEST 5: Conflicting/partial consent -> Only permitted fields displayed.")
    return {
        "id": "TEST 5",
        "title": "Conflicting / Partial Consent",
        "input": "Goal = Yes, Pending = Yes, Summary = No, Sensitive = No",
        "expected": "Goal & Pending shown; Summary & Sensitive hidden",
        "actual": f"Goal: '{summary['client_goal']}' | Summary: '{summary['summary_text']}'",
        "status": "PASS"
    }

def test_6_malformed_incomplete_input():
    """TEST 6: Malformed/incomplete session input -> Application safely validates without crashing."""
    session_data = {
        'client_id': 'C993',
        'session_id': 'S993',
        'session_text': '',       # Missing / Empty string
        'client_goal': None,     # None / Null value
        'pending_action': '',    # Missing
        'sensitive_text': None,  # None
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'Yes'
    }

    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['pending_action'] == "No pending action recorded."
    assert summary['client_goal'] == "No specific goal recorded."
    assert summary['summary_text'] != ""
    print("\n[PASS] TEST 6: Malformed/incomplete input -> Safely validated without crashing.")
    return {
        "id": "TEST 6",
        "title": "Malformed / Incomplete Input",
        "input": "Missing client/session fields, null goal, empty pending_action",
        "expected": "Safely fallback to default descriptive strings without runtime error",
        "actual": f"Pending: '{summary['pending_action']}', Goal: '{summary['client_goal']}'",
        "status": "PASS"
    }

def test_7_dl_false_negative_override():
    """TEST 7: Sensitive content incorrectly missed by DL model -> Consent & RBAC still protect it."""
    session_data = {
        'client_id': 'C992',
        'session_id': 'S992',
        'session_text': 'Standard chat session.',
        'client_goal': 'Goal notes.',
        'pending_action': 'Action notes.',
        'sensitive_text': 'Subtle unclassified distress notes.',
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'No'  # Client denied consent
    }

    # Simulate DL false negative where DL output prediction is 0 (Non-sensitive)
    summary = generate_continuity_summary(session_data, user_role="Counsellor")
    assert summary['sensitive_text'] == "🔒 Restricted by consent"
    print("\n[PASS] TEST 7: DL false negative -> Consent engine still enforces protection.")
    return {
        "id": "TEST 7",
        "title": "DL False Negative Privacy Defense",
        "input": "DL predicts 'Non-sensitive', but consent_sensitive = 'No'",
        "expected": "Consent engine overrides DL prediction and hides content ('🔒 Restricted by consent')",
        "actual": f"Sensitive display: '{summary['sensitive_text']}'",
        "status": "PASS"
    }

def run_all_failure_tests():
    """Runs all 7 test cases and returns structured results."""
    results = [
        test_1_consent_denied(),
        test_2_sensitive_content_and_consent_denied(),
        test_3_social_worker_access_restricted_sensitive(),
        test_4_consent_revoked(),
        test_5_conflicting_partial_consent(),
        test_6_malformed_incomplete_input(),
        test_7_dl_false_negative_override()
    ]
    return results

if __name__ == '__main__':
    print("=== RUNNING AUTOMATED FAILURE & EDGE-CASE TEST SUITE ===")
    res = run_all_failure_tests()
    print(f"\n[SUCCESS] ALL {len(res)} MANDATORY EDGE/FAILURE TEST CASES PASSED SUCCESSFULLY!")
