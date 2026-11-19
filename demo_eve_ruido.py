
"""Demonstration of Eve interception and BB84 channel noise."""

from bb84 import tomar_muestra
from eve_ruido import run_eve_session


def main():
    scenarios = [
        ("Ideal", 0.0, 0.0, 0.0),
        ("Eve 10%", 0.10, 0.0, 0.0),
        ("Eve 25%", 0.25, 0.0, 0.0),
        ("Eve 50%", 0.50, 0.0, 0.0),
        ("Eve 100%", 1.0, 0.0, 0.0),
        ("Noise only", 0.0, 0.02, 0.0),
        ("Eve + noise", 0.25, 0.02, 0.0),
    ]

    for name, fraction, depolarizing, readout in scenarios:
        session = run_eve_session(
            n_signals=4096,
            eve_fraction=fraction,
            depolarizing_probability=depolarizing,
            readout_probability=readout,
            seed=42,
        )

        sample = tomar_muestra(
            session["clave_alice"],
            session["clave_bob"],
            m=256,
            semilla=session["semillas"]["muestra"],
        )

        print(f"\nScenario: {name}")
        print(f"Intercepted: {session['n_attacked']}")
        print(f"Sifted bits: {session['n_cribados']}")
        print(f"Total QBER: {session['qber_cribada']:.2%}")
        print(f"Sample QBER: {sample['qber']:.2%}")
        print(f"Sample errors: {sample['errores']}/256")


if __name__ == "__main__":
    main()
