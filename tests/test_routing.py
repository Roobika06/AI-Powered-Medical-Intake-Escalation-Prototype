"""
tests/test_routing.py - Automated unit and integration tests for
validation, routing rules, fallback handling, and negated keywords.

All AI API calls are mocked - no internet or API key required.
"""

import unittest
from unittest.mock import MagicMock, patch
try:
    import pytest
except ImportError:
    pytest = None

from triage_engine import (
    validate_intake_form,
    route_submission,
    fallback_rule_based_analysis,
    analyze_intake_message,
    parse_and_validate_ai_json,
    ROUTE_PRIORITY,
    ROUTE_ROUTINE,
    ROUTE_GENERAL
)


class TestValidationLogic(unittest.TestCase):
    """Tests form validation rules and required field enforcement."""

    def test_valid_submission_passes(self):
        valid, err = validate_intake_form(
            patient_name="Jane Doe",
            contact_info="jane@example.com",
            symptoms="Mild dry cough and runny nose",
            patient_message="I'd like to book an appointment next week."
        )
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_missing_patient_name_rejected(self):
        valid, err = validate_intake_form(
            patient_name="",
            contact_info="555-0199",
            symptoms="Headache",
            patient_message="Need an appointment"
        )
        self.assertFalse(valid)
        self.assertIn("Patient Name is required", err)

    def test_whitespace_only_patient_name_rejected(self):
        valid, err = validate_intake_form(
            patient_name="   ",
            contact_info="555-0199",
            symptoms="Headache",
            patient_message="Need an appointment"
        )
        self.assertFalse(valid)
        self.assertIn("Patient Name is required", err)

    def test_missing_symptoms_rejected(self):
        valid, err = validate_intake_form(
            patient_name="Jane Doe",
            contact_info="jane@example.com",
            symptoms="",
            patient_message="Please call me back"
        )
        self.assertFalse(valid)
        self.assertIn("Symptom description is required", err)

    def test_missing_patient_message_rejected(self):
        valid, err = validate_intake_form(
            patient_name="Jane Doe",
            contact_info="jane@example.com",
            symptoms="Fever and chills",
            patient_message=""
        )
        self.assertFalse(valid)
        self.assertIn("Patient message is required", err)


class TestDeterministicRoutingRules(unittest.TestCase):
    """
    Tests the deterministic routing logic according to rules A through F.
    """

    def test_explicit_emergency_routes_to_priority_review(self):
        """Rule A: Explicit emergency request routes to priority human review."""
        route = route_submission(
            stated_intent="EMERGENCY_REQUEST",
            priority_human_review=True,
            is_valid_analysis=True
        )
        self.assertEqual(route, ROUTE_PRIORITY)

        # Even if priority_human_review was unexpectedly False, emergency intent must still route to priority
        route_alt = route_submission(
            stated_intent="EMERGENCY_REQUEST",
            priority_human_review=False,
            is_valid_analysis=True
        )
        self.assertEqual(route_alt, ROUTE_PRIORITY)

    def test_concerning_content_flag_overrides_routine_intent(self):
        """Rule B: A concerning-content flag overrides routine intent."""
        # Patient asked for routine appointment, but flagged with concerning content (e.g. chest pain)
        route = route_submission(
            stated_intent="ROUTINE_APPOINTMENT",
            priority_human_review=True,
            is_valid_analysis=True
        )
        self.assertEqual(route, ROUTE_PRIORITY, "Concerning content flag must override routine intent!")

    def test_clear_routine_request_routes_to_routine_appointment(self):
        """Rule C: Clear routine request routes to routine appointment only when no concern is detected."""
        route = route_submission(
            stated_intent="ROUTINE_APPOINTMENT",
            priority_human_review=False,
            is_valid_analysis=True
        )
        self.assertEqual(route, ROUTE_ROUTINE)

    def test_unclear_request_routes_to_general_human_review(self):
        """Rule D: An unclear/ambiguous request routes to general human review."""
        route = route_submission(
            stated_intent="OTHER_OR_UNCLEAR",
            priority_human_review=False,
            is_valid_analysis=True,
            concern_suspected=False
        )
        self.assertEqual(route, ROUTE_GENERAL)

    def test_unclear_request_with_concern_suspected_routes_to_priority(self):
        """Rule D extension: Unclear request with suspected concern routes to priority review."""
        route = route_submission(
            stated_intent="OTHER_OR_UNCLEAR",
            priority_human_review=False,
            is_valid_analysis=True,
            concern_suspected=True
        )
        self.assertEqual(route, ROUTE_PRIORITY)

    def test_invalid_ai_response_never_silently_routes_as_routine(self):
        """Rule D & F: An invalid AI response never silently routes as routine."""
        # Case 1: invalid analysis with no specific concern suspected -> GENERAL_HUMAN_REVIEW
        route_invalid_general = route_submission(
            stated_intent="ROUTINE_APPOINTMENT",
            priority_human_review=False,
            is_valid_analysis=False,
            concern_suspected=False
        )
        self.assertNotEqual(route_invalid_general, ROUTE_ROUTINE)
        self.assertEqual(route_invalid_general, ROUTE_GENERAL)

        # Case 2: invalid analysis with concern suspected -> PRIORITY_HUMAN_REVIEW
        route_invalid_priority = route_submission(
            stated_intent="ROUTINE_APPOINTMENT",
            priority_human_review=False,
            is_valid_analysis=False,
            concern_suspected=True
        )
        self.assertEqual(route_invalid_priority, ROUTE_PRIORITY)


