
"""Run reproducible BB84 detection experiments."""

import csv
from pathlib import Path

from deteccion_qber import evaluate_session


OUTPUT_DIR = Path("resultados")
OUTPUT_FILE = OUTPUT_DIR / "experimentos_bb84.csv"

EVE_FRACTIONS = [0.0, 0.10, 0.25, 0.50, 1.0]
NOISE_LEVELS = [
    (0.01, 0.02),
    (0.03, 0.06),
]
SAMPLE_SIZES = [128, 256, 512]

REPETITIONS = 10
N_SIGNALS = 4096
ALPHA = 0.05


def run_experiments():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    total = (
        len(EVE_FRACTIONS)
        * len(NOISE_LEVELS)
        * len(SAMPLE_SIZES)
        * REPETITIONS
    )
    completed = 0

    for baseline, depolarizing in NOISE_LEVELS:
        for fraction in EVE_FRACTIONS:
            for sample_size in SAMPLE_SIZES:
                for repetition in range(REPETITIONS):
                    seed = (
                        100000
                        + int(baseline * 1000) * 10000
                        + int(fraction * 100) * 100
                        + sample_size * 10
                        + repetition
                    )

                    result = evaluate_session(
                        n_signals=N_SIGNALS,
                        sample_size=sample_size,
                        eve_fraction=fraction,
                        depolarizing_probability=depolarizing,
                        baseline_qber=baseline,
                        alpha=ALPHA,
                        seed=seed,
                    )

                    rows.append({
                        "baseline_qber": baseline,
                        "eve_fraction": fraction,
                        "sample_size": sample_size,
                        "repetition": repetition,
                        "seed": seed,
                        "observed_qber": result["observed_qber"],
                        "errors": result["errors"],
                        "p_value": result["p_value"],
                        "eve_detected": int(result["eve_detected"]),
                    })

                    completed += 1
                    if completed % 25 == 0:
                        print(f"Completed {completed}/{total}")

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} experiments")
    print(f"File: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_experiments()
