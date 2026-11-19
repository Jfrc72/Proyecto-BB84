
"""Demonstration of QBER-based Eve detection."""

from deteccion_qber import evaluate_session


def main():
    scenarios = [
        ("No Eve, noise 1%", 0.0, 0.02, 0.01),
        ("Eve 10%, noise 1%", 0.10, 0.02, 0.01),
        ("Eve 25%, noise 1%", 0.25, 0.02, 0.01),
        ("Eve 50%, noise 1%", 0.50, 0.02, 0.01),
        ("No Eve, noise 3%", 0.0, 0.06, 0.03),
        ("Eve 25%, noise 3%", 0.25, 0.06, 0.03),
    ]

    for name, fraction, depolarizing, baseline in scenarios:
        result = evaluate_session(
            n_signals=4096,
            sample_size=256,
            eve_fraction=fraction,
            depolarizing_probability=depolarizing,
            baseline_qber=baseline,
            alpha=0.05,
            seed=42,
        )

        print(f"\nScenario: {name}")
        print(f"Observed QBER: {result['observed_qber']:.2%}")
        print(f"Baseline QBER: {result['baseline_qber']:.2%}")
        print(f"Errors: {result['errors']}/{result['sample_size']}")
        print(f"P-value: {result['p_value']:.6f}")
        print(f"Eve detected: {result['eve_detected']}")
        print(f"Remaining key bits: {result['remaining_key_length']}")


if __name__ == "__main__":
    main()
