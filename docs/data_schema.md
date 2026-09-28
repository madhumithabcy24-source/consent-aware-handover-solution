# Data Schema Documentation
## Youth Helpline Handover – Consent-Aware Continuity System

### 1. SQLite Database Schema (`youth_helpline.db`)

#### Table: `users`
Stores user credentials and role assignments for system authentication and RBAC.

| Field Name | Data Type | Key / Constraint | Purpose |
|------------|-----------|------------------|---------|
| `id` | INTEGER | Primary Key (AUTOINCREMENT) | Unique auto-incrementing user identifier |
| `username` | TEXT | UNIQUE, NOT NULL | Account login username |
| `password` | TEXT | NOT NULL | Password string (Hashed using Werkzeug `generate_password_hash`) |
| `role` | TEXT | NOT NULL | User system role (`Counsellor` or `Social Worker`) |

---

#### Table: `sessions`
Stores synthetic client session history notes and consent preference flags.

| Field Name | Data Type | Key / Constraint | Purpose |
|------------|-----------|------------------|---------|
| `id` | INTEGER | Primary Key (AUTOINCREMENT) | Internal record identifier |
| `client_id` | TEXT | NOT NULL | Unique synthetic client identifier (e.g., `C001`) |
| `session_id` | TEXT | UNIQUE, NOT NULL | Unique helpline session identifier (e.g., `S001`) |
| `session_text` | TEXT | NOT NULL | Primary session conversation notes / voice transcript summary |
| `client_goal` | TEXT | NULLABLE | Client-stated self-management or coping goal |
| `pending_action` | TEXT | NULLABLE | Next steps or scheduled follow-up actions |
| `sensitive_text` | TEXT | NULLABLE | Potentially sensitive personal disclosures or clinical history |
| `consent_summary` | TEXT | DEFAULT 'Yes' | Client consent flag for sharing session summary notes |
| `consent_goal` | TEXT | DEFAULT 'Yes' | Client consent flag for sharing client goal |
| `consent_pending_action` | TEXT | DEFAULT 'Yes' | Client consent flag for sharing pending actions |
| `consent_sensitive` | TEXT | DEFAULT 'No' | Client consent flag for sharing sensitive personal history |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |

---

#### Table: `handover_logs`
Stores security audit logs for compliance tracking. **NO raw sensitive text is ever stored.**

| Field Name | Data Type | Key / Constraint | Purpose |
|------------|-----------|------------------|---------|
| `id` | INTEGER | Primary Key (AUTOINCREMENT) | Audit record identifier |
| `session_id` | TEXT | NOT NULL | Session ID associated with audit event |
| `user_role` | TEXT | NOT NULL | Role of user performing access (`Counsellor` or `Social Worker`) |
| `event_type` | TEXT | DEFAULT 'handover_access' | Type of audit event (`login`, `logout`, `handover_access`, `consent_filtering`, `role_denial`) |
| `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Audit event timestamp |
| `information_shared` | TEXT | NOT NULL | Summary of categories shared (e.g. `Summary: Shared, Goal: Shared`) |
| `information_restricted` | TEXT | NOT NULL | Summary of categories redacted (e.g. `Sensitive: Restricted by consent`) |

---

### 2. Synthetic Dataset Schema (`data/synthetic_sessions.csv`)

| Field Name | Data Type | Example Value | Description |
|------------|-----------|---------------|-------------|
| `client_id` | String | `C001` | Synthetic client identifier |
| `session_id` | String | `S001` | Synthetic session identifier |
| `session_text` | String | `[Voice Transcript] Client called Helpline...` | Helpline interaction summary or voice transcript |
| `client_goal` | String | `Develop study schedule...` | Client goal statement |
| `pending_action` | String | `Follow-up call next Tuesday.` | Follow-up task |
| `sensitive_text` | String | `Client disclosed private health history.` | Sensitive personal disclosures |
| `consent_summary` | String | `Yes` / `No` | Client consent preference for summary |
| `consent_goal` | String | `Yes` / `No` | Client consent preference for goal |
| `consent_pending_action` | String | `Yes` / `No` | Client consent preference for pending action |
| `consent_sensitive` | String | `Yes` / `No` | Client consent preference for sensitive notes |
| `recommended_role` | String | `Counsellor` / `Social Worker` | Recommended handover practitioner role |
| `relevance_label` | Integer | `1` (Relevant) / `0` (Irrelevant) | Ground-truth ML label for session relevance |
| `sensitivity_label` | Integer | `1` (Sensitive) / `0` (Non-sensitive) | Ground-truth DL label for content sensitivity |
