import os
import random
import pandas as pd
import numpy as np

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CSV_PATH = os.path.join(DATA_DIR, 'synthetic_sessions.csv')

# Templates for synthetic session generation
RELEVANT_SESSIONS = [
    "[Voice Transcript] Client called Helpline regarding severe exam anxiety and academic burnout. Discussed time management techniques.",
    "Chat session: Youth reported persistent sleep issues related to school stress and requested a follow-up coping plan.",
    "[Voice Transcript] Client discussed family communication breakdown and wanted strategies for assertive conversation.",
    "Chat session: Client sought guidance on managing panic symptoms during class presentations. Practiced deep breathing exercises.",
    "[Voice Transcript] Client requested assistance connecting with youth mentorship programs and academic tutoring resources.",
    "Chat session: Discussed conflict resolution with peers. Client set a target goal to talk to school counsellor.",
    "[Voice Transcript] Youth expressed feelings of isolation after moving to a new college campus and inquired about social clubs.",
    "Chat session: Client asked for advice on balancing part-time work with high school assignments and setting healthy boundaries.",
    "[Voice Transcript] Client reported feeling overwhelmed by parental expectations and requested stress reduction strategies.",
    "Chat session: Client wanted resources for grief support following the recent loss of a grandparent."
]

IRRELEVANT_SESSIONS = [
    "Chat session: Client asked if the helpline offers merchandise or stickers.",
    "[Voice Transcript] Caller inquired about office location and standard operational hours on public holidays.",
    "Chat session: Client sent accidental greetings and disconnected after 10 seconds.",
    "[Voice Transcript] Caller asked for technical support regarding their mobile phone settings.",
    "Chat session: Client commented on the weather and tested if the chat service was live.",
    "[Voice Transcript] Misdialed number; caller realized mistake and hung up after asking for local bus timing.",
    "Chat session: Client submitted blank messages repeatedly followed by a question about helpline hiring.",
    "[Voice Transcript] Brief connection test; client confirmed audio quality and thanked the operator."
]

CLIENT_GOALS = [
    "Develop structured study schedule and stress reduction techniques.",
    "Improve sleep hygiene and practice grounding exercises daily.",
    "Schedule follow-up meeting with school social worker.",
    "Connect with peer support network and local community youth group.",
    "Practice assertive communication with parents regarding academic choices.",
    "Build a weekly routine balancing part-time employment and study.",
    "Access bereavement counselling resources and guidance."
]

PENDING_ACTIONS = [
    "Follow-up check-in call scheduled for next Tuesday at 3:00 PM.",
    "Send digital mindfulness guide and grounding exercise PDF via email.",
    "Contact school guidance department with client consent.",
    "Provide list of local youth mental health support drop-in centers.",
    "Re-evaluate progress in next scheduled chat session on Friday.",
    "No pending action recorded."
]

SENSITIVE_TEXTS = [
    "Client disclosed private personal health history and emotional trauma details.",
    "Detailed private disclosure regarding past family dispute and personal medical treatment.",
    "Sensitive discussion regarding personal identity struggles and confidential family matters.",
    "Disclosed highly personal family hardship and past psychological treatment history.",
    "Shared confidential personal diary notes detailing deep emotional distress."
]

NON_SENSITIVE_TEXTS = [
    "No sensitive personal history disclosed during session.",
    "Standard academic planning conversation without sensitive personal disclosures.",
    "General inquiry regarding routine stress management techniques.",
    "Publicly available resource request regarding study strategies."
]

