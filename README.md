# Youth Helpline Handover – Consent-Aware Continuity System

GitHub Repository: [https://github.com/madhumithabcy24-source/consent-aware-handover-solution](https://github.com/madhumithabcy24-source/consent-aware-handover-solution)

> [!IMPORTANT]
> **DISCLAIMER**: The project uses synthetic/de-identified data only and is not intended for real clinical decision-making. This project is a proof-of-concept prototype for educational/evaluation purposes and does not claim production readiness.

---

## 1. Project Title
**Youth Helpline Handover – Consent-Aware Continuity System**  
*Consent-Aware Continuity Summary System for Youth Helpline Counsellor and Social-Worker Handovers*

---

## 2. Problem Statement
When a youth helpline client is transferred from one counsellor or social worker to another, incomplete, unstructured, or un-consented handovers force the client to repeatedly recount distressing personal background details. This creates client frustration, care delay, and potential re-traumatization. Conversely, sharing sensitive notes without explicit client consent violates privacy and breaches professional trust.

---

## 3. Objective
To design and build a working, explainable Python/Flask continuity system that combines Machine Learning (ML) relevance classification, Deep Learning (DL) sensitivity detection, a Consent Safety Engine, and Role-Based Access Control (RBAC) to generate safe, relevant, and privacy-compliant handover summaries.

---

## 4. Key Features
- **Consent-Aware Continuity Summaries**: Structures session history, goals, pending actions, and sensitive notes while respecting consent.
- **Consent Safety Engine (FINAL Authority)**: Unconditional consent enforcement where client choices override all ML/DL model predictions.
- **Role-Based Access Control (RBAC)**: Differential visibility for `Counsellor` (clinical care scope) vs `Social Worker` (community care scope).
- **Real-Time Consent Management UI**: Edit or revoke consent with immediate redaction effect on the next summary generation.
- **Low-Confidence Human Review Flags**: Prominent warning banner when ML/DL prediction confidence drops below 70%.
- **Quantitative Model Evaluation**: Test-split calculation of Accuracy, Precision, Recall, F1-Score, and Confusion Matrices.
- **Redaction Leakage Rate Metric**: Empirical measurement of privacy protection against raw baseline handovers.
- **7 Automated Edge/Failure Test Cases**: Live web and terminal verification of system resilience under failure conditions.
- **Security Hardening & Zero-Sensitive Audit Logging**: Secure Flask cookies, password hashing compatibility, input escaping, and audit logs excluding raw sensitive text.

---

## 5. Architecture
See full architectural details in [`docs/architecture.md`](docs/architecture.md).

```
User (Counsellor / Social Worker)
       ↓
Flask Web Interface (HTTP/HTTPS Sessions)
       ↓
Authentication & RBAC Enforcement
       ↓
Session Data Retrieval (SQLite youth_helpline.db)
       ↓
Data Preprocessing Pipeline
       ↓
 ┌──────────────────────────────────────────────┐
 │ ML Relevance Model (TF-IDF + Logistic Reg)   │
 └──────────────────────────────────────────────┘
       ↓
 ┌──────────────────────────────────────────────┐
 │ DL Sensitivity Model (Keras Embedding+LSTM)  │
 └──────────────────────────────────────────────┘
       ↓
Consent Safety Engine (FINAL AUTHORITY LAYER)
       ↓
Role-Based Access Control Enforcement Layer
       ↓
Continuity Summary Generator (Low-Confidence Flags)
       ↓
Handover Output View / Audit Log & Evaluation
```

---

## 6. Technology Stack
- **Core Logic & Web Framework**: Python 3.13, Flask 3.1.0
- **Database**: SQLite3 (`youth_helpline.db`)
- **Data Science & ML**: Pandas, NumPy, Scikit-learn (TF-IDF Vectorizer + Logistic Regression)
- **Deep Learning**: TensorFlow / Keras 2.19.1 (`TextVectorization` + `Embedding` + `LSTM`)
- **Frontend & Visualizations**: HTML5, CSS3 (Dark Theme), Vanilla JavaScript, Chart.js

---

## 7. Machine Learning (ML) Model
- **Task**: Binary relevance classification (`relevance_label`: 1 = Relevant for handover, 0 = Non-relevant conversational noise).
- **Architecture**: TF-IDF Feature Extraction (max 500 features, 1-2 n-grams) + Logistic Regression.
- **Rationale**: Highly explainable, fast training on small/synthetic datasets, provides calibrated probability scores for confidence calculation.

---

## 8. Deep Learning (DL) Model
- **Task**: Binary sensitivity detection (`sensitivity_label`: 1 = Contains sensitive disclosures, 0 = Non-sensitive notes).
- **Architecture**: Sequential model using `TextVectorization` -> `Embedding` (32-dim) -> `LSTM` (16 units with dropout) -> `Dense` (Sigmoid output).
- **Rationale**: Captures non-linear sequence patterns in text tokens for sensitivity detection.

---

## 9. Consent Mechanism
- **Rule 1**: Consent is the **FINAL AUTHORITY**.
- **Rule 2**: ML and DL predictions **NEVER** override client consent.
- **Rule 3**: Role permissions **NEVER** override explicit client denial.
- **Rule 4**: Field-by-field partial consent is respected independently.
- **Rule 5**: Revocation takes effect immediately for newly generated handovers.

---

## 10. Role-Based Access Control (RBAC)
- **Counsellor Role**: Clinical care scope. Allowed to view sensitive disclosures **only if client consent is granted**.
- **Social Worker Role**: Community care scope. Sensitive disclosures are restricted (`🔒 Restricted by role`) by default even if client consented.

---

## 11. Dataset Description
- **File**: `data/synthetic_sessions.csv`
- **Total Records**: 105 synthetic session records spanning 25 unique synthetic clients.
- **Fields**: `client_id`, `session_id`, `session_text`, `client_goal`, `pending_action`, `sensitive_text`, `consent_summary`, `consent_goal`, `consent_pending_action`, `consent_sensitive`, `recommended_role`, `relevance_label`, `sensitivity_label`.
- **Note on Voice Contacts**: In a real-world youth helpline, contacts occur via chat and phone calls. In this MVP, voice contacts are represented as synthetic transcribed text marked with `[Voice Transcript]`.

---

## 12. Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/madhumithabcy24-source/consent-aware-handover-solution.git
cd consent-aware-handover-solution

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment (Windows)
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 13. How to Run Locally
```bash
# 1. Preprocess synthetic dataset
python preprocess.py

# 2. Train ML Relevance Model
python ml_model.py

# 3. Train DL Sensitivity Model
python dl_model.py

# 4. Launch Flask Application
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 14. Demo Login Credentials
| Role | Username | Password | Access Scope |
|------|----------|----------|--------------|
| **Counsellor** | `counsellor` | `1234` | Clinical care scope: Full handover summary, goals, action items, and sensitive disclosures (when consented). |
| **Social Worker** | `socialworker` | `1234` | Community care scope: Handover summary, goals, action items. Sensitive disclosures restricted by default. |

---

## 15. Testing Instructions
Run automated edge/failure and flow test suites:
```bash
# Run 7 mandatory edge/failure test cases
python tests/test_system.py

# Run 10 end-to-end user flow integration tests
python tests/test_all_flows.py
```

---

## 16. Evaluation Metrics
Evaluated on test split predictions and dataset ground-truth:
- **ML Relevance Model**: Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
- **DL Sensitivity Model**: Accuracy, Precision, Recall, F1-Score, Confusion Matrix.
- **Privacy Metrics**: Redaction Leakage Rate, Sensitive Exposure Count, Items Protected, Consent Violations.
- **Handover Metrics**: Relevant Information Retained %, Handover Completeness %, Unnecessary Exposure %.

---

## 17. Baseline vs Proposed Explanation
- **Baseline System**: Un-filtered handover displaying raw text without ML relevance, DL sensitivity detection, consent checking, or role restrictions. Exposes confidential disclosures even when consent is denied.
- **Proposed System**: Consent-aware handover applying ML relevance filtering, DL sensitivity detection, Consent Engine rules, and RBAC role restrictions, achieving a 0.0% Redaction Leakage Rate.

---

## 18. Failure Cases
Verifies 7 explicit edge/failure scenarios in `/test-cases` and `tests/test_system.py`:
1. **TEST 1**: Consent denied -> Information hidden.
2. **TEST 2**: Sensitive content + consent denied -> Hidden regardless of ML/DL output.
3. **TEST 3**: Social Worker attempts access to restricted sensitive notes -> Access denied by role.
4. **TEST 4**: Consent revoked -> Next handover reflects revocation immediately.
5. **TEST 5**: Partial consent -> Only permitted fields displayed.
6. **TEST 6**: Malformed/incomplete input -> Safely validated without crashing.
7. **TEST 7**: Sensitive content missed by DL model (DL false negative) -> Consent/RBAC still protect privacy.

---

## 19. Privacy & Security Considerations
- **Secure Flask Sessions**: `HTTPOnly` cookies, `SameSite=Lax`, 30-minute session expiration.
- **Password Hashing**: Werkzeug password hashing support.
- **Input Sanitization**: HTML escaping using `markupsafe.escape()` and parameterized SQL queries.
- **Zero-Sensitive Audit Logging**: Audit logs record event metadata (e.g. `Sensitive: Restricted`) without raw sensitive text.

---

## 20. Risk Register Reference
Refer to [`docs/risk_register.md`](docs/risk_register.md) for full risk matrix, impacts, likelihoods, and mitigations across 10 identified system risks.

---

## 21. Limitations
- Evaluated on a synthetic dataset of 105 session records.
- Sensitivity detection model is a lightweight pattern classifier for synthetic notes.
- Voice phone contacts are represented as pre-transcribed text strings.
- Intended for college demonstration, not clinical production deployment.

---

## 22. Future Work
- Integration with real-time automatic speech-to-text (STT) engines for live phone audio.
- Transformer-based classification models (e.g. DistilBERT) for fine-grained clinical entity extraction.
- Enterprise single sign-on (OAuth2 / SAML) and zero-trust encryption at rest.

---

## 23. GitHub Repository Information
- **Repository URL**: [https://github.com/madhumithabcy24-source/consent-aware-handover-solution](https://github.com/madhumithabcy24-source/consent-aware-handover-solution)
- **Author**: Madhumitha (College Viva & Prototype Project)
