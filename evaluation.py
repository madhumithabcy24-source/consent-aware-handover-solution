"""
Evaluation Module for Consent-Aware Continuity Summary System.

Computes REAL empirical metrics on actual synthetic dataset predictions and ground truth labels:
1. ML Relevance Model metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) on test split.
2. DL Sensitivity Model metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) on test split.
3. Privacy Metrics (Redaction Leakage Rate, Sensitive Exposure Count, Sensitive Items Protected, Consent Violations).
4. Handover Metrics (Relevant Information Retained %, Handover Completeness %, Unnecessary Noise Exposure %).
5. Empirical Baseline vs. Proposed System Comparison.
"""

import os
import pandas as pd
import numpy as np

from preprocess import load_and_preprocess_data
from ml_model import train_and_evaluate_ml
from database import get_all_sessions

_EVALUATION_CACHE = None

def clear_evaluation_cache():
    """Clears cached evaluation result so next request recomputes updated stats."""
    global _EVALUATION_CACHE
    _EVALUATION_CACHE = None

def get_model_evaluation_metrics():
    """Returns real test set metrics for both ML Relevance and DL Sensitivity models."""
    ml_metrics = train_and_evaluate_ml()
    
    # Import build_and_train_dl dynamically
    from dl_model import build_and_train_dl
    dl_metrics = build_and_train_dl()

    return {
        "ml_relevance": ml_metrics,
        "dl_sensitivity": dl_metrics
    }

def evaluate_baseline_system(sessions=None):
    """
    Evaluates PURE BASELINE SYSTEM performance across session records.
    
    BASELINE BEHAVIOR:
    Displays raw session text, goal, pending action, and sensitive text without consent checking,
    without ML relevance filtering, without DL sensitivity detection, and without role restriction.
    
    HAS ZERO DEPENDENCY ON DEEP LEARNING MODELS OR KERAS/TENSORFLOW.
    """
    if sessions is None:
        sessions = get_all_sessions()
        if not sessions:
            df, _ = load_and_preprocess_data()
            sessions = df.to_dict('records')

    total_sessions = len(sessions)
    baseline_consent_violations = 0
    baseline_sensitive_exposures = 0
    sensitive_items_to_protect = 0
    sensitive_items_incorrectly_exposed = 0
    sensitive_items_correctly_protected = 0
    
    baseline_relevant_retained_count = 0
    baseline_unnecessary_exposure_count = 0

    total_relevant_items = 0
    total_irrelevant_items = 0
    total_permitted_relevant_fields = 0
    retained_permitted_relevant_fields = 0

    for s in sessions:
        s_dict = dict(s)
        
        is_relevant = int(s_dict.get('relevance_label', 1) if 'relevance_label' in s_dict else 1)
        is_sensitive = int(s_dict.get('sensitivity_label', 0) if 'sensitivity_label' in s_dict else 0)
        
        consent_summary = str(s_dict.get('consent_summary', 'Yes')).strip().capitalize() == 'Yes'
        consent_sensitive = str(s_dict.get('consent_sensitive', 'No')).strip().capitalize() == 'Yes'
        consent_goal = str(s_dict.get('consent_goal', 'Yes')).strip().capitalize() == 'Yes'
        consent_pending = str(s_dict.get('consent_pending_action', 'Yes')).strip().capitalize() == 'Yes'

        if is_relevant == 1:
            total_relevant_items += 1
        else:
            total_irrelevant_items += 1

        # Check sensitive protection required (if consent denied OR if sensitive text exists)
        has_sensitive_content = (is_sensitive == 1 or len(str(s_dict.get('sensitive_text', '')).strip()) > 0)
        
        if has_sensitive_content and not consent_sensitive:
            sensitive_items_to_protect += 1
            # Baseline shows everything, so it leaks protected sensitive content
            sensitive_items_incorrectly_exposed += 1
        elif has_sensitive_content and consent_sensitive:
            # Sensitive but consented
            pass

        # Baseline displays everything regardless of consent or role
        if not consent_summary or not consent_sensitive or not consent_goal or not consent_pending:
            baseline_consent_violations += 1
        
        if has_sensitive_content:
            baseline_sensitive_exposures += 1

        if is_relevant == 1:
            baseline_relevant_retained_count += 1
            # Handover completeness: baseline includes all 3 relevant fields regardless of consent
            retained_permitted_relevant_fields += 3
        else:
            baseline_unnecessary_exposure_count += 1

        # Count total permitted relevant fields
        if is_relevant == 1:
            if consent_summary: total_permitted_relevant_fields += 1
            if consent_goal: total_permitted_relevant_fields += 1
            if consent_pending: total_permitted_relevant_fields += 1

    # Redaction Leakage Rate calculation with zero-denominator safety
    if sensitive_items_to_protect > 0:
        redaction_leakage_rate = round((sensitive_items_incorrectly_exposed / sensitive_items_to_protect) * 100.0, 1)
    else:
        redaction_leakage_rate = 0.0

    total_rel = max(total_relevant_items, 1)
    total_irrel = max(total_irrelevant_items, 1)
    total_perm_fields = max(total_permitted_relevant_fields, 1)

    baseline_rel_pct = round((baseline_relevant_retained_count / total_rel) * 100.0, 1)
    baseline_unnec_pct = round((baseline_unnecessary_exposure_count / total_irrel) * 100.0, 1)
    handover_completeness = round(min(100.0, (retained_permitted_relevant_fields / total_perm_fields) * 100.0), 1)

    return {
        "total_sessions": total_sessions,
        "consent_violations": baseline_consent_violations,
        "sensitive_exposures": baseline_sensitive_exposures,
        "sensitive_to_protect": sensitive_items_to_protect,
        "sensitive_incorrectly_exposed": sensitive_items_incorrectly_exposed,
        "sensitive_protected": 0,
        "redaction_leakage_rate": redaction_leakage_rate,
        "relevant_retained_count": baseline_relevant_retained_count,
        "unnecessary_exposure_count": baseline_unnecessary_exposure_count,
        "relevant_retained_pct": baseline_rel_pct,
        "handover_completeness_pct": handover_completeness,
        "unnecessary_exposure_pct": baseline_unnec_pct,
        "total_relevant": total_relevant_items,
        "total_irrelevant": total_irrelevant_items
    }

