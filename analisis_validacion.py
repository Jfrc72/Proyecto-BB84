
"""Summarize final BB84 validation results."""

from pathlib import Path

import pandas as pd


INPUT_FILE = Path("resultados/validacion_final.csv")
OUTPUT_FILE = Path("resultados/resumen_validacion.csv")


def main():
    df = pd.read_csv(INPUT_FILE)

    summary = (
        df.groupby([
            "baseline_qber",
            "eve_fraction",
            "sample_size",
        ])
        .agg(
            repetitions=("eve_detected", "size"),
            detections=("eve_detected", "sum"),
            detection_rate=("eve_detected", "mean"),
            mean_qber=("observed_qber", "mean"),
            std_qber=("observed_qber", "std"),
        )
        .reset_index()
    )

    summary["detection_rate_percent"] = (
        summary["detection_rate"] * 100
    )

    summary["mean_qber_percent"] = (
        summary["mean_qber"] * 100
    )

    summary.to_csv(OUTPUT_FILE, index=False)

    print("\nFINAL VALIDATION RESULTS")
    print("=" * 75)

    for baseline in sorted(df["baseline_qber"].unique()):
        print(f"\nBaseline QBER: {baseline:.0%}")

        subset = summary[
            summary["baseline_qber"] == baseline
        ]

        for _, row in subset.iterrows():
            scenario = (
                "False positives"
                if row["eve_fraction"] == 0
                else "Eve detection"
            )

            print(
                f"{scenario:16} | "
                f"Eve: {row['eve_fraction']:.0%} | "
                f"Sample: {int(row['sample_size']):3} | "
                f"Rate: {row['detection_rate_percent']:5.1f}% | "
                f"Mean QBER: {row['mean_qber_percent']:5.2f}%"
            )

    print(f"\nSaved summary: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
