
"""Run the experimental design defined in config_experimentos.json."""

import csv
import json
import random
from pathlib import Path

from bb84 import tomar_muestra
from deteccion_qber import detect_eve
from eve_ruido import run_eve_session


CONFIG_FILE = Path("config_experimentos.json")
OUTPUT_DIR = Path("resultados")
OUTPUT_FILE = OUTPUT_DIR / "experimentos_bb84.csv"

N_SIGNALS = 4096
ALPHA = 0.05

# Depolarizing probabilities calibrated for each baseline QBER.
DEPOLARIZING_PROBABILITIES = {
    0.0: 0.0,
    0.01: 0.02,
    0.03: 0.06,
}


def run_experiments():
    with CONFIG_FILE.open(encoding="utf-8") as file:
        config = json.load(file)

    eve_fractions = config["fracciones_interceptacion"]
    baselines = config["qber_basal_objetivo"]
    sample_sizes = sorted(config["muestras"])
    repetitions = config["sesiones_por_combinacion"]
    master_seed = config["semilla_maestra"]

    if repetitions < 300:
        raise ValueError("At least 300 sessions are required")

    if N_SIGNALS <= 0:
        raise ValueError("Invalid number of signals")

    if max(sample_sizes) > N_SIGNALS:
        raise ValueError("Sample size exceeds signals")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_sessions = (
        len(eve_fractions)
        * len(baselines)
        * repetitions
    )

    total_evaluations = total_sessions * len(sample_sizes)

    print(f"Total quantum sessions: {total_sessions}")
    print(f"Total statistical evaluations: {total_evaluations}")

    fieldnames = [
        "baseline_qber",
        "eve_fraction",
        "sample_size",
        "repetition",
        "seed",
        "observed_qber",
        "errors",
        "p_value",
        "eve_detected",
        "session_id",
        "sifted_bits",
    ]

    completed = 0
    evaluations = 0

    # Independent seeds for each quantum session.
    master_rng = random.Random(master_seed)

    with OUTPUT_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for baseline in baselines:
            depolarizing = DEPOLARIZING_PROBABILITIES[baseline]

            for fraction in eve_fractions:
                for repetition in range(repetitions):
                    seed = master_rng.randrange(1, 2**31)

                    session = run_eve_session(
                        n_signals=N_SIGNALS,
                        eve_fraction=fraction,
                        depolarizing_probability=depolarizing,
                        readout_probability=0.0,
                        seed=seed,
                    )

                    alice_key = session["clave_alice"]
                    bob_key = session["clave_bob"]

                    if len(alice_key) < max(sample_sizes):
                        raise RuntimeError(
                            "Insufficient sifted bits "
                            f"for seed {seed}"
                        )

                    session_id = (
                        f"b{int(baseline * 100)}"
                        f"_e{int(fraction * 100)}"
                        f"_r{repetition}"
                    )

                    # One random ordering per session.
                    # Samples are nested but sessions are independent.
                    sample_rng = random.Random(seed + 1)

                    positions = sample_rng.sample(
                        range(len(alice_key)),
                        max(sample_sizes),
                    )

                    for sample_size in sample_sizes:
                        selected = positions[:sample_size]

                        errors = sum(
                            alice_key[index] != bob_key[index]
                            for index in selected
                        )

                        detection = detect_eve(
                            errors=errors,
                            sample_size=sample_size,
                            baseline_qber=baseline,
                            alpha=ALPHA,
                        )

                        writer.writerow({
                            "baseline_qber": baseline,
                            "eve_fraction": fraction,
                            "sample_size": sample_size,
                            "repetition": repetition,
                            "seed": seed,
                            "observed_qber": detection["observed_qber"],
                            "errors": errors,
                            "p_value": detection["p_value"],
                            "eve_detected": int(
                                detection["eve_detected"]
                            ),
                            "session_id": session_id,
                            "sifted_bits": len(alice_key),
                        })

                        evaluations += 1

                    completed += 1

                    if completed % 100 == 0:
                        print(
                            f"Completed {completed}/{total_sessions} "
                            "quantum sessions"
                        )
                        file.flush()

    print("\nExperimental design completed")
    print(f"Quantum sessions: {completed}")
    print(f"Statistical evaluations: {evaluations}")
    print(f"Results: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_experiments()
