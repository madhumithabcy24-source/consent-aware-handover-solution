"""
Role-Based Access Control (RBAC) Module for Youth Helpline Handover System.

ROLES:
1. Counsellor: Full care scope, allowed to view sensitive information ONLY if client consent is granted.
2. Social Worker: Community/social care scope, sensitive information restricted by default.
"""

ROLE_COUNSELLOR = "Counsellor"
ROLE_SOCIAL_WORKER = "Social Worker"

def check_role_access(user_role, category_key, consent_permitted):
    """
    Checks if a user role is permitted to view content for a category, given client consent status.
    
    Args:
        user_role (str): 'Counsellor' or 'Social Worker'
        category_key (str): 'summary', 'goal', 'pending_action', or 'sensitive'
        consent_permitted (bool): Output from Consent Engine evaluation
        
    Returns:
        dict: {
            "allowed": bool,
            "display_text": None if allowed else restriction badge text,
            "reason": Explanation string
        }
    """
    # Rule 1: Consent MUST override everything. If consent denied, block immediately.
    if not consent_permitted:
        return {
            "allowed": False,
            "display_text": "🔒 Restricted by consent",
            "reason": "Restricted because client consent was not provided."
        }

    # Rule 2: Category-level RBAC check
    if category_key == "sensitive":
        # Social workers restricted by default for sensitive text
        if user_role.strip().lower() == "social worker":
            return {
                "allowed": False,
                "display_text": "🔒 Restricted by role",
                "reason": "Restricted because Social Worker role does not have default access to sensitive clinical notes."
            }
        elif user_role.strip().lower() == "counsellor":
            # Allowed because consent was True
            return {
                "allowed": True,
                "display_text": None,
                "reason": "Permitted for Counsellor role with explicit client consent."
            }
        else:
            return {
                "allowed": False,
                "display_text": "🔒 Restricted by role",
                "reason": "Unrecognized user role."
            }

    # For non-sensitive categories (summary, goal, pending_action), allowed if consent granted
    return {
        "allowed": True,
        "display_text": None,
        "reason": f"Permitted for {user_role} with client consent."
    }

if __name__ == '__main__':
    print("=== ACCESS CONTROL (RBAC) TEST ===")
    
    # Test 1: Counsellor + Consent Yes
    res1 = check_role_access("Counsellor", "sensitive", consent_permitted=True)
    print(f"Counsellor (Consent=Yes): Allowed={res1['allowed']}, Text='{res1['display_text']}'")
    
    # Test 2: Social Worker + Consent Yes
    res2 = check_role_access("Social Worker", "sensitive", consent_permitted=True)
    print(f"Social Worker (Consent=Yes): Allowed={res2['allowed']}, Text='{res2['display_text']}'")
    
    # Test 3: Counsellor + Consent No
    res3 = check_role_access("Counsellor", "sensitive", consent_permitted=False)
    print(f"Counsellor (Consent=No): Allowed={res3['allowed']}, Text='{res3['display_text']}'")
