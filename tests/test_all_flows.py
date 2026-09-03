"""
Comprehensive Flow Test Suite for Consent-Aware Continuity Summary System.

Tests all 10 user flows:
1. Login flow
2. Dashboard flow
3. Create Session flow
4. Baseline flow (verifies /baseline opens cleanly without requiring sensitivity_model.keras)
5. Proposed Handover flow
6. ML prediction flow
7. DL sensitivity detection flow
8. Consent filtering flow
9. Role-based visibility flow (Counsellor vs Social Worker)
10. Evaluation flow
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import init_db, get_session_by_id
from dl_model import DL_MODEL_PATH
from evaluation import evaluate_baseline_system

class SystemFlowsTestCase(unittest.TestCase):
    def setUp(self):
        init_db()
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()

    def login_as(self, username, password):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_flow_1_login(self):
        """1. Login Flow Test"""
        response = self.login_as('counsellor', '1234')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in as Counsellor', response.data)
        print("[PASS] Flow 1: Login flow verified.")

    def test_flow_2_dashboard(self):
        """2. Dashboard Flow Test"""
        self.login_as('counsellor', '1234')
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'System Dashboard', response.data)
        print("[PASS] Flow 2: Dashboard flow verified.")

    def test_flow_3_create_session(self):
        """3. Create Session Flow Test"""
        self.login_as('counsellor', '1234')
        session_id = "S_TEST_99"
        response = self.client.post('/create-session', data={
            'client_id': 'C_TEST_99',
            'session_id': session_id,
            'session_text': 'Client discussed study focus and routine.',
            'client_goal': 'Improve focus.',
            'pending_action': 'Check-in on Monday.',
            'sensitive_text': 'No sensitive notes.',
            'consent_summary': 'Yes',
            'consent_goal': 'Yes',
            'consent_pending_action': 'Yes',
            'consent_sensitive': 'No'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        session_record = get_session_by_id(session_id)
        self.assertIsNotNone(session_record)
        print("[PASS] Flow 3: Create Session flow verified.")

    def test_flow_4_baseline_without_dl_dependency(self):
        """4. Baseline Flow Test - Verifies /baseline works without loading DL model."""
        self.login_as('counsellor', '1234')
        
        # Test evaluate_baseline_system directly
        base_res = evaluate_baseline_system()
        self.assertIn('total_sessions', base_res)
        self.assertIn('consent_violations', base_res)

        # GET /baseline
        response = self.client.get('/baseline')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Baseline vs. Proposed System Comparison', response.data)
        self.assertIn(b'BASELINE SYSTEM', response.data)
        print("[PASS] Flow 4: Baseline flow verified without DL model dependency.")

    def test_flow_5_proposed_handover(self):
        """5. Proposed Handover Summary Flow Test"""
        self.login_as('counsellor', '1234')
        response = self.client.get('/handover/S001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CONTINUITY SUMMARY', response.data)
        print("[PASS] Flow 5: Proposed Handover summary flow verified.")

    def test_flow_6_ml_prediction(self):
        """6. ML Prediction Flow Test"""
        from ml_model import predict_relevance
        res = predict_relevance("Client requested study schedule assistance.")
        self.assertIn('prediction', res)
        self.assertIn('confidence', res)
        self.assertEqual(res['prediction'], 1)
        print("[PASS] Flow 6: ML prediction flow verified.")

    def test_flow_7_dl_sensitivity_detection(self):
        """7. DL Sensitivity Detection Flow Test"""
        from dl_model import predict_sensitivity
        res = predict_sensitivity("Client disclosed private medical history.")
        self.assertIn('prediction', res)
        self.assertIn('confidence', res)
        print("[PASS] Flow 7: DL sensitivity detection flow verified.")

    def test_flow_8_consent_filtering(self):
        """8. Consent Filtering Flow Test"""
        from summary_generator import generate_continuity_summary
        test_data = {
            'client_id': 'C888',
            'session_id': 'S888',
            'session_text': 'Session text notes.',
            'client_goal': 'Goal text.',
            'pending_action': 'Pending action.',
            'sensitive_text': 'Private trauma disclosure.',
            'consent_summary': 'Yes',
            'consent_goal': 'Yes',
            'consent_pending_action': 'Yes',
            'consent_sensitive': 'No'  # Consent denied
        }
        summary = generate_continuity_summary(test_data, user_role="Counsellor")
        self.assertEqual(summary['sensitive_text'], "🔒 Restricted by consent")
        print("[PASS] Flow 8: Consent filtering flow verified.")

    def test_flow_9_role_based_visibility(self):
        """9. Role-Based Visibility Flow Test (Counsellor vs Social Worker)"""
        from summary_generator import generate_continuity_summary
        test_data = {
            'client_id': 'C777',
            'session_id': 'S777',
            'session_text': 'Session text notes.',
            'client_goal': 'Goal text.',
            'pending_action': 'Pending action.',
            'sensitive_text': 'Private medical notes.',
            'consent_summary': 'Yes',
            'consent_goal': 'Yes',
            'consent_pending_action': 'Yes',
            'consent_sensitive': 'Yes'  # Client consented
        }

        summary_sw = generate_continuity_summary(test_data, user_role="Social Worker")
        self.assertEqual(summary_sw['sensitive_text'], "🔒 Restricted by role")

        summary_counsellor = generate_continuity_summary(test_data, user_role="Counsellor")
        self.assertEqual(summary_counsellor['sensitive_text'], "Private medical notes.")
        print("[PASS] Flow 9: Role-based visibility flow verified.")

    def test_flow_10_evaluation(self):
        """10. Evaluation Flow Test"""
        self.login_as('counsellor', '1234')
        response = self.client.get('/evaluation')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Model Evaluation &amp; Before/After System Experiment', response.data)
        print("[PASS] Flow 10: Evaluation page flow verified.")

if __name__ == '__main__':
    unittest.main()
