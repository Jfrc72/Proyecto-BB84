
"""Estimate baseline QBER for the channel noise levels."""

import numpy as np
from eve_ruido import run_eve_session


def main():
    configurations = [
        ("Ideal", 0.0, 0.0),
        ("Baseline 1%", 0.02, 0.0),
        ("Baseline 3%", 0.06, 0.0),
    ]

    for name, depolarizing, readout in configurations:
        total_errors = 0
        total_sifted = 0
        measured_qbers = []

        for seed in range(100, 120):
            session = run_eve_session(
                n_signals=4096,
                eve_fraction=0.0,
                depolarizing_probability=depolarizing,
                readout_probability=readout,
                seed=seed,
            )

            total_errors += session["errores_cribados"]
            total_sifted += session["n_cribados"]
            measured_qbers.append(session["qber_cribada"])

        pooled_qber = total_errors / total_sifted

        print(f"\n{name}")
        print(f"Depolarizing p: {depolarizing}")
        print(f"Readout p: {readout}")
        print(f"Measured baseline QBER: {pooled_qber:.3%}")
        print(
            f"Session QBER std: "
            f"{np.std(measured_qbers, ddof=1):.3%}"
        )


if __name__ == "__main__":
    main()
