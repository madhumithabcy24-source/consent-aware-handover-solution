"""
Evaluation Module for Consent-Aware Continuity Summary System.

Computes:
1. Actual ML & DL model performance metrics (Accuracy, Precision, Recall, F1, Confusion Matrix) on test split.
2. Empirical comparison between Baseline System vs Proposed System across all synthetic dataset records.
"""

import os
import pandas as pd
import numpy as np

from preprocess import load_and_preprocess_data
from ml_model import train_and_evaluate_ml
from access_control import check_role_access
from database import get_all_sessions

def get_model_evaluation_metrics():
    """Returns test set metrics for both ML Relevance and DL Sensitivity models."""
    ml_metrics = train_and_evaluate_ml()
    
    # Import build_and_train_dl dynamically when evaluation metrics page is loaded
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
    
    THIS FUNCTION HAS ZERO DEPENDENCY ON DEEP LEARNING MODELS OR KERAS/TENSORFLOW.
    The Baseline page and baseline evaluation use this function directly.
    """
    if sessions is None:
        sessions = get_all_sessions()
        if not sessions:
            df, _ = load_and_preprocess_data()
            sessions = df.to_dict('records')

    total_sessions = len(sessions)
    baseline_consent_violations = 0
    baseline_sensitive_exposures = 0
    baseline_relevant_retained_count = 0
    baseline_unnecessary_exposure_count = 0

    total_relevant_items = 0
    total_irrelevant_items = 0

    for s in sessions:
        s_dict = dict(s)
        
        # Ground truth / inputs
        is_relevant = int(s_dict.get('relevance_label', 1) if 'relevance_label' in s_dict else 1)
        is_sensitive = int(s_dict.get('sensitivity_label', 0) if 'sensitivity_label' in s_dict else 0)
        
        consent_summary = str(s_dict.get('consent_summary', 'Yes')).strip().capitalize() == 'Yes'
        consent_sensitive = str(s_dict.get('consent_sensitive', 'No')).strip().capitalize() == 'Yes'

        if is_relevant == 1:
            total_relevant_items += 1
        else:
            total_irrelevant_items += 1

        # Baseline displays everything regardless of consent or role
        # Consent violation occurs if raw content is shown when consent = No
        if not consent_summary or not consent_sensitive:
            baseline_consent_violations += 1
        
        # Sensitive exposure occurs whenever sensitive text is present
        if is_sensitive == 1 or len(str(s_dict.get('sensitive_text', ''))) > 0:
            baseline_sensitive_exposures += 1

        if is_relevant == 1:
            baseline_relevant_retained_count += 1
        else:
            baseline_unnecessary_exposure_count += 1

    total_rel = max(total_relevant_items, 1)
    total_irrel = max(total_irrelevant_items, 1)

    baseline_rel_pct = round((baseline_relevant_retained_count / total_rel) * 100.0, 1)
    baseline_unnec_pct = round((baseline_unnecessary_exposure_count / total_irrel) * 100.0, 1)

    return {
        "total_sessions": total_sessions,
        "consent_violations": baseline_consent_violations,
        "sensitive_exposures": baseline_sensitive_exposures,
        "relevant_retained_count": baseline_relevant_retained_count,
        "unnecessary_exposure_count": baseline_unnecessary_exposure_count,
        "relevant_retained_pct": baseline_rel_pct,
        "unnecessary_exposure_pct": baseline_unnec_pct,
        "total_relevant": total_relevant_items,
        "total_irrelevant": total_irrelevant_items
    }

def evaluate_proposed_system(sessions=None):
    """
    Evaluates PROPOSED CONSENT-AWARE SYSTEM across session records.
    Applies ML relevance, DL sensitivity detection, Consent Engine, and RBAC rules.
    """
    from summary_generator import generate_continuity_summary
    
    if sessions is None:
        sessions = get_all_sessions()
        if not sessions:
            df, _ = load_and_preprocess_data()
            sessions = df.to_dict('records')

    proposed_consent_violations = 0
    proposed_sensitive_exposures = 0
    proposed_relevant_retained_count = 0
    proposed_unnecessary_exposure_count = 0

    total_relevant_items = 0
    total_irrelevant_items = 0

    for s in sessions:
        s_dict = dict(s)
        is_relevant = int(s_dict.get('relevance_label', 1) if 'relevance_label' in s_dict else 1)
        
        consent_summary = str(s_dict.get('consent_summary', 'Yes')).strip().capitalize() == 'Yes'
        consent_sensitive = str(s_dict.get('consent_sensitive', 'No')).strip().capitalize() == 'Yes'

        if is_relevant == 1:
            total_relevant_items += 1
        else:
            total_irrelevant_items += 1

        summary_obj = generate_continuity_summary(s_dict, user_role="Social Worker")

        summary_shown = summary_obj['summary_text'] not in ["🔒 Restricted by consent", "Session content classified as non-relevant for handover."]
        sensitive_shown = summary_obj['sensitive_text'] not in ["🔒 Restricted by consent", "🔒 Restricted by role"]

        if (summary_shown and not consent_summary) or (sensitive_shown and not consent_sensitive):
            proposed_consent_violations += 1

        if sensitive_shown:
            proposed_sensitive_exposures += 1

        if is_relevant == 1 and summary_obj['ml_relevance'] == "Relevant" and summary_obj['access_details']['summary']['allowed']:
            proposed_relevant_retained_count += 1

        if is_relevant == 0 and summary_obj['summary_text'] not in ["Session content classified as non-relevant for handover.", "🔒 Restricted by consent", "🔒 Restricted by role"]:
            proposed_unnecessary_exposure_count += 1

    total_rel = max(total_relevant_items, 1)
    total_irrel = max(total_irrelevant_items, 1)

    proposed_rel_pct = round((proposed_relevant_retained_count / total_rel) * 100.0, 1)
    proposed_unnec_pct = round((proposed_unnecessary_exposure_count / total_irrel) * 100.0, 1)

    return {
        "consent_violations": proposed_consent_violations,
        "sensitive_exposures": proposed_sensitive_exposures,
        "relevant_retained_pct": proposed_rel_pct,
        "unnecessary_exposure_pct": proposed_unnec_pct
    }

def evaluate_baseline_vs_proposed():
    """
    Combines Baseline evaluation and Proposed System evaluation for comparison views.
    Separates baseline system logic completely from proposed system model logic.
    """
    sessions = get_all_sessions()
    if not sessions:
        df, _ = load_and_preprocess_data()
        sessions = df.to_dict('records')

    # 1. Baseline Evaluation (ZERO DL dependency)
    b_eval = evaluate_baseline_system(sessions)
    
    # 2. Proposed System Evaluation
    p_eval = evaluate_proposed_system(sessions)

    return {
        "total_sessions_evaluated": b_eval["total_sessions"],
        "metrics_table": [
            {
                "metric": "Consent Violations",
                "baseline": str(b_eval["consent_violations"]),
                "proposed": str(p_eval["consent_violations"]),
                "improvement": f"-{b_eval['consent_violations'] - p_eval['consent_violations']} violations"
            },
            {
                "metric": "Sensitive Content Exposure",
                "baseline": str(b_eval["sensitive_exposures"]),
                "proposed": str(p_eval["sensitive_exposures"]),
                "improvement": f"-{b_eval['sensitive_exposures'] - p_eval['sensitive_exposures']} exposures"
            },
            {
                "metric": "Relevant Information Retained (%)",
                "baseline": f"{b_eval['relevant_retained_pct']}%",
                "proposed": f"{p_eval['relevant_retained_pct']}%",
                "improvement": "High relevance retained"
            },
            {
                "metric": "Unnecessary Exposure (%)",
                "baseline": f"{b_eval['unnecessary_exposure_pct']}%",
                "proposed": f"{p_eval['unnecessary_exposure_pct']}%",
                "improvement": f"-{round(b_eval['unnecessary_exposure_pct'] - p_eval['unnecessary_exposure_pct'], 1)}% reduction"
            }
        ],
        "chart_data": {
            "categories": ["Consent Violations", "Sensitive Exposures", "Relevant Retained (%)", "Unnecessary Noise (%)"],
            "baseline_values": [b_eval["consent_violations"], b_eval["sensitive_exposures"], b_eval["relevant_retained_pct"], b_eval["unnecessary_exposure_pct"]],
            "proposed_values": [p_eval["consent_violations"], p_eval["sensitive_exposures"], p_eval["relevant_retained_pct"], p_eval["unnecessary_exposure_pct"]]
        }
    }

if __name__ == '__main__':
    print("=== BASELINE VS PROPOSED COMPARISON ===")
    comp = evaluate_baseline_vs_proposed()
    print(f"Evaluated {comp['total_sessions_evaluated']} session records:")
    for row in comp['metrics_table']:
        print(f"  {row['metric']}: Baseline = {row['baseline']} | Proposed = {row['proposed']} ({row['improvement']})")
