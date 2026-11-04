"""Demostracion del caso ideal: python demo.py --muestra 256 --semilla 42."""

import argparse
import json
import platform
from importlib.metadata import version
from pathlib import Path

from bb84 import construir_circuito, ejecutar_sesion, tomar_muestra


def main():
    parser = argparse.ArgumentParser(description="Simulacion ideal de BB84, sin Eve y sin ruido")
    parser.add_argument("--senales", type=int, default=4096, help="Cantidad de senales antes del cribado")
    parser.add_argument("--muestra", type=int, default=256, help="Bits cribados que se comparan publicamente")
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--guardar", type=Path, help="Ruta para guardar la sesion y la muestra en JSON")
    parser.add_argument("--circuitos", action="store_true", help="Muestra los cuatro casos con bases iguales")
    args = parser.parse_args()

    try:
        sesion = ejecutar_sesion(args.senales, args.semilla)
        muestra = tomar_muestra(
            sesion["clave_alice"], sesion["clave_bob"], args.muestra, sesion["semillas"]["muestra"]
        )
    except ValueError as error:
        parser.error(str(error))

    print("BB84: caso ideal (sin Eve y sin ruido)")
    print(f"Semilla: {args.semilla}")
    print(f"Senales enviadas: {sesion['n_senales']}")
    print(f"Bits cribados: {sesion['n_cribados']} ({sesion['n_cribados'] / args.senales:.1%})")
    print(f"Errores en la clave cribada: {sesion['errores_cribados']}")
    print(f"QBER de la clave cribada: {sesion['qber_cribada']:.2%}")
    print(f"Muestra publica: {muestra['m']} bits")
    print(f"Errores en la muestra: {muestra['errores']}")
    print(f"QBER de la muestra: {muestra['qber']:.2%}")
    print(f"Bits restantes tras retirar la muestra: {len(muestra['clave_restante_alice'])}")
    print("Primeros 24 bits cribados:")
    print("Alice:", "".join(map(str, sesion["clave_alice"][:24])))
    print("Bob:  ", "".join(map(str, sesion["clave_bob"][:24])))

    if args.circuitos:
        for base in ("Z", "X"):
            for bit in (0, 1):
                print(f"\nAlice envia {bit} en {base}; Bob mide en {base}:")
                print(construir_circuito(bit, base, base).draw(output="text"))

    if args.guardar:
        datos = {
            "versiones": {
                "python": platform.python_version(),
                **{p: version(p) for p in ("qiskit", "qiskit-aer", "numpy")},
            },
            "sesion": sesion,
            "muestra": muestra,
        }
        args.guardar.parent.mkdir(parents=True, exist_ok=True)
        args.guardar.write_text(json.dumps(datos, indent=2), encoding="utf-8")
        print(f"\nSesion guardada en {args.guardar}")


if __name__ == "__main__":
    main()
