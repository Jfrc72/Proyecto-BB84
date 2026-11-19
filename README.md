
# Proyecto BB84

**Detección de interceptación parcial en BB84 bajo ruido y muestras finitas.**

Proyecto de Computación Cuántica y Criptografía, Universidad de los Andes.

## Integrantes

- Juan Francisco Rodriguez
- Daniel Alfonso Rudas Bohorquez
- Tomas Camilo Ostos

## Objetivo

Estudiar cuántos bits de muestra necesitan Alice y Bob para detectar
a Eve cuando intercepta una fracción de las señales cuánticas y el
canal también introduce errores normales.

El proyecto implementa el protocolo BB84 mediante Qiskit Aer,
incorpora un ataque intercept-resend, simula ruido del canal y
utiliza una prueba estadística sobre el QBER para identificar
errores superiores al nivel basal esperado.

## Funcionalidades implementadas

### 1. Protocolo BB84

- Generación de bits y bases aleatorias para Alice.
- Preparación de estados cuánticos en bases Z y X.
- Medición de Bob en bases aleatorias.
- Cribado de posiciones con bases coincidentes.
- Cálculo del QBER.
- Selección de muestras públicas sin reemplazo.
- Retirada de los bits revelados de la clave restante.

### 2. Ataque de Eve y ruido

- Ataque intercept-resend con interceptación parcial.
- Fracciones de interceptación entre 0 y 1.
- Medición y retransmisión de señales por Eve.
- Ruido despolarizante del canal.
- Errores de lectura configurables.
- Semillas para reproducibilidad experimental.

### 3. Detección estadística

El detector utiliza una prueba binomial unilateral:

- H0: el QBER corresponde al ruido basal del canal.
- H1: el QBER supera el nivel esperado.

Se calcula un valor-p utilizando el número de errores de la
muestra pública.

El nivel de significancia utilizado es alpha = 0.05.

Se declara una anomalía estadísticamente significativa cuando
el valor-p es menor o igual a alpha.

La detección de un exceso de errores no demuestra por sí sola
la presencia de Eve, porque también pueden existir otras
fuentes de ruido no modeladas.

### 4. Experimentos y visualizaciones

Se implementaron:

- Calibración del ruido basal.
- Experimentos con diferentes fracciones de interceptación.
- Comparación de tamaños de muestra.
- Medición de tasas de detección.
- Medición de falsos positivos.
- Gráficas de QBER y curvas ROC.
- Validación estadística con sesiones independientes.

## Instalación

El proyecto utiliza Python y Qiskit Aer.

### Windows con PowerShell

```powershell
git clone https://github.com/Jfrc72/Proyecto-BB84.git
cd Proyecto-BB84

py -3.12 -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si se utiliza otra versión compatible de Python, debe
verificarse la disponibilidad de las dependencias.

### macOS o Linux

```bash
git clone https://github.com/Jfrc72/Proyecto-BB84.git
cd Proyecto-BB84

python3.12 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

En los comandos siguientes se utiliza `python`. En Windows,
puede reemplazarse por `.\.venv\Scripts\python.exe`.

## Ejecución

### Demostración del protocolo ideal

```bash
python demo.py
python demo.py --senales 4096 --muestra 1024 --semilla 42
python demo.py --circuitos
python demo.py --guardar resultados/sesion_ideal.json
```

Parámetros:

- `--senales`: cantidad de señales enviadas.
- `--muestra`: cantidad de bits cribados revelados.
- `--semilla`: semilla para reproducibilidad.
- `--circuitos`: muestra circuitos cuánticos.
- `--guardar`: exporta resultados en JSON.

### Simulación de Eve y ruido

```bash
python demo_eve_ruido.py
```

Ejecuta escenarios ideales, ataques parciales de Eve,
ruido del canal y combinaciones de ataque y ruido.

### Calibración del ruido

```bash
python calibrar_ruido.py
```

Permite estudiar el QBER basal del canal sin Eve.

### Detección estadística

```bash
python demo_deteccion.py
```

Ejecuta escenarios con y sin Eve y calcula:

- QBER observado.
- QBER basal.
- Número de errores.
- Valor-p binomial.
- Decisión estadística.
- Longitud restante de la clave.

### Experimentos piloto

```bash
python experimentos.py
```

Ejecuta 300 simulaciones distribuidas entre:

- Interceptación: 0 %, 10 %, 25 %, 50 % y 100 %.
- Ruido basal: 1 % y 3 %.
- Muestras: 128, 256 y 512 bits.
- 10 repeticiones por configuración.

Los resultados se guardan en:

`resultados/experimentos_bb84.csv`

### Generación de gráficas

```bash
python graficas.py
```

Genera:

- `01_qber_vs_eve.png`
- `02_detection_rate.png`
- `03_false_positives.png`
- `04_roc_curves.png`

También exporta `resultados/resumen_experimentos.csv`.

### Validación estadística final

```bash
python validacion_final.py
python analisis_validacion.py
```

La validación utiliza:

- Eve: 0 % y 10 %.
- Ruido basal: 1 % y 3 %.
- Muestras: 128, 256 y 512 bits.
- 100 sesiones independientes por combinación de ruido y ataque.

En total se ejecutan 400 sesiones cuánticas y 1200
evaluaciones estadísticas.

