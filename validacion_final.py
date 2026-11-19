
"""Final statistical validation of BB84 Eve detection."""

import csv
import random
from pathlib import Path

from eve_ruido import run_eve_session
from deteccion_qber import detect_eve


OUTPUT_DIR = Path("resultados")
OUTPUT_FILE = OUTPUT_DIR / "validacion_final.csv"

EVE_FRACTIONS = [0.0, 0.10]
NOISE_LEVELS = [
    (0.01, 0.02),
    (0.03, 0.06),
]
SAMPLE_SIZES = [128, 256, 512]

REPETITIONS = 100
N_SIGNALS = 4096
ALPHA = 0.05


def generate_nested_samples(alice_key, bob_key, seed):
    """Generate nested public samples without replacement."""
    if len(alice_key) != len(bob_key):
        raise ValueError("Alice and Bob keys must have equal length")

    maximum_size = max(SAMPLE_SIZES)

    if len(alice_key) < maximum_size:
        raise ValueError("Not enough sifted bits for sampling")

    rng = random.Random(seed)

    positions = rng.sample(
        range(len(alice_key)),
        maximum_size,
    )

    results = {}

    for sample_size in SAMPLE_SIZES:
        selected = positions[:sample_size]

        errors = sum(
            alice_key[index] != bob_key[index]
            for index in selected
        )

        results[sample_size] = errors

    return results


def run_validation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    total_sessions = (
        len(EVE_FRACTIONS)
        * len(NOISE_LEVELS)
        * REPETITIONS
    )

    completed = 0

    for baseline, depolarizing in NOISE_LEVELS:
        for fraction in EVE_FRACTIONS:
            for repetition in range(REPETITIONS):

                seed = (
                    500000
                    + int(baseline * 1000) * 10000
                    + int(fraction * 100) * 1000
                    + repetition
                )

                session = run_eve_session(
                    n_signals=N_SIGNALS,
                    eve_fraction=fraction,
                    depolarizing_probability=depolarizing,
                    readout_probability=0.0,
                    seed=seed,
                )

                sample_errors = generate_nested_samples(
                    session["clave_alice"],
                    session["clave_bob"],
                    seed=seed + 1000000,
                )

                for sample_size, errors in sample_errors.items():
                    detection = detect_eve(
                        errors=errors,
                        sample_size=sample_size,
                        baseline_qber=baseline,
                        alpha=ALPHA,
                    )

                    rows.append({
                        "baseline_qber": baseline,
                        "eve_fraction": fraction,
                        "sample_size": sample_size,
                        "repetition": repetition,
                        "seed": seed,
                        "sifted_bits": session["n_cribados"],
                        "errors": errors,
                        "observed_qber": detection["observed_qber"],
                        "p_value": detection["p_value"],
                        "eve_detected": int(detection["eve_detected"]),
                    })

                completed += 1

                if completed % 25 == 0:
                    print(
                        f"Completed {completed}/{total_sessions} sessions",
                        flush=True,
                    )

    fieldnames = [
        "baseline_qber",
        "eve_fraction",
        "sample_size",
        "repetition",
        "seed",
        "sifted_bits",
        "errors",
        "observed_qber",
        "p_value",
        "eve_detected",
    ]

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCompleted {completed} quantum sessions")
    print(f"Saved {len(rows)} statistical evaluations")
    print(f"File: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_validation()
