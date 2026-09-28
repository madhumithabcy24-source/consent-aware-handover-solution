# Risk Register & Privacy Analysis
## Youth Helpline Handover – Consent-Aware Continuity System

> [!IMPORTANT]
> **GOVERNANCE PRINCIPLE**:  
> Machine Learning (ML) relevance predictions and Deep Learning (DL) sensitivity predictions are **analytical assistance tools only**. They are **NEVER the final privacy authority**. Client consent preferences and Role-Based Access Control (RBAC) serve as absolute, un-bypassable enforcement layers.

---

### Risk Matrix Table

| Risk ID | Identified Risk Description | Impact | Likelihood | Mitigation Strategy |
|---------|-----------------------------|--------|------------|---------------------|
| **R-01** | **Sensitive Information Leakage**: Confidential notes exposed to unauthorized practitioner. | High | Low | **Consent & RBAC Enforcement**: Consent Engine and RBAC block sensitive fields prior to rendering regardless of model output. |
| **R-02** | **Incorrect ML Classification**: ML relevance model misclassifies important session notes as non-relevant. | Medium | Low | **Low-Confidence Flagging**: Predictions with < 70% confidence trigger a human review alert badge for supervisor inspection. |
| **R-03** | **DL False Negative**: DL sensitivity model predicts "Non-Sensitive" for text containing subtle distress. | High | Low | **Consent Fallback Defense**: Consent engine checks `consent_sensitive` preference independently of DL prediction. |
| **R-04** | **Consent Misconfiguration**: Client preference improperly registered or updated. | High | Low | **Field-by-Field Consent & Real-Time Management UI**: Dynamic consent editing with instant revocation effect on next summary. |
| **R-05** | **Unauthorized Role Access**: Social Worker attempts to view restricted clinical sensitive notes. | High | Low | **Backend Role Enforcement**: `check_role_access()` evaluates `session['role']` on the backend server, blocking client-side bypass. |
| **R-06** | **Session Hijacking / Data Exposure**: Session cookie tampered or intercepted. | Medium | Low | **Flask Session Hardening**: `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, 30-minute session timeout. |
| **R-07** | **Model Over-reliance**: Helpline staff blindly trust ML/DL outputs without clinical judgement. | Medium | Medium | **Prominent UI Indicators & Human-in-the-Loop Flags**: Displays explicit confidence scores and low-confidence review prompts. |
| **R-08** | **Synthetic Data Gap**: Model trained on synthetic data fails to generalize to nuanced clinical transcripts. | Medium | Medium | **De-identified Synthetic Disclaimer & Modular Pipeline**: Clear disclaimer that system is a proof-of-concept for synthetic data. |
| **R-09** | **Database Injection / Corruption**: Malicious input in session creation corrupts SQLite database. | High | Low | **Parameterized SQL Queries & HTML Input Escaping**: All database operations use `?` parameter placeholders and `markupsafe.escape()`. |
| **R-10** | **Audit Trail Contamination**: Sensitive clinical details leaked into system audit logs. | High | Low | **Zero-Sensitive Audit Logging**: Audit logger records category metadata status (e.g. `Sensitive: Restricted`) without raw text. |
