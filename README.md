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

## 🎓 VIVA EXPLANATION (College Viva Preparation)

### 1. What is the problem?
When a youth helpline client is transferred from one worker to another, incomplete handovers force the client to repeat sensitive personal experiences, causing frustration and re-traumatization.

### 2. Why do clients repeat information?
Handovers are often unstructured, missing key action items, or lacking permission to share sensitive details safely.

### 3. What is a continuity summary?
A concise, structured record containing relevant session history, goals, pending action items, and privacy status needed for seamless worker handovers.

### 4. What is consent-aware processing?
A governance framework where client privacy choices directly control whether specific data categories (summary, goal, pending action, sensitive notes) are shared or masked.

### 5. Why synthetic data?
Youth helpline interactions contain highly sensitive personal data. Using 100% synthetic, de-identified data ensures complete privacy safety during development and demonstration.

### 6. Why Python?
Python offers mature, standard data science libraries (Pandas, Scikit-learn, TensorFlow) and web framework integration (Flask).

### 7. Why Flask?
Flask is a lightweight, explainable Python web framework ideal for building demonstrable MVPs without complex boilerplate.

### 8. Why SQLite?
SQLite is a zero-configuration file-based database perfect for local college project demonstrations without external database server overhead.

### 9. Why TF-IDF?
Term Frequency-Inverse Document Frequency (TF-IDF) converts text into numerical feature vectors by weighting term importance relative to document frequency across the corpus.

### 10. Why Logistic Regression?
Logistic Regression is linear, highly explainable, fast to train on small text datasets, and outputs calibrated probability scores for confidence calculation.

### 11. Why Deep Learning?
Deep learning models learn non-linear sequence patterns in text that traditional linear models might miss when detecting sensitive topics.

### 12. Why LSTM?
Long Short-Term Memory (LSTM) recurrent neural networks retain sequential context over text token sequences, capturing phrase dependencies relevant to sensitivity.

### 13. What does the ML model do?
Classifies whether session text is relevant for worker handover (`relevance_label`: 1 = Relevant, 0 = Not Relevant) with a confidence percentage.

### 14. What does the DL model do?
Detects whether session text contains potentially sensitive disclosures (`sensitivity_label`: 1 = Sensitive, 0 = Non-sensitive).

### 15. Why can't ML/DL override consent?
AI predictions are probabilistic and can make errors. Ethical privacy principles demand that client consent is absolute: if consent is denied, data MUST NOT be displayed regardless of AI output.

### 16. How does role-based access work?
Counsellors can view sensitive disclosures only when client consent is granted. Social Workers are restricted from viewing sensitive clinical disclosures by default (`🔒 Restricted by role`).

### 17. What is the baseline?
A standard handover system that displays raw, unfiltered session content without ML relevance filtering, DL sensitivity detection, consent checks, or role restrictions.

### 18. How is the proposed system better?
It eliminates consent violations (reducing sensitive exposures to 0) while retaining high relevant content and filtering out unnecessary conversational noise.

### 19. What are the failure cases?
The system handles 5 key edge cases: consent denied, sensitive content + consent denied, unauthorized role access, missing fields, and real-time consent revocation.

### 20. How did you evaluate the system?
Using test-set confusion matrices, Accuracy, Precision, Recall, F1 scores, and an empirical Before/After comparison across all synthetic dataset records.

### 21. What are the limitations?
Small synthetic dataset size, basic prototype sensitivity classifier, text representation of voice calls, and local demo authentication.

### 22. What would you improve in the future?
Integration with speech-to-text engines for automated voice call transcription, transformer-based NLP models (e.g., DistilBERT), and enterprise role-based authentication (OAuth2/SSO).