Las tres muestras de una misma sesión son anidadas y
no constituyen sesiones independientes entre sí.

## Resultados experimentales

### Calibración

En las pruebas de calibración, los niveles basales
observados estuvieron próximos a los objetivos:

| QBER objetivo | QBER observado |
|---|---|
| 0 % | 0 % |
| 1 % | 0.992 % |
| 3 % | 3.036 % |

### Detección de Eve al 10 %

Resultados de 100 sesiones por configuración:

| Muestra | Ruido 1 % | Ruido 3 % |
|---|---|---|
| 128 bits | 64 % | 41 % |
| 256 bits | 87 % | 64 % |
| 512 bits | 99 % | 85 % |

### Falsos positivos

| Muestra | Ruido 1 % | Ruido 3 % |
|---|---|---|
| 128 bits | 6 % | 3 % |
| 256 bits | 5 % | 3 % |
| 512 bits | 3 % | 4 % |

Los resultados son compatibles con el nivel de
significancia del 5 %, considerando la variabilidad
estadística de las simulaciones.

### QBER promedio

| Escenario | 128 bits | 256 bits | 512 bits |
|---|---|---|---|
| Sin Eve, ruido 1 % | 0.94 % | 0.91 % | 0.95 % |
| Eve 10 %, ruido 1 % | 3.37 % | 3.44 % | 3.61 % |
| Sin Eve, ruido 3 % | 2.91 % | 2.98 % | 3.10 % |
| Eve 10 %, ruido 3 % | 5.34 % | 5.33 % | 5.37 % |

## Interpretación de resultados

Los experimentos muestran que el QBER aumenta cuando
Eve intercepta una mayor proporción de señales.

El tamaño de muestra influye directamente en la
capacidad estadística de detectar ataques débiles.

Con ruido basal del 1 %, la detección de Eve al 10 %
aumentó del 64 % al 99 % al pasar de 128 a 512 bits.

Con ruido basal del 3 %, aumentó del 41 % al 85 %.

El ruido adicional dificulta distinguir los errores
provocados por Eve de los errores habituales del canal.

Los falsos positivos observados estuvieron entre
el 3 % y el 6 % en la validación final.

## Pruebas automatizadas

```bash
python -m unittest discover -s tests -v
python -m pip check
```

Se implementaron 33 pruebas automatizadas:

- 13 pruebas del protocolo BB84.
- 10 pruebas de Eve y ruido.
- 10 pruebas del detector estadístico.

La última ejecución reportó 33 pruebas exitosas.

## Organización

```text
Proyecto-BB84/
├── bb84.py
├── demo.py
├── eve_ruido.py
├── demo_eve_ruido.py
├── calibrar_ruido.py
├── deteccion_qber.py
├── demo_deteccion.py
├── experimentos.py
├── graficas.py
├── validacion_final.py
├── analisis_validacion.py
├── config_experimentos.json
├── requirements.txt
├── README.md
├── docs/
│   └── INTEGRACION.md
├── tests/
│   ├── test_bb84.py
│   ├── test_eve_ruido.py
│   └── test_deteccion_qber.py
└── resultados/
    ├── experimentos_bb84.csv
    ├── resumen_experimentos.csv
    ├── validacion_final.csv
    ├── resumen_validacion.csv
    └── graficas/
```

La carpeta `resultados/` se genera localmente y está
excluida de Git mediante `.gitignore`.

## Experimentos acordados en la propuesta

El archivo `config_experimentos.json` describe el diseño
experimental originalmente acordado:

- Interceptación: 0, 0.10, 0.25, 0.50 y 1.00.
- Canal ideal y ruido basal cercano al 1 % y 3 %.
- Muestras de 64, 256 y 1024 bits.
- Al menos 300 sesiones independientes por combinación.

Los experimentos implementados hasta ahora son un piloto
y una validación complementaria.

Por tanto, todavía no se ha ejecutado íntegramente
el diseño establecido en la configuración original.

Los objetivos de desempeño propuestos son alcanzar
al menos 90 % de detección y como máximo 5 % de falsas
alarmas. Las configuraciones que no los cumplan deben
reportarse sin modificar los resultados.

## Supuestos y limitaciones

El simulador utiliza señales independientes y un qubit
por señal, con un canal clásico autenticado para el
anuncio de bases.

Las semillas permiten reproducir los experimentos,
pero no representan un mecanismo criptográfico seguro
para generar claves reales.

No se implementan reconciliación de errores ni
amplificación de privacidad.

El detector presupone un nivel de ruido basal conocido.
En una implementación real, ese nivel debe estimarse
independientemente y considerar su incertidumbre.

Los bits revelados públicamente deben excluirse de
cualquier clave criptográfica final.

Los resultados experimentales dependen del modelo
de ruido, del ataque simulado y de las condiciones
evaluadas. No constituyen una demostración general
de seguridad del protocolo BB84.

## Referencias

- [Bennett y Brassard, BB84 (1984), reimpresión](https://arxiv.org/abs/2003.06557).
- [Qiskit: QuantumCircuit](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.QuantumCircuit).
- [Qiskit Aer: simuladores](https://qiskit.github.io/qiskit-aer/tutorials/1_aersimulator.html).
- [Qiskit Aer: modelos de ruido](https://qiskit.github.io/qiskit-aer/tutorials/3_building_noise_models.html).
```