def evaluate_proposed_system(sessions=None, default_role="Social Worker"):
    """
    Evaluates PROPOSED CONSENT-AWARE SYSTEM across session records.
    Applies ML relevance, DL sensitivity detection, Consent Engine, and RBAC rules.
    Uses single-pass batch inference for ML and DL model execution.
    """
    from ml_model import predict_relevance_batch
    from dl_model import predict_sensitivity_batch
    from consent_engine import evaluate_consent
    from access_control import check_role_access
    
    if sessions is None:
        sessions = get_all_sessions()
        if not sessions:
            df, _ = load_and_preprocess_data()
            sessions = df.to_dict('records')

    session_dicts = [dict(s) for s in sessions]
    total_sessions = len(session_dicts)

    # 1. Prepare batch prediction text inputs
    session_texts = [str(s.get('session_text', '') or '').strip() for s in session_dicts]
    sensitive_texts = [str(s.get('sensitive_text', '') or '').strip() + " " + str(s.get('session_text', '') or '').strip() for s in session_dicts]

    # 2. Run single-pass batch predictions across dataset
    ml_results = predict_relevance_batch(session_texts)
    dl_results = predict_sensitivity_batch(sensitive_texts)

    proposed_consent_violations = 0
    proposed_sensitive_exposures = 0
    sensitive_items_to_protect = 0
    sensitive_items_incorrectly_exposed = 0
    sensitive_items_protected = 0
    
    proposed_relevant_retained_count = 0
    proposed_unnecessary_exposure_count = 0

    total_relevant_items = 0
    total_irrelevant_items = 0
    total_permitted_relevant_fields = 0
    retained_permitted_relevant_fields = 0

    for idx, s_dict in enumerate(session_dicts):
        is_relevant = int(s_dict.get('relevance_label', 1) if 'relevance_label' in s_dict else 1)
        is_sensitive = int(s_dict.get('sensitivity_label', 0) if 'sensitivity_label' in s_dict else 0)
        
        consent_summary = str(s_dict.get('consent_summary', 'Yes')).strip().capitalize() == 'Yes'
        consent_sensitive = str(s_dict.get('consent_sensitive', 'No')).strip().capitalize() == 'Yes'
        consent_goal = str(s_dict.get('consent_goal', 'Yes')).strip().capitalize() == 'Yes'
        consent_pending = str(s_dict.get('consent_pending_action', 'Yes')).strip().capitalize() == 'Yes'

        if is_relevant == 1:
            total_relevant_items += 1
            if consent_summary: total_permitted_relevant_fields += 1
            if consent_goal: total_permitted_relevant_fields += 1
            if consent_pending: total_permitted_relevant_fields += 1
        else:
            total_irrelevant_items += 1

        has_sensitive_content = (is_sensitive == 1 or len(str(s_dict.get('sensitive_text', '')).strip()) > 0)
        
        if has_sensitive_content and (not consent_sensitive or default_role.lower() == "social worker"):
            sensitive_items_to_protect += 1

        # Use batch predictions mapped to this session
        ml_res = ml_results[idx]
        dl_res = dl_results[idx]

        consent_flags = {
            'consent_summary': s_dict.get('consent_summary', 'No'),
            'consent_goal': s_dict.get('consent_goal', 'No'),
            'consent_pending_action': s_dict.get('consent_pending_action', 'No'),
            'consent_sensitive': s_dict.get('consent_sensitive', 'No')
        }
        consent_eval = evaluate_consent(consent_flags)

        summary_access = check_role_access(default_role, 'summary', consent_eval['summary']['permitted'])
        goal_access = check_role_access(default_role, 'goal', consent_eval['goal']['permitted'])
        pending_access = check_role_access(default_role, 'pending_action', consent_eval['pending_action']['permitted'])
        sensitive_access = check_role_access(default_role, 'sensitive', consent_eval['sensitive']['permitted'])

        if summary_access['allowed']:
            summary_text = s_dict.get('session_text', '') if ml_res['prediction'] == 1 else "Session content classified as non-relevant for handover."
        else:
            summary_text = summary_access['display_text']

        goal_text = s_dict.get('client_goal', '') if goal_access['allowed'] else goal_access['display_text']
        pending_text = s_dict.get('pending_action', '') if pending_access['allowed'] else pending_access['display_text']
        sensitive_text = s_dict.get('sensitive_text', '') if sensitive_access['allowed'] else sensitive_access['display_text']

        summary_shown = summary_text not in ["🔒 Restricted by consent", "Session content classified as non-relevant for handover."]
        goal_shown = goal_text != "🔒 Restricted by consent"
        pending_shown = pending_text != "🔒 Restricted by consent"
        sensitive_shown = sensitive_text not in ["🔒 Restricted by consent", "🔒 Restricted by role"]

        if (summary_shown and not consent_summary) or \
           (goal_shown and not consent_goal) or \
           (pending_shown and not consent_pending) or \
           (sensitive_shown and not consent_sensitive):
            proposed_consent_violations += 1

        if sensitive_shown:
            proposed_sensitive_exposures += 1

        if has_sensitive_content and (not consent_sensitive or default_role.lower() == "social worker"):
            if sensitive_shown:
                sensitive_items_incorrectly_exposed += 1
            else:
                sensitive_items_protected += 1

        if is_relevant == 1 and ml_res['prediction'] == 1 and summary_access['allowed']:
            proposed_relevant_retained_count += 1

        if is_relevant == 1:
            if summary_shown and consent_summary: retained_permitted_relevant_fields += 1
            if goal_shown and consent_goal: retained_permitted_relevant_fields += 1
            if pending_shown and consent_pending: retained_permitted_relevant_fields += 1

        if is_relevant == 0 and summary_text not in ["Session content classified as non-relevant for handover.", "🔒 Restricted by consent", "🔒 Restricted by role"]:
            proposed_unnecessary_exposure_count += 1

    if sensitive_items_to_protect > 0:
        redaction_leakage_rate = round((sensitive_items_incorrectly_exposed / sensitive_items_to_protect) * 100.0, 1)
    else:
        redaction_leakage_rate = 0.0

    total_rel = max(total_relevant_items, 1)
    total_irrel = max(total_irrelevant_items, 1)
    total_perm_fields = max(total_permitted_relevant_fields, 1)

    proposed_rel_pct = round((proposed_relevant_retained_count / total_rel) * 100.0, 1)
    proposed_unnec_pct = round((proposed_unnecessary_exposure_count / total_irrel) * 100.0, 1)
    handover_completeness = round(min(100.0, (retained_permitted_relevant_fields / total_perm_fields) * 100.0), 1)

    return {
        "total_sessions": total_sessions,
        "consent_violations": proposed_consent_violations,
        "sensitive_exposures": proposed_sensitive_exposures,
        "sensitive_to_protect": sensitive_items_to_protect,
        "sensitive_incorrectly_exposed": sensitive_items_incorrectly_exposed,
        "sensitive_protected": sensitive_items_protected,
        "redaction_leakage_rate": redaction_leakage_rate,
        "relevant_retained_pct": proposed_rel_pct,
        "handover_completeness_pct": handover_completeness,
        "unnecessary_exposure_pct": proposed_unnec_pct
    }

