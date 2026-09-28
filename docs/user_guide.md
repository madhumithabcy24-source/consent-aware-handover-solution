# User Guide & Operational Walkthrough
## Youth Helpline Handover – Consent-Aware Continuity System

This document provides a step-by-step user guide for starting, operating, demonstrating, and evaluating the Youth Helpline Handover application.

---

### Step 1: How to Start the Application

1. Open your terminal or PowerShell window.
2. Navigate to the project root directory:
   ```bash
   cd C:\Users\madhu\.gemini\antigravity\scratch\youth_helpline_handover
   ```
3. Run the Flask application:
   ```bash
   python app.py
   ```
4. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

### Step 2: How to Login

The application provides two pre-configured demo user accounts:
- **Counsellor Role**:
  - **Username**: `counsellor`
  - **Password**: `1234`
- **Social Worker Role**:
  - **Username**: `socialworker`
  - **Password**: `1234`

Enter the credentials on the login screen (`/login`) and click **Sign In**.

---

### Step 3: How to Create a Session

1. Log in as a `counsellor`.
2. Click **Create Session** in the top navigation bar.
3. Fill in the session form:
   - **Client ID**: e.g., `C026`
   - **Session ID**: e.g., `S106`
   - **Session Notes / Voice Transcript**: Enter conversation summary notes (voice phone contacts are represented as synthetic text marked with `[Voice Transcript]`).
   - **Client Goal**: Enter the agreed coping or study goal.
   - **Pending Action**: Enter next follow-up steps.
   - **Sensitive Text**: Enter confidential personal disclosures.
   - **Consent Preferences**: Check or uncheck `Yes`/`No` for Summary, Goal, Pending Action, and Sensitive Notes.
4. Click **Create Session & Generate Handover**.

---

### Step 4: How Consent Works

- **Consent is the FINAL Authority**: Client consent preferences dictate information sharing.
- **Field-by-Field Consent**: Each field (Summary, Goal, Pending Action, Sensitive Notes) has an independent consent check.
- If consent for a category is set to `No`, the system outputs `🔒 Restricted by consent` regardless of ML or DL model predictions.

---

### Step 5: How Role-Based Visibility Works

- **Counsellor**: Has full clinical scope and can view sensitive disclosures **if client consent is granted**.
- **Social Worker**: Has community care scope. Sensitive clinical notes are restricted with `🔒 Restricted by role` **by default**, even if the client granted consent.

---

### Step 6: How to Generate a Handover

1. Navigate to **Sessions** (`/sessions`).
2. Click **View Handover** next to any session ID (e.g., `S001`).
3. The system processes the notes through ML relevance, DL sensitivity detection, Consent Engine, and RBAC, displaying the safe continuity summary.

---

### Step 7: How to View Baseline vs Proposed

1. Click **Baseline System** (`/baseline`) in the top navigation bar.
2. Select any session from the dropdown menu.
3. Compare the **Raw Unfiltered Baseline Card** (which exposes sensitive text even when consent is denied) against the **Proposed System Card** (which redacts protected text).
4. Review the empirical metric comparison table and visual Chart.js comparison chart.

---

### Step 8: How to View Evaluation

1. Click **Evaluation** (`/evaluation`) in the top navigation bar.
2. Review **Model Metrics**: Accuracy, Precision, Recall, F1-score, and Confusion Matrices for both ML relevance and DL sensitivity models.
3. Review **Privacy Metrics**: Redaction Leakage Rate (0.0% proposed), Sensitive Exposures, Items Protected, and Consent Violations.

---

### Step 9: How to Run Test Cases

1. **In Web Interface**: Click **Test Cases** (`/test-cases`) in the navigation bar to see live execution results for all 7 mandatory edge/failure test cases.
2. **From Terminal**:
   ```bash
   python tests/test_system.py
   python tests/test_all_flows.py
   ```

---

### Step 10: How to Logout

Click **Logout** in the right-hand corner of the top navigation bar. The session cookie will be invalidated immediately, and you will be redirected to the login screen.
