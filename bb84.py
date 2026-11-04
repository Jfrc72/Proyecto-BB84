"""Preparacion, medicion y cribado de una sesion de BB84."""

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def _validar_entero(valor, nombre, minimo=0):
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < minimo:
        raise ValueError(f"{nombre} debe ser un entero mayor o igual a {minimo}")


def _validar_claves(clave_alice, clave_bob):
    if len(clave_alice) != len(clave_bob):
        raise ValueError("Las dos claves deben tener la misma longitud")
    if any(bit not in (0, 1) for bit in [*clave_alice, *clave_bob]):
        raise ValueError("Las claves solo pueden contener bits 0 o 1")


def _validar_datos(datos):
    campos = ("bits_alice", "bases_alice", "bases_bob")
    if any(campo not in datos for campo in campos):
        raise ValueError("Faltan bits_alice, bases_alice o bases_bob")
    n = len(datos["bits_alice"])
    if any(len(datos[campo]) != n for campo in campos):
        raise ValueError("Los bits y las bases deben tener la misma longitud")
    if any(bit not in (0, 1) for bit in datos["bits_alice"]):
        raise ValueError("Los bits de Alice deben ser 0 o 1")
    if any(base not in ("Z", "X") for campo in campos[1:] for base in datos[campo]):
        raise ValueError("Las bases deben ser Z o X")


def generar_datos(n_senales, semilla):
    """Genera los bits de Alice y las elecciones de base de Alice y Bob."""
    _validar_entero(n_senales, "n_senales", minimo=1)
    _validar_entero(semilla, "semilla")
    rng = np.random.default_rng(semilla)
    return {
        "bits_alice": rng.integers(0, 2, size=n_senales).tolist(),
        "bases_alice": rng.choice(["Z", "X"], size=n_senales).tolist(),
        "bases_bob": rng.choice(["Z", "X"], size=n_senales).tolist(),
    }


def preparar_estado(bit, base):
    """Prepara |0>, |1>, |+> o |-> en el qubit 0."""
    if bit not in (0, 1) or base not in ("Z", "X"):
        raise ValueError("Se necesita un bit 0 o 1 y una base Z o X")
    circuito = QuantumCircuit(1, 1)
    if bit == 1:
        circuito.x(0)
    if base == "X":
        circuito.h(0)
    return circuito


def medir_en_base(circuito, base):
    """Devuelve una copia con la medicion de Bob en el bit clasico 0."""
    if base not in ("Z", "X"):
        raise ValueError("La base de medicion debe ser Z o X")
    if circuito.num_qubits != 1 or circuito.num_clbits < 1:
        raise ValueError("Se necesita un qubit y al menos un bit clasico")
    copia = circuito.copy()
    copia.barrier(0)
    if base == "X":
        copia.h(0)
    copia.measure(0, 0)
    return copia


def construir_circuito(bit, base_alice, base_bob):
    return medir_en_base(preparar_estado(bit, base_alice), base_bob)


def simular_mediciones(datos, semilla, simulador=None):
    """Simula cada senal y devuelve los bits de Bob en el orden original."""
    _validar_datos(datos)
    _validar_entero(semilla, "semilla")
    n = len(datos["bits_alice"])
    if n == 0:
        return []
    if simulador is None:
        simulador = AerSimulator(max_parallel_threads=1)

    grupos = {}
    for i in range(n):
        caso = (datos["bits_alice"][i], datos["bases_alice"][i], datos["bases_bob"][i])
        grupos.setdefault(caso, []).append(i)

    casos = sorted(grupos)
    circuitos = [construir_circuito(*caso) for caso in casos]
    shots = max(len(indices) for indices in grupos.values())
    resultado = simulador.run(
        circuitos, shots=shots, memory=True, seed_simulator=semilla
    ).result()
    if not resultado.success:
        raise RuntimeError("Aer no pudo completar la simulacion")

    # Senales con la misma preparacion y bases comparten circuito, no medicion.
    bits_bob = [0] * n
    for j, caso in enumerate(casos):
        mediciones = resultado.get_memory(j)
        for i, medicion in zip(grupos[caso], mediciones):
            bits_bob[i] = int(medicion, 2)
    return bits_bob


def cribar(datos, bits_bob):
    """Conserva, en orden, las posiciones donde coinciden las bases."""
    _validar_datos(datos)
    _validar_claves(datos["bits_alice"], bits_bob)
    posiciones = [
        i for i, (a, b) in enumerate(zip(datos["bases_alice"], datos["bases_bob"]))
        if a == b
    ]
    return {
        "posiciones_cribadas": posiciones,
        "clave_alice": [datos["bits_alice"][i] for i in posiciones],
        "clave_bob": [bits_bob[i] for i in posiciones],
    }


def calcular_qber(clave_alice, clave_bob):
    """QBER como fraccion entre 0 y 1; no como porcentaje."""
    _validar_claves(clave_alice, clave_bob)
    if len(clave_alice) == 0:
        raise ValueError("No se puede calcular QBER sin bits para comparar")
    errores = sum(a != b for a, b in zip(clave_alice, clave_bob))
    return errores / len(clave_alice)


def tomar_muestra(clave_alice, clave_bob, m, semilla):
    """Extrae m posiciones sin reemplazo y las retira de las claves restantes."""
    _validar_claves(clave_alice, clave_bob)
    _validar_entero(m, "m", minimo=1)
    _validar_entero(semilla, "semilla")
    if m > len(clave_alice):
        raise ValueError(
            f"Se pidieron {m} bits de muestra, pero solo hay {len(clave_alice)} cribados. "
            "Aumenta el numero de senales."
        )
    rng = np.random.default_rng(semilla)
    indices = sorted(rng.choice(len(clave_alice), size=m, replace=False).tolist())
    elegidos = set(indices)
    muestra_alice = [clave_alice[i] for i in indices]
    muestra_bob = [clave_bob[i] for i in indices]
    return {
        "m": m,
        "indices": indices,
        "bits_alice": muestra_alice,
        "bits_bob": muestra_bob,
        "errores": sum(a != b for a, b in zip(muestra_alice, muestra_bob)),
        "qber": calcular_qber(muestra_alice, muestra_bob),
        "clave_restante_alice": [bit for i, bit in enumerate(clave_alice) if i not in elegidos],
        "clave_restante_bob": [bit for i, bit in enumerate(clave_bob) if i not in elegidos],
    }


def ejecutar_sesion(n_senales=4096, semilla=42, simulador=None):
    """Ejecuta BB84 sin Eve. Acepta un backend Aer para integrar ruido despues."""
    _validar_entero(semilla, "semilla")
    rng = np.random.default_rng(semilla)
    s_datos, s_medicion, s_muestra = rng.integers(0, 2**31 - 1, size=3).tolist()
    datos = generar_datos(n_senales, s_datos)
    bits_bob = simular_mediciones(datos, s_medicion, simulador)
    cribado = cribar(datos, bits_bob)
    n_cribados = len(cribado["clave_alice"])
    errores = sum(a != b for a, b in zip(cribado["clave_alice"], cribado["clave_bob"]))
    return {
        "n_senales": n_senales,
        "semilla": semilla,
        "semillas": {"datos": s_datos, "medicion": s_medicion, "muestra": s_muestra},
        **datos,
        "bits_bob": bits_bob,
        **cribado,
        "n_cribados": n_cribados,
        "errores_cribados": errores,
        "qber_cribada": errores / n_cribados if n_cribados else None,
    }
