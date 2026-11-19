
"""Unit tests for QBER-based statistical detection."""

import unittest

from deteccion_qber import detect_eve, evaluate_session


class TestQBERDetection(unittest.TestCase):

    def test_no_errors(self):
        result = detect_eve(0, 256, 0.01)
        self.assertEqual(result["observed_qber"], 0.0)
        self.assertFalse(result["eve_detected"])

    def test_strong_attack(self):
        result = detect_eve(64, 256, 0.01)
        self.assertTrue(result["eve_detected"])
        self.assertLessEqual(result["p_value"], 0.05)

    def test_no_false_alarm_in_example(self):
        result = detect_eve(3, 256, 0.01)
        self.assertFalse(result["eve_detected"])

    def test_higher_baseline_changes_decision(self):
        low = detect_eve(8, 256, 0.01)
        high = detect_eve(8, 256, 0.03)

        self.assertTrue(low["eve_detected"])
        self.assertFalse(high["eve_detected"])

    def test_invalid_errors(self):
        with self.assertRaises(ValueError):
            detect_eve(300, 256, 0.01)

    def test_invalid_sample_size(self):
        with self.assertRaises(ValueError):
            detect_eve(0, 0, 0.01)

    def test_invalid_baseline(self):
        with self.assertRaises(ValueError):
            detect_eve(2, 256, 1.5)

    def test_invalid_alpha(self):
        with self.assertRaises(ValueError):
            detect_eve(2, 256, 0.01, alpha=0)

    def test_session_integration(self):
        result = evaluate_session(
            n_signals=1024,
            sample_size=128,
            eve_fraction=0.25,
            depolarizing_probability=0.02,
            baseline_qber=0.01,
            seed=42,
        )

        self.assertEqual(result["sample_size"], 128)
        self.assertGreaterEqual(result["p_value"], 0)
        self.assertLessEqual(result["p_value"], 1)

    def test_ideal_session(self):
        result = evaluate_session(
            n_signals=1024,
            sample_size=128,
            eve_fraction=0,
            depolarizing_probability=0,
            baseline_qber=0,
            seed=42,
        )

        self.assertEqual(result["observed_qber"], 0)
        self.assertFalse(result["eve_detected"])


if __name__ == "__main__":
    unittest.main()
