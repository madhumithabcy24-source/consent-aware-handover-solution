# Consent-Aware Continuity Summary System for Youth Helpline Handovers

A complete, working end-to-end MVP for a college project titled **"Consent-Aware Continuity Summary System for Youth Helpline Counsellor and Social-Worker Handovers"**.

It demonstrates a privacy-first, consent-aware NLP/ML pipeline that filters and structures youth helpline session handovers while strictly enforcing client consent and role-based access control (RBAC).

---

## 📌 Note on Voice Contact Representation
In a real-world youth helpline, client contacts occur via text chat and voice phone calls. In this MVP, **voice contacts are represented as synthetic transcribed text** (prefixed with `[Voice Transcript]`). The preprocessing and NLP pipeline ingests these transcribed logs identically to text chat logs.

---

## 🏗️ System Architecture

```text
Synthetic Dataset (CSV)
       ↓
Data Preprocessing (preprocess.py)
       ↓
ML Relevance Model (ml_model.py: TF-IDF + Logistic Regression)
       ↓
DL Sensitivity Model (dl_model.py: Keras Embedding + LSTM)
       ↓
Consent Engine (consent_engine.py)
       ↓
Role-Based Access Control (access_control.py)
       ↓
Summary Generator (summary_generator.py)
       ↓
Flask Backend & SQLite Database (app.py & database.py)
       ↓
Web Dashboard & Handover UI (HTML/CSS/JS)
```

---

## 🚀 Running the Project on Windows

Follow these step-by-step Windows commands to run the project:

### 1. Create Virtual Environment
```cmd
python -m venv venv
```

### 2. Activate Virtual Environment
```cmd
venv\Scripts\activate
```

### 3. Install Required Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Run Preprocessing & Synthetic Data Generation
```cmd
python preprocess.py
```

### 5. Train Machine Learning Relevance Model
```cmd
python ml_model.py
```

### 6. Train Deep Learning Sensitivity Model
```cmd
python dl_model.py
```

### 7. Run Automated Edge/Failure Test Suite
```cmd
python tests/test_system.py
```

### 8. Start Flask Web Application
```cmd
python app.py
```

Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Demo Login Accounts

| Role | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Counsellor** | `counsellor` | `1234` | Clinical care scope: Full handover summary, goals, action items, and sensitive disclosures (when explicitly consented). |
| **Social Worker** | `socialworker` | `1234` | Community/social care scope: Handover summary, goals, action items. Sensitive disclosures restricted by default. |

---

## 🛡️ Risk Register

| Risk Description | Severity | Mitigation Strategy Implemented |
| :--- | :--- | :--- |
| **1. Sensitive Information Exposure** | High | Unconditional Consent Engine filtering + RBAC role restrictions. |
| **2. Incorrect ML Relevance Prediction** | Medium | Human review warning flag when ML confidence < 70%. |
| **3. Incorrect DL Sensitivity Classification** | Medium | Treat DL output as warning indicator; consent always overrides. |
| **4. Missing Session Data Fields** | Low | Safe fallback defaults ("No pending action recorded"). |
| **5. Client Consent Changes / Revocation** | High | Evaluate consent dynamically on every handover request. |
| **6. Unauthorized Access to Handovers** | High | Role-based authentication and non-sensitive audit logging. |

---

## 📋 Stakeholder Assumptions

1. Youth helpline clients provide privacy consent choices regarding their session details.
2. Helpline counsellors create structured session notes and transcript logs.
3. Social workers receive permitted handover summaries for community follow-up.
4. The system is a decision-support tool; human professionals remain responsible for care decisions.
5. De-identified synthetic data is used for development and demonstration.

---

## ⚠️ System Limitations

- **Dataset Size:** Built and evaluated on a synthetic dataset of 105 session records.
- **Model Scope:** Prototype sensitive detector classifies text patterns; it does not diagnose clinical conditions.
- **Voice Transcription:** Voice phone contacts are represented as synthetic text transcripts.
- **Production Governance:** Real deployment would require HIPAA/GDPR compliance reviews, encryption at rest, and OAuth2/SAML integration.

---
## Review 1 – Current Project Status

### Project Progress

The project has progressed beyond the minimum Review 1 milestone and currently has a functional end-to-end MVP/prototype.

The Review 1 submission demonstrates the core workflow of a consent-aware youth helpline handover system.

### Completed Features

- Flask-based web application
- SQLite database integration
- Counsellor and Social Worker role-based login
- Session creation and management
- Consent-aware information sharing
- Role-based visibility of sensitive information
- ML-based handover relevance classification
- DL-based sensitive content detection
- Structured continuity summary generation
- Baseline vs Proposed comparison
- Evaluation metrics and results
- Failure and edge-case test scenarios
- Audit logging for handover activities
- Synthetic/de-identified dataset for testing
- Project documentation and user guidance

### Current Working Status

The core application workflow is functional and can be demonstrated through the web interface.

The system can process a synthetic session, apply relevance and sensitivity detection, enforce consent rules, apply role-based access control, and generate an appropriate handover summary.

### Planned Improvements

Further development will focus on:

- Additional testing with more diverse synthetic scenarios
- Improving ML/DL model performance
- More detailed error analysis
- Stakeholder/user validation
- Additional privacy and security hardening
- Improved deployment and reproducibility
- Final documentation and presentation preparation

### Review 1 Note

Although the functional MVP currently demonstrates most of the core system workflow, the project will continue to be refined and validated through the subsequent development stages.