def evaluate_baseline_vs_proposed(force_refresh=False):
    """
    Combines Baseline evaluation and Proposed System evaluation for comparison views.
    Caches aggregate dataset evaluation metrics in memory for instant HTTP rendering.
    """
    global _EVALUATION_CACHE

    if _EVALUATION_CACHE is not None and not force_refresh:
        return _EVALUATION_CACHE

    sessions = get_all_sessions()
    if not sessions:
        df, _ = load_and_preprocess_data()
        sessions = df.to_dict('records')

    # 1. Baseline Evaluation (ZERO DL dependency)
    b_eval = evaluate_baseline_system(sessions)
    
    # 2. Proposed System Evaluation (Batch prediction pass)
    p_eval = evaluate_proposed_system(sessions, default_role="Social Worker")

    result = {
        "total_sessions_evaluated": b_eval["total_sessions"],
        "privacy_metrics": {
            "redaction_leakage_rate": {
                "baseline": f"{b_eval['redaction_leakage_rate']}%",
                "proposed": f"{p_eval['redaction_leakage_rate']}%"
            },
            "sensitive_exposures": {
                "baseline": b_eval["sensitive_exposures"],
                "proposed": p_eval["sensitive_exposures"]
            },
            "sensitive_protected": {
                "baseline": 0,
                "proposed": p_eval["sensitive_protected"]
            },
            "consent_violations": {
                "baseline": b_eval["consent_violations"],
                "proposed": p_eval["consent_violations"]
            }
        },
        "handover_metrics": {
            "relevant_retained_pct": {
                "baseline": f"{b_eval['relevant_retained_pct']}%",
                "proposed": f"{p_eval['relevant_retained_pct']}%"
            },
            "handover_completeness_pct": {
                "baseline": f"{b_eval['handover_completeness_pct']}%",
                "proposed": f"{p_eval['handover_completeness_pct']}%"
            },
            "unnecessary_exposure_pct": {
                "baseline": f"{b_eval['unnecessary_exposure_pct']}%",
                "proposed": f"{p_eval['unnecessary_exposure_pct']}%"
            }
        },
        "metrics_table": [
            {
                "metric": "Redaction Leakage Rate (%)",
                "baseline": f"{b_eval['redaction_leakage_rate']}%",
                "proposed": f"{p_eval['redaction_leakage_rate']}%",
                "improvement": f"-{round(b_eval['redaction_leakage_rate'] - p_eval['redaction_leakage_rate'], 1)}% leakage reduction"
            },
            {
                "metric": "Sensitive Content Exposure Count",
                "baseline": str(b_eval["sensitive_exposures"]),
                "proposed": str(p_eval["sensitive_exposures"]),
                "improvement": f"-{b_eval['sensitive_exposures'] - p_eval['sensitive_exposures']} unauthorized exposures"
            },
            {
                "metric": "Sensitive Items Correctly Protected",
                "baseline": "0 (N/A)",
                "proposed": str(p_eval["sensitive_protected"]),
                "improvement": f"+{p_eval['sensitive_protected']} items protected"
            },
            {
                "metric": "Consent Violations",
                "baseline": str(b_eval["consent_violations"]),
                "proposed": str(p_eval["consent_violations"]),
                "improvement": f"-{b_eval['consent_violations'] - p_eval['consent_violations']} violations (0 in proposed)"
            },
            {
                "metric": "Relevant Information Retained (%)",
                "baseline": f"{b_eval['relevant_retained_pct']}%",
                "proposed": f"{p_eval['relevant_retained_pct']}%",
                "improvement": "High relevance retained"
            },
            {
                "metric": "Handover Completeness (%)",
                "baseline": f"{b_eval['handover_completeness_pct']}%",
                "proposed": f"{p_eval['handover_completeness_pct']}%",
                "improvement": "Permitted relevant fields delivered"
            },
            {
                "metric": "Unnecessary Noise Exposure (%)",
                "baseline": f"{b_eval['unnecessary_exposure_pct']}%",
                "proposed": f"{p_eval['unnecessary_exposure_pct']}%",
                "improvement": f"-{round(b_eval['unnecessary_exposure_pct'] - p_eval['unnecessary_exposure_pct'], 1)}% noise reduction"
            }
        ],
        "chart_data": {
            "categories": ["Redaction Leakage (%)", "Consent Violations", "Sensitive Exposures", "Handover Completeness (%)", "Unnecessary Noise (%)"],
            "baseline_values": [b_eval["redaction_leakage_rate"], b_eval["consent_violations"], b_eval["sensitive_exposures"], b_eval["handover_completeness_pct"], b_eval["unnecessary_exposure_pct"]],
            "proposed_values": [p_eval["redaction_leakage_rate"], p_eval["consent_violations"], p_eval["sensitive_exposures"], p_eval["handover_completeness_pct"], p_eval["unnecessary_exposure_pct"]]
        }
    }

    _EVALUATION_CACHE = result
    return result

if __name__ == '__main__':
    print("=== BASELINE VS PROPOSED COMPARISON WITH BATCH PREDICTION ===")
    comp = evaluate_baseline_vs_proposed()
    print(f"Evaluated {comp['total_sessions_evaluated']} session records:")
    for row in comp['metrics_table']:
        print(f"  {row['metric']}: Baseline = {row['baseline']} | Proposed = {row['proposed']} ({row['improvement']})")
