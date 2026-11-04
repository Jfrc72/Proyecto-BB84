# Proyecto BB84

**Detección de interceptación parcial en BB84 bajo ruido y muestras finitas.**

Proyecto de Computación Cuántica y Criptografía, Universidad de los Andes.

Integrantes:

- Juan Francisco Rodriguez
- Daniel Alfonso Rudas Bohorquez
- Tomas Camilo Ostos

Queremos estudiar cuántos bits de muestra necesitan Alice y Bob para detectar a
Eve cuando ella intercepta una parte de las señales y el canal también produce
errores normales.

## Qué está listo

Esta es la base de Juan: BB84 ideal con Qiskit Aer, preparación y medición en
bases Z y X, cribado, cálculo de QBER y selección de una muestra pública.
Incluye una demostración y pruebas del caso ideal.

Quedan para las otras partes del equipo: interceptación parcial de Eve, modelos
de ruido calibrados, detector estadístico, experimentos completos y gráficas.
La guía [docs/INTEGRACION.md](docs/INTEGRACION.md) explica qué puede reutilizar
cada integrante y cómo están organizados los datos.

## Instalación

Usamos **Python 3.12**. La ejecución es local con Qiskit Aer.

### macOS o Linux

```bash
git clone https://github.com/Jfrc72/Proyecto-BB84.git
cd Proyecto-BB84
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows, con PowerShell

```powershell
git clone https://github.com/Jfrc72/Proyecto-BB84.git
cd Proyecto-BB84
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En Windows se pueden ejecutar los comandos siguientes reemplazando `python`
por `.\.venv\Scripts\python.exe`.

En macOS o Linux hay que volver a activar el entorno con
`source .venv/bin/activate` cuando se abre una terminal nueva.

## Ejecutar la demostración

```bash
python demo.py
python demo.py --senales 4096 --muestra 1024 --semilla 42
python demo.py --circuitos
python demo.py --guardar resultados/sesion_ideal.json
```

- `--senales`: cantidad de señales enviadas, antes de comparar las bases.
- `--muestra`: cantidad de bits **ya cribados** que se comparan públicamente.
- `--semilla`: permite repetir la sesión con las mismas versiones y opciones.
- `--circuitos`: imprime los cuatro circuitos con bases iguales.
- `--guardar`: guarda los datos, las semillas y las versiones en un JSON.

Con las dependencias de `requirements.txt`, los valores por defecto dieron:

```text
Senales enviadas: 4096
Bits cribados: 2075 (50.7%)
Errores en la clave cribada: 0
QBER de la clave cribada: 0.00%
Muestra publica: 256 bits
Errores en la muestra: 0
Bits restantes tras retirar la muestra: 1819
```

El número de bits cribados fluctúa al cambiar la semilla. Aproximadamente la
mitad de las bases coinciden. En el caso ideal, los bits que quedan sí coinciden
siempre y su QBER es cero.

Si se pide una muestra mayor que la clave cribada disponible, el programa avisa.
En ese caso hay que aumentar `--senales`; no se reduce la muestra en silencio.

## Qué hace el código

1. Alice genera bits aleatorios y elige una base aleatoria por señal.
2. Se prepara un qubit según esta tabla:

| Base | Bit 0 | Bit 1 |
|---|---|---|
| Z | `|0>`: no aplicar compuertas | `|1>`: aplicar X |
| X | `|+>`: aplicar H | `|->`: aplicar X y después H |

3. Bob elige sus bases de forma independiente. Para medir en Z mide
   directamente; para medir en X aplica H antes de medir en Z.
4. Alice y Bob anuncian sus bases. Se conservan únicamente las posiciones donde
   coinciden, respetando el orden. Eso es el cribado.
5. La QBER es `errores / bits comparados`. Las funciones devuelven una fracción
   entre 0 y 1; la demostración la muestra como porcentaje.
6. Se escogen `m` posiciones aleatorias, sin reemplazo, de la clave cribada.
   Los bits revelados para esta comparación se retiran de las claves restantes.

En la simulación podemos calcular la QBER de toda la clave para verificar el
código. El detector del proyecto debe usar la muestra pública y la calibración;
no puede usar como ayuda los bits restantes ni saber de antemano si había Eve.

## Organización

```text
Proyecto-BB84/
├── bb84.py                    # Funciones del protocolo ideal
├── demo.py                    # Ejecución y exportación de una sesión
├── requirements.txt           # Dependencias usadas
├── config_experimentos.json   # Escenarios acordados en la propuesta
├── docs/
│   └── INTEGRACION.md          # Acuerdo de datos y próximos pasos
└── tests/
    └── test_bb84.py            # Pruebas del protocolo y de la demostración
```

`resultados/` y `.venv/` quedan fuera de Git. El JSON de demostración contiene
bits y claves completos para inspeccionar el experimento.

## Comprobar la base

```bash
python -m unittest discover -s tests -v
python -m pip check
```

Las pruebas comprueban los cuatro estados, la recuperación del bit al coincidir
las bases, el comportamiento aleatorio con bases distintas, el cribado, los
errores de QBER, las semillas, el muestreo y la exportación de la demostración.
También se pasa un simulador con lectura invertida para comprobar que la
función realmente utiliza las mediciones del backend externo.

## Experimentos acordados

`config_experimentos.json` registra lo que se ejecutará cuando estén las otras
partes: fracciones de interceptación `0, 0.10, 0.25, 0.50, 1.00`; ruido ideal
y configuraciones con QBER basal cercana al 1 % y al 3 %; muestras de 64, 256
y 1024 bits; al menos 300 sesiones independientes por combinación.

Esos niveles de QBER son objetivos de calibración, no probabilidades de ruido
que se puedan pasar directamente a una compuerta. Daniel medirá la QBER basal
real de cada modelo. Tomás elegirá el umbral usando solo sesiones sin Eve y lo
evaluará en sesiones nuevas. Buscamos al menos 90 % de detección y máximo 5 %
de falsas alarmas; si una combinación no cumple, se reportará así.

## Supuestos y límites

Esta base modela señales independientes, un qubit por señal, y un canal clásico
autenticado para anunciar las bases. Para acelerar la simulación se agrupan las
señales con la misma preparación y bases: cada una recibe su propia medición
de un shot de Aer, que se devuelve a su posición original. No se construye un
estado entrelazado de miles de qubits.

Los circuitos conservan las compuertas de preparación y lectura, sin eliminar
pares de H. Esto permite añadir ruido a esas operaciones después. La agrupación
supone que el canal no tiene memoria ni correlaciones entre señales.

Las semillas son para reproducir experimentos; no son un generador de claves
para uso real. No implementamos reconciliación de errores ni amplificación de
privacidad. Tener QBER cero en una simulación ideal no demuestra la seguridad
general de BB84. Cambiar versiones, backend u opciones puede cambiar la secuencia
aleatoria incluso usando la misma semilla.

## Referencias

- [Bennett y Brassard, BB84 (1984), reimpresión](https://arxiv.org/abs/2003.06557).
- [Qiskit: QuantumCircuit](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.QuantumCircuit).
- [Qiskit Aer: simuladores y mediciones por shot](https://qiskit.github.io/qiskit-aer/tutorials/1_aersimulator.html).
- [Qiskit Aer: modelos de ruido](https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html).