def generate_synthetic_dataset(num_records=105):
    """
    Generates realistic, completely synthetic session data for Youth Helpline Handovers.
    No real names, phone numbers, addresses, or actual client data are used.
    Voice contacts are represented as synthetic transcribed text marked with [Voice Transcript].
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    records = []

    for i in range(1, num_records + 1):
        client_num = (i % 25) + 1  # 25 unique synthetic clients
        client_id = f"C{client_num:03d}"
        session_id = f"S{i:03d}"
        
        is_relevant = 1 if (i % 4 != 0) else 0  # ~75% relevant
        is_sensitive = 1 if (i % 3 == 0) else 0   # ~33% sensitive
        
        if is_relevant == 1:
            session_text = random.choice(RELEVANT_SESSIONS) + f" (Ref code: #{100+i})"
            goal = random.choice(CLIENT_GOALS)
            pending = random.choice(PENDING_ACTIONS)
        else:
            session_text = random.choice(IRRELEVANT_SESSIONS)
            goal = "No specific long-term goal established."
            pending = "No pending action recorded." if random.random() > 0.3 else "General follow-up."

        if is_sensitive == 1:
            sensitive_text = random.choice(SENSITIVE_TEXTS)
        else:
            sensitive_text = random.choice(NON_SENSITIVE_TEXTS)

        # Consent preferences (Yes/No)
        # Edge case testing: varying consent combinations
        consent_summary = "Yes" if random.random() > 0.1 else "No"
        consent_goal = "Yes" if random.random() > 0.15 else "No"
        consent_pending_action = "Yes" if random.random() > 0.15 else "No"
        
        # Sensitive consent is denied more frequently to test consent engine
        consent_sensitive = "Yes" if (is_sensitive and random.random() > 0.5) else "No"

        recommended_role = "Counsellor" if (is_sensitive or random.random() > 0.5) else "Social Worker"

        records.append({
            "client_id": client_id,
            "session_id": session_id,
            "session_text": session_text,
            "client_goal": goal,
            "pending_action": pending,
            "sensitive_text": sensitive_text,
            "consent_summary": consent_summary,
            "consent_goal": consent_goal,
            "consent_pending_action": consent_pending_action,
            "consent_sensitive": consent_sensitive,
            "recommended_role": recommended_role,
            "relevance_label": is_relevant,
            "sensitivity_label": is_sensitive
        })

    df = pd.DataFrame(records)
    df.to_csv(CSV_PATH, index=False)
    print(f"[SUCCESS] Generated {len(df)} synthetic session records at '{CSV_PATH}'")
    return df

def load_and_preprocess_data():
    """
    Data Preprocessing Pipeline:
    - Load CSV (generate if not present)
    - Deduplicate records
    - Handle missing values
    - Normalize text strings
    - Convert Yes/No consent values to binary integers (1/0)
    - Returns cleaned DataFrame and basic dataset statistics
    """
    if not os.path.exists(CSV_PATH):
        df = generate_synthetic_dataset()
    else:
        df = pd.read_csv(CSV_PATH)

    # 1. Deduplicate
    initial_len = len(df)
    df = df.drop_duplicates(subset=['session_id']).copy()

    # 2. Handle missing values
    df['session_text'] = df['session_text'].fillna("No session text provided.")
    df['client_goal'] = df['client_goal'].fillna("No goal recorded.")
    df['pending_action'] = df['pending_action'].fillna("No pending action recorded.")
    df['sensitive_text'] = df['sensitive_text'].fillna("No sensitive text recorded.")

    # 3. Text normalization (lowercasing helper column for vectorizers)
    df['normalized_text'] = df['session_text'].astype(str).str.lower().str.strip()
    df['normalized_sensitive'] = df['sensitive_text'].astype(str).str.lower().str.strip()

    # 4. Map Yes/No consent to binary (1/0)
    consent_cols = ['consent_summary', 'consent_goal', 'consent_pending_action', 'consent_sensitive']
    for col in consent_cols:
        binary_col = col + "_num"
        df[binary_col] = df[col].astype(str).str.strip().str.capitalize().map({'Yes': 1, 'No': 0}).fillna(0).astype(int)

    # 5. Summary Statistics
    stats = {
        "total_sessions": len(df),
        "relevant_sessions": int(df['relevance_label'].sum()),
        "sensitive_sessions": int(df['sensitivity_label'].sum()),
        "consent_summary_granted": int(df['consent_summary_num'].sum()),
        "consent_sensitive_granted": int(df['consent_sensitive_num'].sum()),
        "consent_denied_sensitive": int(len(df) - df['consent_sensitive_num'].sum()),
        "deduplicated_count": initial_len - len(df)
    }

    return df, stats

if __name__ == '__main__':
    print("=== DATA PREPROCESSING PIPELINE ===")
    df, stats = load_and_preprocess_data()
    print("\nDataset Summary Statistics:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")
