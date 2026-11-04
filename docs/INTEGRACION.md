# Cómo continuar el proyecto

## Reparto

| Integrante | Trabajo |
|---|---|
| Juan | Base ideal, circuitos, cribado, QBER, semillas, demostración y pruebas básicas. |
| Daniel | Interceptación parcial de Eve, ruido de compuertas y lectura, calibración e integración del canal. |
| Tomás | Detector, repetición de experimentos, falsas alarmas, detección, intervalos de confianza y gráficas. |

Cada integrante escribe la explicación de su parte del informe. Los tres
revisamos los resultados y preparamos la demostración y la defensa.

## Funciones que ya pueden usar

```python
from bb84 import ejecutar_sesion, tomar_muestra

sesion = ejecutar_sesion(n_senales=4096, semilla=42)
muestra = tomar_muestra(
    sesion["clave_alice"],
    sesion["clave_bob"],
    m=256,
    semilla=sesion["semillas"]["muestra"],
)
print(muestra["errores"], muestra["m"], muestra["qber"])
```

También se pueden usar las etapas por separado:

| Función | Devuelve |
|---|---|
| `generar_datos(n_senales, semilla)` | Un diccionario con `bits_alice`, `bases_alice` y `bases_bob`. |
| `preparar_estado(bit, base)` | Un `QuantumCircuit` con el estado que envía Alice, sin medir. |
| `medir_en_base(circuito, base)` | Una copia del circuito con la medición de Bob. |
| `construir_circuito(bit, base_alice, base_bob)` | El circuito completo de una señal ideal. |
| `simular_mediciones(datos, semilla, simulador=None)` | La lista de bits medidos por Bob, en el orden de las señales. |
| `cribar(datos, bits_bob)` | Las posiciones conservadas y las dos claves cribadas. |
| `calcular_qber(clave_alice, clave_bob)` | La proporción de errores, entre 0 y 1. |
| `tomar_muestra(clave_alice, clave_bob, m, semilla)` | Muestra pública y claves restantes, sin los bits revelados. |

Los bits son listas de enteros 0/1 y las bases son listas de letras `Z`/`X`.
Todas las listas de señales conservan su orden. Las funciones rechazan
longitudes incompatibles.

## Formato de la sesión

`ejecutar_sesion` devuelve un diccionario con estos campos:

```text
n_senales, semilla
semillas: datos, medicion, muestra
bits_alice, bases_alice, bases_bob, bits_bob
posiciones_cribadas, clave_alice, clave_bob
n_cribados, errores_cribados, qber_cribada
```

`qber_cribada` vale `None` si no hubo ninguna coincidencia de bases. La función
`calcular_qber` lanza `ValueError` si se intenta comparar claves vacías.

`tomar_muestra` devuelve:

```text
m, indices, bits_alice, bits_bob, errores, qber
clave_restante_alice, clave_restante_bob
```

**Los índices de la muestra son posiciones dentro de la clave cribada.**
Las posiciones de `posiciones_cribadas`, en cambio, apuntan a las señales
originales. Si hace falta pasar de una a otra:

```python
posiciones_originales = [
    sesion["posiciones_cribadas"][i] for i in muestra["indices"]
]
```

Los JSON de `demo.py --guardar ...` contienen `versiones`, `sesion` y `muestra`.
Así se puede comprobar con qué versiones y semillas se generaron.

## Para Daniel

Puede crearse `eve_ruido.py` para los modelos del canal. Para añadir solo ruido
ya se acepta un `AerSimulator` externo:

```python
from qiskit_aer import AerSimulator
from bb84 import ejecutar_sesion

# modelo_ruido es el NoiseModel que se defina y calibre en esta parte.
simulador = AerSimulator(noise_model=modelo_ruido, max_parallel_threads=1)
sesion = ejecutar_sesion(4096, semilla=42, simulador=simulador)
```

Para Eve hay que extender la etapa de simulación: elegir qué señales
intercepta, sus bases y las mediciones/reenvíos. Se puede reutilizar
`preparar_estado`, introducir las operaciones de Eve y cerrar con
`medir_en_base`. Bob usa el qubit 0 y el bit clásico 0. Si se necesita guardar
una medición de Eve en el circuito, debe usarse otro bit clásico.

La agrupación actual solo distingue bit, base de Alice y base de Bob. Al añadir
Eve, también hay que distinguir señales interceptadas, bases de Eve y cualquier
otra diferencia del circuito. No se deben simular señales atacadas con el
circuito de las que no fueron interceptadas. Los pasos de cribado y muestreo
se pueden reutilizar después con la nueva lista `bits_bob`.

Primero se valida el ataque sin ruido: la QBER de muchas señales debe acercarse
a `f / 4`. Después se calibran las configuraciones sin Eve para obtener QBER
basales cercanas al 1 % y al 3 %. Se guarda la QBER realmente medida, además
de los parámetros del ruido. Los errores de lectura y compuertas no producen
necesariamente la misma tasa de error.

## Para Tomás

Puede crearse `detector.py` para el umbral y `experimentos.py` para las sesiones.
El detector necesita `muestra["errores"]` y `muestra["m"]`. La QBER de toda la
clave se guarda para validar la simulación; no debe usarse para decidir la
alerta ni para ajustar el umbral.

`config_experimentos.json` guarda los escenarios de la propuesta. Todavía no
es un ejecutor de esa cuadrícula: la demostración disponible es solo ideal.

1. Separar sesiones de calibración y de evaluación. Calibrar el umbral usando
   únicamente sesiones sin Eve, para cada configuración de ruido y tamaño de
   muestra. Mantener el umbral fijo al evaluar.
2. Usar sesiones nuevas para medir falsas alarmas con `f = 0` y detección con
   `f > 0`. Cada sesión lleva una semilla distinta y registrada. No repetir
   300 veces una misma semilla.
3. Ejecutar al menos 300 sesiones por combinación de `f`, ruido y `m`. Las
   sesiones usadas para calibrar no cuentan como evaluación.
4. Guardar por sesión: identificador, semilla, fase de calibración/evaluación,
   `f`, parámetros del ruido, QBER basal calibrada, `m`, errores de muestra,
   QBER de muestra, umbral y decisión.
5. Calcular tasas e intervalos de confianza y buscar el menor `m` de los
   estudiados que alcance 90 % de detección y máximo 5 % de falsas alarmas.
   Si ninguno cumple, se reporta; no se ajusta el umbral mirando los ataques.

Las muestras de 64, 256 y 1024 bits se toman **después del cribado**. Hay que
generar suficientes señales antes de llamar a `tomar_muestra`. La función no
acepta muestras menores en silencio.

La cuadrícula de evaluación son 5 fracciones, 3 configuraciones de ruido y 3
tamaños: 45 combinaciones, o 13 500 sesiones si se hacen 300 por combinación.
La ejecución se puede repartir entre los tres conservando semillas distintas
y el mismo formato de resultados.

## Trabajar en Git

Después de descargar la base, cada uno puede crear su rama:

```bash
git switch main
git pull origin main
git switch -c daniel/eve-ruido
```

Tomás puede usar `tomas/detector`. Antes de integrar cambios, ejecutar:

```bash
python -m unittest discover -s tests -v
```

Al cambiar un modelo o una función, agregar una prueba que compruebe su efecto
físico o estadístico. Al final se integra la demostración para variar `f`,
ruido y `m`, y mostrar la decisión del detector.
