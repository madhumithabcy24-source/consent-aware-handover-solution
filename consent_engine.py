"""
Consent Engine Module for Youth Helpline Handover System.

CORE DESIGN PRINCIPLE:
CONSENT MUST ALWAYS OVERRIDE MODEL OUTPUT.
Even if the ML/DL model predicts that an item is relevant or sensitive/non-sensitive,
if the client has not granted explicit consent for that category, the item MUST NOT be displayed.
"""

def normalize_consent_value(val):
    """Normalizes consent input (str 'Yes'/'No', bool, or int 1/0) into boolean True/False."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val == 1)
    if isinstance(val, str):
        return val.strip().lower() in ['yes', '1', 'true']
    return False

def evaluate_consent(consent_flags):
    """
    Evaluates consent flags for all handover categories.
    
    Args:
        consent_flags (dict): {
            'consent_summary': 'Yes'/'No' or True/False,
            'consent_goal': 'Yes'/'No' or True/False,
            'consent_pending_action': 'Yes'/'No' or True/False,
            'consent_sensitive': 'Yes'/'No' or True/False
        }
        
    Returns:
        dict: Evaluation status for each category with boolean permission and explanatory reason.
    """
    summary_granted = normalize_consent_value(consent_flags.get('consent_summary', 'No'))
    goal_granted = normalize_consent_value(consent_flags.get('consent_goal', 'No'))
    pending_granted = normalize_consent_value(consent_flags.get('consent_pending_action', 'No'))
    sensitive_granted = normalize_consent_value(consent_flags.get('consent_sensitive', 'No'))

    return {
        "summary": {
            "permitted": summary_granted,
            "reason": "Consent granted by client." if summary_granted else "Restricted because client consent was not provided."
        },
        "goal": {
            "permitted": goal_granted,
            "reason": "Consent granted by client." if goal_granted else "Restricted because client consent was not provided."
        },
        "pending_action": {
            "permitted": pending_granted,
            "reason": "Consent granted by client." if pending_granted else "Restricted because client consent was not provided."
        },
        "sensitive": {
            "permitted": sensitive_granted,
            "reason": "Consent granted by client." if sensitive_granted else "Restricted because client consent was not provided."
        }
    }

if __name__ == '__main__':
    # Quick test case
    sample_consent = {
        'consent_summary': 'Yes',
        'consent_goal': 'Yes',
        'consent_pending_action': 'Yes',
        'consent_sensitive': 'No'  # Client denied consent for sensitive info
    }
    result = evaluate_consent(sample_consent)
    print("=== CONSENT ENGINE TEST ===")
    for cat, info in result.items():
        print(f"  {cat.upper()}: Permitted={info['permitted']} | Reason='{info['reason']}'")