class TestNegationAndHeuristics(unittest.TestCase):
    """
    Tests conservative heuristics and keyword negation.
    A message containing the word 'emergency' in a negated context must NOT be blindly
    classified as an emergency solely by keyword matching.
    """

    def test_negated_emergency_context_not_classified_as_emergency(self):
        """'This is not an emergency' must not trigger EMERGENCY_REQUEST."""
        symptoms = "Mild dry cough for 3 days"
        message = "This is definitely NOT an emergency, but I need to refill my prescription inhaler."
        
        result = fallback_rule_based_analysis(symptoms, message)
        
        # Must not be classified as EMERGENCY_REQUEST
        self.assertNotEqual(result["stated_intent"], "EMERGENCY_REQUEST")
        self.assertIn(result["stated_intent"], ["ROUTINE_APPOINTMENT", "OTHER_OR_UNCLEAR"])
        
        # Route determination
        route = route_submission(result["stated_intent"], result["priority_human_review"])
        self.assertNotEqual(route, ROUTE_PRIORITY)

    def test_explicit_emergency_triggers_priority(self):
        """Explicit emergency markers trigger EMERGENCY_REQUEST and priority review."""
        symptoms = "Severe pressure on chest"
        message = "Please call 911 right now I need an ambulance immediately!"
        
        result = fallback_rule_based_analysis(symptoms, message)
        self.assertEqual(result["stated_intent"], "EMERGENCY_REQUEST")
        self.assertTrue(result["priority_human_review"])
        
        route = route_submission(result["stated_intent"], result["priority_human_review"])
        self.assertEqual(route, ROUTE_PRIORITY)

    def test_concerning_symptoms_without_word_emergency_triggers_priority(self):
        """Subtle or serious red flags (e.g. facial droop, slurred speech) trigger priority review."""
        symptoms = "Sudden weakness in left arm and facial drooping"
        message = "I just woke up and my left side feels numb. Can I book a checkup next week?"
        
        result = fallback_rule_based_analysis(symptoms, message)
        self.assertTrue(result["priority_human_review"], "Red-flag symptom must trigger priority review")
        
        route = route_submission(result["stated_intent"], result["priority_human_review"])
        self.assertEqual(route, ROUTE_PRIORITY, "Must escalate to priority review even if patient asks for checkup")


class TestAIIntegrationAndFallback(unittest.TestCase):
    """Tests AI response parsing, API error handling, and safe fallback activation."""

    def test_ai_response_parsing_valid_json(self):
        raw_json = '''{
            "summary": "Patient requests annual checkup, reports no symptoms.",
            "stated_intent": "ROUTINE_APPOINTMENT",
            "priority_human_review": false,
            "review_reason": "Routine wellness exam with no acute complaints."
        }'''
        parsed = parse_and_validate_ai_json(raw_json)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["stated_intent"], "ROUTINE_APPOINTMENT")
        self.assertFalse(parsed["priority_human_review"])

    def test_ai_response_parsing_markdown_wrapped_json(self):
        raw_markdown = '''```json
        {
            "summary": "Severe chest pain radiating to arm.",
            "stated_intent": "EMERGENCY_REQUEST",
            "priority_human_review": true,
            "review_reason": "Cardiac red-flag symptoms reported."
        }
        ```'''
        parsed = parse_and_validate_ai_json(raw_markdown)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["stated_intent"], "EMERGENCY_REQUEST")
        self.assertTrue(parsed["priority_human_review"])

    def test_ai_response_parsing_malformed_json_returns_none(self):
        bad_responses = [
            "Sorry, I cannot process this.",
            "{summary: missing quotes}",
            '{"summary": "test", "stated_intent": "INVALID_INTENT", "priority_human_review": true, "review_reason": "ok"}',
            ""
        ]
        for bad in bad_responses:
            self.assertIsNone(parse_and_validate_ai_json(bad))

    @patch("triage_engine.fallback_rule_based_analysis")
    def test_missing_api_key_activates_fallback_mode(self, mock_fallback):
        mock_fallback.return_value = {
            "summary": "Mock summary",
            "stated_intent": "ROUTINE_APPOINTMENT",
            "priority_human_review": False,
            "review_reason": "Mock reason",
            "mode": "CONSERVATIVE_FALLBACK"
        }
        with patch.dict("os.environ", {}, clear=True):
            result = analyze_intake_message("Cough", "Checkup", api_key=None)
            self.assertEqual(result["mode"], "CONSERVATIVE_FALLBACK")
            mock_fallback.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_ai_api_network_error_activates_safe_fallback(self, mock_urlopen):
        # Simulate network or HTTP error from Google Gemini API
        mock_urlopen.side_effect = Exception("Simulated connection timeout / 503 Service Unavailable")
        
        result = analyze_intake_message(
            symptoms="Mild rash on arm",
            message="Need appointment",
            api_key="mock-api-key-test"
        )
        
        # Must gracefully degrade to fallback mode and not crash
        self.assertEqual(result["mode"], "CONSERVATIVE_FALLBACK")
        self.assertIn("fallback", result["review_reason"].lower())
