
"""Partial intercept-resend attack and channel noise for BB84."""

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import (
    NoiseModel,
    ReadoutError,
    depolarizing_error,
)

from bb84 import (
    generar_datos,
    preparar_estado,
    medir_en_base,
    cribar,
)


def validate_probability(value, name):
    if not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")


def select_eve_attack(n_signals, fraction, seed):
    """Select attacked positions and Eve's random bases."""
    validate_probability(fraction, "fraction")

    if not isinstance(n_signals, int) or n_signals < 1:
        raise ValueError("n_signals must be a positive integer")

    rng = np.random.default_rng(seed)
    n_attacked = int(round(n_signals * fraction))

    positions = sorted(
        rng.choice(
            n_signals, size=n_attacked, replace=False
        ).tolist()
    )

    bases = rng.choice(
        ["Z", "X"], size=n_attacked
    ).tolist()

    return dict(zip(positions, bases))


def create_noise_model(
    depolarizing_probability=0.0,
    readout_probability=0.0,
):
    """Build independent transmission and measurement noise."""
    validate_probability(
        depolarizing_probability, "depolarizing_probability"
    )
    validate_probability(
        readout_probability, "readout_probability"
    )

    # For a one-qubit depolarizing channel, Aer accepts p <= 4/3.
    model = NoiseModel()

    if depolarizing_probability > 0:
        model.add_all_qubit_quantum_error(
            depolarizing_error(depolarizing_probability, 1),
            ["id"],
        )

    if readout_probability > 0:
        p = readout_probability
        model.add_all_qubit_readout_error(
            ReadoutError([
                [1 - p, p],
                [p, 1 - p],
            ])
        )

    return model


def build_attack_circuit(
    bit,
    alice_basis,
    bob_basis,
    eve_basis=None,
):
    """Prepare Alice, optionally intercept, then measure Bob."""
    circuit = QuantumCircuit(1, 2)

    if bit == 1:
        circuit.x(0)

    if alice_basis == "X":
        circuit.h(0)

    if eve_basis is not None:
        if eve_basis not in ("Z", "X"):
            raise ValueError("Eve basis must be Z or X")

        # Eve measures in her chosen basis.
        if eve_basis == "X":
            circuit.h(0)

        circuit.measure(0, 1)

        # Destroy the measured state and prepare a fresh qubit.
        circuit.reset(0)

        with circuit.if_test((circuit.clbits[1], 1)):
            circuit.x(0)

        if eve_basis == "X":
            circuit.h(0)

    # Explicit channel location, after Eve and before Bob.
    circuit.barrier(0)
    circuit.id(0)
    circuit.barrier(0)

    if bob_basis == "X":
        circuit.h(0)

    circuit.measure(0, 0)
    return circuit


def simulate_eve_channel(
    data,
    eve_fraction=0.0,
    depolarizing_probability=0.0,
    readout_probability=0.0,
    seed=42,
):
    """Simulate BB84 with optional Eve and channel noise."""
    validate_probability(eve_fraction, "eve_fraction")

    n = len(data["bits_alice"])

    if n == 0:
        raise ValueError("At least one signal is required")

    if any(len(data[key]) != n for key in (
        "bases_alice", "bases_bob"
    )):
        raise ValueError("Signal arrays must have equal lengths")

    attack = select_eve_attack(n, eve_fraction, seed)

    noise_model = create_noise_model(
        depolarizing_probability,
        readout_probability,
    )

    simulator = AerSimulator(
        noise_model=noise_model,
        max_parallel_threads=1,
    )

    # Group signals only when their full circuit is identical.
    groups = {}

    for i in range(n):
        case = (
            data["bits_alice"][i],
            data["bases_alice"][i],
            data["bases_bob"][i],
            attack.get(i),
        )
        groups.setdefault(case, []).append(i)

    cases = sorted(
        groups,
        key=lambda case: (
            case[0], case[1], case[2],
            case[3] or "",
        ),
    )

    circuits = [build_attack_circuit(*case) for case in cases]
    shots = max(len(indices) for indices in groups.values())

    result = simulator.run(
        circuits,
        shots=shots,
        memory=True,
        seed_simulator=seed + 1,
    ).result()

    if not result.success:
        raise RuntimeError("Aer simulation failed")

    bob_bits = [0] * n
    eve_bits = [None] * n

    for j, case in enumerate(cases):
        memories = result.get_memory(j)

        for index, measurement in zip(groups[case], memories):
            # Qiskit prints c1 c0: Bob is c0 (rightmost).
            value = measurement.replace(" ", "")
            bob_bits[index] = int(value[-1])

            if case[3] is not None:
                eve_bits[index] = int(value[-2])

    return {
        "bits_bob": bob_bits,
        "eve_bases": [
            attack.get(i) for i in range(n)
        ],
        "eve_bits": eve_bits,
        "attacked_positions": sorted(attack),
        "n_attacked": len(attack),
        "eve_fraction": eve_fraction,
        "depolarizing_probability": depolarizing_probability,
        "readout_probability": readout_probability,
    }


def run_eve_session(
    n_signals=4096,
    eve_fraction=0.0,
    depolarizing_probability=0.0,
    readout_probability=0.0,
    seed=42,
):
    """Return a session compatible with the original BB84 format."""
    rng = np.random.default_rng(seed)
    data_seed, attack_seed, sample_seed = rng.integers(
        0, 2**31 - 1, size=3
    ).tolist()

    data = generar_datos(n_signals, data_seed)

    channel = simulate_eve_channel(
        data,
        eve_fraction=eve_fraction,
        depolarizing_probability=depolarizing_probability,
        readout_probability=readout_probability,
        seed=attack_seed,
    )

    sifted = cribar(data, channel["bits_bob"])
    n_sifted = len(sifted["clave_alice"])

    errors = sum(
        a != b for a, b in zip(
            sifted["clave_alice"], sifted["clave_bob"]
        )
    )

    return {
        "n_senales": n_signals,
        "semilla": seed,
        "semillas": {
            "datos": data_seed,
            "medicion": attack_seed,
            "muestra": sample_seed,
        },
        **data,
        **channel,
        **sifted,
        "n_cribados": n_sifted,
        "errores_cribados": errors,
        "qber_cribada": (
            errors / n_sifted if n_sifted else None
        ),
    }
