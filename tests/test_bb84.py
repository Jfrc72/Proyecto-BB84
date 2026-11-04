import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError

from bb84 import (
    calcular_qber,
    cribar,
    ejecutar_sesion,
    generar_datos,
    medir_en_base,
    preparar_estado,
    simular_mediciones,
    tomar_muestra,
)


class PruebasBB84(unittest.TestCase):
    def test_los_cuatro_estados(self):
        esperados = {
            (0, "Z"): [1, 0],
            (1, "Z"): [0, 1],
            (0, "X"): np.array([1, 1]) / np.sqrt(2),
            (1, "X"): np.array([1, -1]) / np.sqrt(2),
        }
        for (bit, base), esperado in esperados.items():
            with self.subTest(bit=bit, base=base):
                estado = Statevector.from_instruction(preparar_estado(bit, base))
                np.testing.assert_allclose(estado.data, esperado, atol=1e-12)

    def test_medir_no_modifica_el_circuito_de_alice(self):
        preparacion = preparar_estado(1, "X")
        antes = preparacion.copy()
        medicion = medir_en_base(preparacion, "X")
        self.assertEqual(preparacion, antes)
        self.assertNotEqual(preparacion, medicion)

    def test_bases_iguales_recuperan_el_bit(self):
        datos = {"bits_alice": [], "bases_alice": [], "bases_bob": []}
        for base in ("Z", "X"):
            for bit in (0, 1):
                datos["bits_alice"] += [bit] * 256
                datos["bases_alice"] += [base] * 256
                datos["bases_bob"] += [base] * 256
        self.assertEqual(simular_mediciones(datos, 42), datos["bits_alice"])

    def test_bases_distintas_producen_resultados_aleatorios(self):
        datos = {"bits_alice": [], "bases_alice": [], "bases_bob": []}
        for base_alice, base_bob in (("Z", "X"), ("X", "Z")):
            for bit in (0, 1):
                datos["bits_alice"] += [bit] * 2048
                datos["bases_alice"] += [base_alice] * 2048
                datos["bases_bob"] += [base_bob] * 2048
        bits_bob = simular_mediciones(datos, 314)
        for inicio in range(0, len(bits_bob), 2048):
            proporcion_unos = sum(bits_bob[inicio:inicio + 2048]) / 2048
            self.assertLess(abs(proporcion_unos - 0.5), 0.05)

    def test_cribado_conserva_posiciones_y_errores(self):
        datos = {
            "bits_alice": [0, 1, 1, 0, 1],
            "bases_alice": ["Z", "X", "Z", "X", "Z"],
            "bases_bob": ["Z", "Z", "Z", "X", "X"],
        }
        resultado = cribar(datos, [0, 0, 0, 0, 1])
        self.assertEqual(resultado["posiciones_cribadas"], [0, 2, 3])
        self.assertEqual(resultado["clave_alice"], [0, 1, 0])
        self.assertEqual(resultado["clave_bob"], [0, 0, 0])
        self.assertAlmostEqual(calcular_qber(resultado["clave_alice"], resultado["clave_bob"]), 1 / 3)

    def test_cribado_sin_coincidencias(self):
        datos = {"bits_alice": [0, 1], "bases_alice": ["Z", "X"], "bases_bob": ["X", "Z"]}
        self.assertEqual(cribar(datos, [1, 0])["clave_alice"], [])
        with self.assertRaises(ValueError):
            calcular_qber([], [])

    def test_sesion_ideal_completa(self):
        sesion = ejecutar_sesion(4096, 42)
        self.assertEqual(sesion["qber_cribada"], 0)
        self.assertEqual(sesion["clave_alice"], sesion["clave_bob"])
        self.assertLess(abs(sesion["n_cribados"] / 4096 - 0.5), 0.05)
        muestra = tomar_muestra(sesion["clave_alice"], sesion["clave_bob"], 1024, 5)
        self.assertEqual(muestra["qber"], 0)
        self.assertEqual(muestra["m"], 1024)

    def test_semilla_repite_la_sesion(self):
        self.assertEqual(ejecutar_sesion(256, 17), ejecutar_sesion(256, 17))
        self.assertNotEqual(generar_datos(256, 17), generar_datos(256, 18))

    def test_muestra_sin_reemplazo_y_retirada_de_la_clave(self):
        alice = [i % 2 for i in range(100)]
        bob = [1 - bit if i % 3 == 0 else bit for i, bit in enumerate(alice)]
        muestra = tomar_muestra(alice, bob, 32, 10)
        elegidos = muestra["indices"]
        restantes = [i for i in range(100) if i not in elegidos]
        self.assertEqual(len(set(elegidos)), 32)
        self.assertEqual(muestra["bits_alice"], [alice[i] for i in elegidos])
        self.assertEqual(muestra["bits_bob"], [bob[i] for i in elegidos])
        self.assertEqual(muestra["clave_restante_alice"], [alice[i] for i in restantes])
        self.assertEqual(muestra["clave_restante_bob"], [bob[i] for i in restantes])
        self.assertEqual(muestra["errores"], sum(i % 3 == 0 for i in elegidos))
        self.assertEqual(muestra, tomar_muestra(alice, bob, 32, 10))
        self.assertNotEqual(elegidos, tomar_muestra(alice, bob, 32, 11)["indices"])

    def test_qber_totalmente_opuesta(self):
        self.assertEqual(calcular_qber([0, 1, 0], [1, 0, 1]), 1)

    def test_simulador_externo_se_aplica(self):
        modelo = NoiseModel()
        modelo.add_all_qubit_readout_error(ReadoutError([[0, 1], [1, 0]]))
        simulador = AerSimulator(noise_model=modelo, max_parallel_threads=1)
        sesion = ejecutar_sesion(256, 42, simulador=simulador)
        self.assertEqual(sesion["qber_cribada"], 1)

    def test_rechaza_entradas_invalidas(self):
        for n, semilla in ((0, 1), (-1, 1), (10, -1)):
            with self.subTest(n=n, semilla=semilla), self.assertRaises(ValueError):
                generar_datos(n, semilla)
        for bit, base in ((2, "Z"), (0, "Y")):
            with self.subTest(bit=bit, base=base), self.assertRaises(ValueError):
                preparar_estado(bit, base)
        with self.assertRaises(ValueError):
            calcular_qber([0], [0, 1])
        with self.assertRaises(ValueError):
            tomar_muestra([0, 1], [0, 1], 3, 0)
        with self.assertRaises(ValueError):
            simular_mediciones({"bits_alice": [0], "bases_alice": ["Z"], "bases_bob": []}, 0)

    def test_demo_guarda_un_resultado_utilizable(self):
        raiz = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporal:
            salida = Path(temporal) / "sesion.json"
            proceso = subprocess.run(
                [sys.executable, "demo.py", "--senales", "256", "--muestra", "64", "--guardar", str(salida)],
                cwd=raiz, capture_output=True, text=True,
            )
            self.assertEqual(proceso.returncode, 0, proceso.stderr)
            dato = json.loads(salida.read_text())
            self.assertEqual(dato["muestra"]["m"], 64)
            self.assertEqual(dato["muestra"]["qber"], 0)
            self.assertEqual(dato["sesion"]["n_senales"], 256)
            self.assertIn("qiskit-aer", dato["versiones"])


if __name__ == "__main__":
    unittest.main()
