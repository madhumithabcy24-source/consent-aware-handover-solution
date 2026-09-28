# Architecture Documentation
## Youth Helpline Handover – Consent-Aware Continuity System

### 1. System Architecture Overview

The system processes client session history and generates role-tailored, privacy-compliant continuity summaries for Counsellor and Social Worker handovers.

```
                  ┌──────────────────────────────┐
                  │    User (Counsellor /        │
                  │      Social Worker)          │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │     Flask Web Interface      │
                  │   (Cookie/Session Auth)      │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │  Authentication & Security   │
                  │  (Role Injection & Audit)    │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │ SQLite Database (`sessions`) │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │  Preprocessing & Text Norm   │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
  ┌──────────────────────────────┐ ┌──────────────────────────────┐
  │  ML Relevance Classifier     │ │  DL Sensitivity Detector     │
  │  (TF-IDF + Logistic Reg)     │ │  (Keras Embedding + LSTM)    │
  └──────────────┬───────────────┘ └──────────────┬───────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │    CONSENT SAFETY ENGINE     │
                  │   (FINAL AUTHORITY LAYER)    │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │  ROLE-BASED ACCESS CONTROL   │
                  │  (Counsellor vs SocialWorker)│
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │ Continuity Summary Generator │
                  │ (Low-Confidence Flagging)    │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
  ┌──────────────────────────────┐ ┌──────────────────────────────┐
  │ Handover Output View (UI)    │ │ Audit Logs & Evaluation      │
  │ (Redacted / Permitted Notes) │ │ (No sensitive raw text log)  │
  └──────────────────────────────┘ └──────────────────────────────┘
```

---

### 2. Architectural Components

#### A. Presentation & Web Interface Layer (`app.py`, `templates/`)
- Built with Python Flask web framework.
- Secure Flask session cookies with `HTTPOnly`, `SameSite=Lax`, and 30-minute expiration.
- Dynamic Jinja2 templates auto-escape rendered output.

#### B. Preprocessing & Model Layer (`preprocess.py`, `ml_model.py`, `dl_model.py`)
- **Preprocessing**: Deduplication, text normalization, and lowercasing.
- **ML Relevance Model**: TF-IDF vectorization coupled with Logistic Regression predicting session note relevance for handover (`relevance_label`).
- **DL Sensitivity Model**: Keras `TextVectorization` + `Embedding` + `LSTM` network detecting sensitive personal disclosures (`sensitivity_label`).

#### C. Governance & Enforcement Layer (`consent_engine.py`, `access_control.py`)
- **Consent Safety Engine**: Serves as the **FINAL AUTHORITY**. ML and DL model predictions **NEVER** override explicit client consent.
- **Role-Based Access Control (RBAC)**: Enforces role permissions. Social Workers are restricted from viewing sensitive clinical disclosures even if model predicts non-sensitive or client consented.

#### D. Summary Generator & Audit Layer (`summary_generator.py`, `database.py`)
- Assembles continuity summaries and flags low-confidence predictions (< 70%) for human supervisor review.
- Writes structured security audit logs for login, logout, handover access, consent filtering, and role denial without storing raw sensitive text.

---

### 3. Emergency Override Governance & Privacy Risk Analysis

> [!WARNING]
> **Why Emergency Override is Restricted:**  
> An unrestricted emergency override toggle would allow operators to bypass client consent silently, introducing severe privacy violation risks, loss of client trust, and legal non-compliance under privacy frameworks (e.g., GDPR/HIPAA).

#### Emergency Override Governance Framework (Future Consideration):
1. **Authorization Threshold**: Override must require dual-authorization by a Clinical Lead and Legal Data Protection Officer.
2. **Mandatory Audit Logging**: Every override invocation must record timestamp, authorizing officer ID, clinical justification case number, and immutable hash.
3. **Automated Client Notification**: Post-emergency notification workflow to inform the client of consent override in accordance with helpline emergency care protocols.
