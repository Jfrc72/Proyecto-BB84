
"""Generate plots and summaries for BB84 experiments."""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


RESULTS_DIR = Path("resultados")
CSV_PATH = RESULTS_DIR / "experimentos_bb84.csv"
PLOTS_DIR = RESULTS_DIR / "graficas"

PLOTS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV_PATH)

required = {
    "baseline_qber", "eve_fraction", "sample_size",
    "observed_qber", "p_value", "eve_detected",
}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

df["eve_present"] = df["eve_fraction"] > 0

COLORS = {
    0.0: "tab:green",
    0.01: "tab:blue",
    0.03: "tab:orange",
}
SAMPLES = sorted(df["sample_size"].unique())
BASELINES = sorted(df["baseline_qber"].unique())


def save_plot(filename):
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=200)
    plt.close()
    print(f"Saved: {filename}")


def plot_qber():
    """Mean observed QBER versus intercepted fraction."""
    plt.figure(figsize=(9, 5))

    for baseline in BASELINES:
        subset = df[df["baseline_qber"] == baseline]

        summary = subset.groupby("eve_fraction")[
            "observed_qber"
        ].agg(["mean", "std", "count"])

        x = summary.index.to_numpy() * 100
        y = summary["mean"].to_numpy() * 100
        se = (
            summary["std"].to_numpy()
            / np.sqrt(summary["count"].to_numpy())
        ) * 100

        plt.errorbar(
            x, y, yerr=1.96 * se,
            marker="o", capsize=3,
            color=COLORS[baseline],
            label=f"Baseline {baseline:.0%}",
        )

        # Expected QBER for intercept-resend plus
        # independent depolarizing channel noise.
        f = np.linspace(0, 1, 101)
        expected = baseline + (f / 4) * (1 - 2 * baseline)

        plt.plot(
            f * 100, expected * 100,
            linestyle="--",
            color=COLORS[baseline],
            alpha=0.6,
        )

    plt.xlabel("Intercepted signals (%)")
    plt.ylabel("QBER (%)")
    plt.title("QBER versus Eve interception")
    plt.legend()
    plt.grid(alpha=0.3)
    save_plot("01_qber_vs_eve.png")


def plot_detection():
    """Detection rate by Eve fraction and sample size."""
    fig, axes = plt.subplots(
        1, len(BASELINES),
        figsize=(12, 5),
        sharey=True,
        squeeze=False,
    )

    for ax, baseline in zip(axes[0], BASELINES):
        subset = df[
            (df["baseline_qber"] == baseline)
            & (df["eve_present"])
        ]

        for sample_size in SAMPLES:
            group = subset[
                subset["sample_size"] == sample_size
            ]

            rates = group.groupby("eve_fraction")[
                "eve_detected"
            ].mean()

            ax.plot(
                rates.index * 100,
                rates.values * 100,
                marker="o",
                label=f"{sample_size} bits",
            )

        ax.set_title(f"Baseline QBER: {baseline:.0%}")
        ax.set_xlabel("Intercepted signals (%)")
        ax.set_ylim(0, 105)
        ax.grid(alpha=0.3)
        ax.legend()

    axes[0][0].set_ylabel("Detection rate (%)")
    fig.suptitle("Eve detection rate")
    save_plot("02_detection_rate.png")


def plot_false_positives():
    """False-positive rate for sessions without Eve."""
    subset = df[~df["eve_present"]]

    summary = subset.groupby([
        "baseline_qber", "sample_size"
    ])["eve_detected"].mean().unstack(0)

    ax = summary.mul(100).plot(
        kind="bar", figsize=(9, 5)
    )

    ax.set_title("False-positive rate without Eve")
    ax.set_xlabel("Public sample size (bits)")
    ax.set_ylabel("False-positive rate (%)")
    ax.legend(title="Baseline QBER")
    ax.grid(axis="y", alpha=0.3)

    save_plot("03_false_positives.png")


def roc_points(subset):
    """Compute empirical ROC from binomial p-values."""
    labels = subset["eve_present"].to_numpy()
    scores = subset["p_value"].to_numpy()

    thresholds = np.unique(
        np.concatenate(([0.0], scores, [1.0]))
    )

    positive = labels.sum()
    negative = (~labels).sum()

    if positive == 0 or negative == 0:
        raise ValueError("ROC needs both classes")

    fpr = []
    tpr = []

    for threshold in thresholds:
        predicted = scores <= threshold

        fpr.append(
            np.sum(predicted & ~labels) / negative
        )
        tpr.append(
            np.sum(predicted & labels) / positive
        )

    return np.array(fpr), np.array(tpr)


def plot_roc():
    """ROC curves comparing baseline noise and sample size."""
    fig, axes = plt.subplots(
        1, len(BASELINES),
        figsize=(12, 5),
        squeeze=False,
    )

    for ax, baseline in zip(axes[0], BASELINES):
        for sample_size in SAMPLES:
            subset = df[
                (df["baseline_qber"] == baseline)
                & (df["sample_size"] == sample_size)
            ]

            fpr, tpr = roc_points(subset)
            auc = np.trapezoid(tpr, fpr)

            ax.plot(
                fpr, tpr,
                marker=".",
                label=f"{sample_size} bits (AUC={auc:.3f})",
            )

        ax.plot(
            [0, 1], [0, 1],
            linestyle="--", color="gray",
        )

        ax.set_title(f"Baseline QBER: {baseline:.0%}")
        ax.set_xlabel("False-positive rate")
        ax.set_ylabel("True-positive rate")
        ax.legend()
        ax.grid(alpha=0.3)

    fig.suptitle("ROC curves for QBER detection")
    save_plot("04_roc_curves.png")


def save_summary():
    summary = df.groupby([
        "baseline_qber", "eve_fraction", "sample_size"
    ]).agg(
        repetitions=("eve_detected", "size"),
        mean_qber=("observed_qber", "mean"),
        std_qber=("observed_qber", "std"),
        detection_rate=("eve_detected", "mean"),
    ).reset_index()

    output = RESULTS_DIR / "resumen_experimentos.csv"
    summary.to_csv(output, index=False)
    print(f"Saved: {output}")


if __name__ == "__main__":
    plot_qber()
    plot_detection()
    plot_false_positives()
    plot_roc()
    save_summary()
    print("\nAll plots generated successfully.")
