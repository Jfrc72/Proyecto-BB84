
"""Statistical detection of excess QBER in BB84."""

from scipy.stats import binom

from bb84 import tomar_muestra
from eve_ruido import run_eve_session


def detect_eve(errors, sample_size, baseline_qber, alpha=0.05):
    """One-sided binomial test for excess errors."""
    if not isinstance(sample_size, int) or sample_size <= 0:
        raise ValueError("sample_size must be a positive integer")

    if not isinstance(errors, int) or not 0 <= errors <= sample_size:
        raise ValueError("Invalid number of errors")

    if not 0 <= baseline_qber <= 1:
        raise ValueError("baseline_qber must be between 0 and 1")

    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    observed_qber = errors / sample_size

    # P(X >= errors), where X ~ Binomial(n, baseline_qber).
    p_value = float(
        binom.sf(errors - 1, sample_size, baseline_qber)
    )

    return {
        "errors": errors,
        "sample_size": sample_size,
        "observed_qber": observed_qber,
        "baseline_qber": baseline_qber,
        "alpha": alpha,
        "p_value": p_value,
        "eve_detected": p_value <= alpha,
    }


def evaluate_session(
    n_signals=4096,
    sample_size=256,
    eve_fraction=0.0,
    depolarizing_probability=0.02,
    readout_probability=0.0,
    baseline_qber=0.01,
    alpha=0.05,
    seed=42,
):
    """Run BB84, reveal a sample and test for excess QBER."""
    session = run_eve_session(
        n_signals=n_signals,
        eve_fraction=eve_fraction,
        depolarizing_probability=depolarizing_probability,
        readout_probability=readout_probability,
        seed=seed,
    )

    sample = tomar_muestra(
        session["clave_alice"],
        session["clave_bob"],
        m=sample_size,
        semilla=session["semillas"]["muestra"],
    )

    detection = detect_eve(
        errors=sample["errores"],
        sample_size=sample["m"],
        baseline_qber=baseline_qber,
        alpha=alpha,
    )

    return {
        **detection,
        "eve_fraction": eve_fraction,
        "depolarizing_probability": depolarizing_probability,
        "readout_probability": readout_probability,
        "n_signals": n_signals,
        "seed": seed,
        "sifted_bits": session["n_cribados"],
        "remaining_key_length": len(
            sample["clave_restante_alice"]
        ),
    }
