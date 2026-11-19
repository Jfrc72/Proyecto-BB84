
"""Tests for Eve interception and channel noise."""

import unittest

from bb84 import generar_datos
from eve_ruido import (
    select_eve_attack,
    build_attack_circuit,
    create_noise_model,
    run_eve_session,
)


class TestEveNoise(unittest.TestCase):

    def test_attack_fraction_zero(self):
        attack = select_eve_attack(100, 0.0, 42)
        self.assertEqual(len(attack), 0)

    def test_attack_fraction_one(self):
        attack = select_eve_attack(100, 1.0, 42)
        self.assertEqual(len(attack), 100)

    def test_attack_is_reproducible(self):
        a = select_eve_attack(100, 0.25, 42)
        b = select_eve_attack(100, 0.25, 42)
        self.assertEqual(a, b)

    def test_invalid_fraction(self):
        with self.assertRaises(ValueError):
            select_eve_attack(100, 1.5, 42)

    def test_circuit_contains_eve_measurement(self):
        circuit = build_attack_circuit(
            0, "Z", "Z", eve_basis="X"
        )
        operations = circuit.count_ops()
        self.assertEqual(operations.get("measure"), 2)
        self.assertEqual(operations.get("reset"), 1)

    def test_noise_model_is_created(self):
        model = create_noise_model(0.02, 0.01)
        self.assertIsNotNone(model)

    def test_ideal_qber_is_zero(self):
        session = run_eve_session(
            n_signals=4096,
            eve_fraction=0.0,
            seed=42,
        )
        self.assertEqual(session["qber_cribada"], 0.0)

    def test_full_eve_qber_near_25_percent(self):
        session = run_eve_session(
            n_signals=8192,
            eve_fraction=1.0,
            seed=42,
        )
        self.assertAlmostEqual(
            session["qber_cribada"], 0.25, delta=0.04
        )

    def test_noise_without_eve(self):
        session = run_eve_session(
            n_signals=8192,
            eve_fraction=0.0,
            depolarizing_probability=0.04,
            seed=42,
        )
        self.assertGreater(session["qber_cribada"], 0.0)

    def test_session_has_expected_fields(self):
        session = run_eve_session(
            n_signals=512, eve_fraction=0.25, seed=42
        )

        for field in (
            "clave_alice",
            "clave_bob",
            "qber_cribada",
            "semillas",
            "attacked_positions",
        ):
            self.assertIn(field, session)


if __name__ == "__main__":
    unittest.main()
