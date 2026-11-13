# GLOBAL · Quién hace qué, con qué script y cómo se conecta todo

Este archivo es el mapa del equipo. Cada integrante debe poder explicar **su** parte sin mirar el código, y saber **qué recibe y qué entrega** a la siguiente.

## 1. El flujo completo en una imagen

```
 datos/ (crudo, NO se toca)
   │
   ▼
 ┌────────────────────┐   salidas/limpio/*.parquet
 │ 1 HELLEN           │──────────────────────────────┐
 │ 1_leer_limpiar.py  │                              │
 └────────────────────┘                              ▼
                                       ┌────────────────────┐
         ajustes.py  ◄──── corrige ────│ 2 NAT              │  ¿existen las tablas/columnas?
         (NAT lo cuida)                │ 2_revisar.py       │  tasa base, línea de tiempo
                                       └────────────────────┘
                                                     │ OK
                                                     ▼
                                       ┌────────────────────┐   salidas/entrena.parquet
                                       │ 3 KATH             │   salidas/predice.parquet
                                       │ 3_variables.py     │───────────────┐
                                       └────────────────────┘               │
                                                                            ▼
                                       ┌────────────────────┐   salidas/prob.parquet
                                       │ 4 SOPHIA           │───────────────┐
                                       │ 4_modelo.py        │               │
                                       └────────────────────┘               ▼
                                       ┌────────────────────┐   salidas/submission.csv
                                       │ 5 LIZ              │──> ENTREGA
                                       │ 5_entregar.py      │
                                       └────────────────────┘
                     NAT integra, cronometra, decide y presenta
```

**Los contratos** (lo que no se puede romper entre una y otra):

| De → a | Archivo | Qué debe cumplir |
|---|---|---|
| Hellen → Kath | `salidas/limpio/<tabla>.parquet` | 1 archivo por tabla; columnas en minúsculas sin tildes; IDs como texto; fechas como fecha; montos como número |
| Kath → Sophia | `entrena.parquet`, `predice.parquet` | 1 fila por empresa (`id` único); columnas `target` y `target_monto`; las mismas variables en ambas |
| Sophia → Liz | `prob.parquet` | columnas `id` y `prob`; una fila por empresa de `predice`; prob entre 0 y 1 |
| Liz → jurado | `submission.csv` | nombres de columna de `ajustes.ENTREGA`; 1 fila por empresa; exactamente K priorizadas |
| Nat → todas | `ajustes.py` | los nombres reales de tablas, columnas, corte, horizonte, filtro del target y cupos |

Si cada una respeta su contrato, cualquiera puede rehacer su paso sin romper el de las demás.

---

## 2. NAT · Líder e integradora

**Objetivo:** que el flujo corra de punta a punta con los datos reales y que el equipo entregue a tiempo una historia clara.

**Scripts:** `ajustes.py` y `2_revisar.py`.

| Bloque | Qué hace | Por qué |
|---|---|---|
| `ajustes.py` | nombres de tablas y columnas, `CORTE`, `CORTE_ANTERIOR`, `HORIZONTE`, `HISTORIA`, `EVENTOS`, `TARGET_FILTRO`, `FUERA`, `CUPOS`, `ENTREGA` | es **lo único** que cambia entre la práctica y el reto real |
| `2_revisar.py` §1 | verifica que cada tabla y columna nombrada exista | si un nombre está mal, detiene todo con un mensaje claro |
| §2 | tasa base en cada corte | decide la métrica (si es < 5%, AUC-PR) y es el "azar" contra el que se compara |
| §3 | capacidad K | cuántas empresas se priorizan |
| §4 | gráfico `2_linea_tiempo.png` | muestra corte, horizonte y que entrenamos con el pasado |

**Debe dominar:** corte, horizonte, target y fuga (`02_flujo_y_conceptos.md`), el negocio (`01_factoring.md`, `papers/01_factoring.md`) y las respuestas al jurado (`12_jurado.md`).
**Plan B:** `11_que_hacer_si.md` (si el reto llega distinto) y `papers/00_INDICE.md` (una cita por decisión).
**Frase al jurado:** *"Definimos el corte el 1 de julio: todo lo anterior describe a la empresa y lo posterior es lo que queremos predecir. Entrenamos con el corte anterior y comprobamos en uno que el modelo nunca vio."*

---

## 3. HELLEN · Data Engineer 1 (crudo → limpio)

**Objetivo:** convertir archivos sucios en tablas limpias y confiables **sin perder ni inventar datos**.

**Script:** `1_leer_limpiar.py`.

| Bloque | Qué hace | Por qué |
|---|---|---|
| Macros SQL `txt`, `idn`, `num`, `numero`, `fecha` | una función de limpieza por tipo de dato | se escribe una vez y se aplica a cualquier columna |
| Leer todo como texto (`all_varchar=true`) | nada se rompe al leer | el tipo se decide **midiendo**, no adivinando |
| Decidir el tipo (95%) | si ≥ 95% de los valores se convierten a número o fecha, la columna es de ese tipo | tolera algunos valores sucios sin perder la columna |
| IDs como texto | `ruc`, `id_`, `cod_` nunca son números | se perderían ceros y aparecerían `.0` |
| `SELECT DISTINCT` | quita duplicados exactos | gráfico `1_filas.png` muestra cuántos |

**Debe dominar:** `06_limpieza_casos.md`, `10_eficiencia_y_tiempo.md`, `09_funciones_clave.md`.
**Plan B:** `extra/limpieza_pandas.py` + `16_si_la_limpieza_falla.md` (mismo resultado sin DuckDB, con diagnóstico por columna).
**Frase al jurado:** *"Leímos todo como texto y decidimos el tipo de cada columna midiendo qué porcentaje se convertía. Los RUC los tratamos como texto, los códigos de 'sin dato' como 999999 los pasamos a nulo y quitamos los duplicados exactos."*

---

## 4. KATH · Data Engineer 2 (limpio → tabla del modelo)

**Objetivo:** una fila por empresa con variables que **solo miran el pasado**, y el target bien construido.

**Script:** `3_variables.py`.

| Bloque | Qué hace | Por qué |
|---|---|---|
| `armar_tabla(corte)` a) | atributos de la empresa; las fechas se vuelven "días antes del corte" | el modelo entiende distancias, no fechas |
| b) eventos | por cada tabla: conteo, monto, promedio, eventos de los últimos 3 meses y recencia | resumen RFM: frecuencia, monto, recencia |
| **`WHERE fecha < corte AND fecha >= corte - HISTORIA`** | **la línea anti-fuga** | con `<=` o sin límite, el Gini saltó de 0.31 a 0.62 en una prueba: era trampa |
| c) target | 1 si hubo factoring (con filtro) en [corte, corte + horizonte) | define exactamente qué predecimos |
| `assert id.is_unique` | si un JOIN duplicó empresas, se detiene | mejor un error que un resultado falso |
| Prueba de fuga | Gini de cada variable sola (> 0.5 = sospecha) | gráfico `3_fugas.png` |

**Debe dominar:** `07_variables.md`, `05_fugas_y_validacion.md`, `09_funciones_clave.md`.
**Plan B / ampliación:** `temporal/varios_cortes.py` (más cortes si hay pocos positivos) y `temporal/pronostico.py` si el reto es de series de tiempo → `17_series_de_tiempo.md`.
**Frase al jurado:** *"Cada variable se calcula solo con datos anteriores al corte, con la misma ventana de 12 meses en entrenamiento y en predicción. Probamos cada variable sola: ninguna supera Gini 0.5, así que no hay trampa evidente."*

---

## 5. SOPHIA · Data Scientist 1 (qué modelo y cuánto mide)

**Objetivo:** elegir el modelo con una validación honesta y la métrica oficial.

**Script:** `4_modelo.py`.

| Bloque | Qué hace | Por qué |
|---|---|---|
| Candidatos | regla de 1 variable, logística (imputar, log con signo, escalar, one-hot, C=0.1) y LightGBM (15 hojas, 50 mínimo por hoja) | de lo más simple a lo más complejo |
| Validación OOF | 5 pliegues: cada fila se predice con un modelo que no la vio | compara a todos los modelos con la misma vara |
| Examen fuera de tiempo | Gini en el corte actual | comprueba que funciona en el futuro |
| Regla de elección | el mejor OOF; si uno más simple está a < 0.005, gana el simple | explicable y más robusto |
| Alarma | Gini > 0.8 → sospechar fuga | demasiado bueno para ser verdad |
| Gráficos | `4_modelos.png`, `4_deciles.png` (lift), `4_importancia.png` | resultado, valor de negocio y explicación |

**Resultado en la práctica:** regla 0.260 · **logística 0.292** · LightGBM 0.246 (Gini examen).
**Debe dominar:** `03_metricas.md`, `04_modelos.md`, `05_fugas_y_validacion.md`, `14`, `15`, `19`, `20`.
**Plan B / ampliación:** `extra/metricas.py` (si la métrica no es Gini), `extra/mas_modelos.py` (7 modelos), `extra/uno_o_varios.py` (global vs por zona), `temporal/arima_paso_a_paso.py`.
**Frase al jurado:** *"Comparamos regla, logística y LightGBM con la misma validación fuera de pliegue. Ganó la logística: 0.29 de Gini contra 0.26 de ordenar solo por ventas. El 10% de arriba convierte el doble que el promedio."*

---

## 6. LIZ · Data Scientist 2 (por qué predice y a quién llamar)

**Objetivo:** convertir probabilidades en una **decisión de negocio** que cumpla las reglas, y explicarla.

**Script:** `5_entregar.py`.

| Bloque | Qué hace | Por qué |
|---|---|---|
| Monto si convierte | mediana de lo financiado en su rubro (corte anterior) | robusto a montos extremos |
| Valor esperado | prob × monto | prioriza soles esperados, no solo probabilidad |
| Cupos por zona (resto mayor) | reparte K según `CUPOS` y que sume exacto | cumple la regla sin discusión |
| `nlargest` por zona | las de mayor valor en cada zona | la lista final |
| Controles | 1 fila por empresa, prob en [0, 1], sin vacíos, exactamente K priorizadas | un CSV mal formado anula todo |
| Gráfico `5_rubros.png` | conversión por rubro | un hallazgo de negocio para la historia |

**Resultado en la práctica:** las 125 priorizadas convierten 52% contra 19.9% de la base (2.6×).
**Debe dominar:** `08_priorizacion_y_entrega.md`, `01_factoring.md`, `12_jurado.md`, `18_optimizacion_restricciones.md`.
**Plan B / ampliación:** `optimizacion/priorizar_restricciones.py` (presupuesto, mínimos y máximos, ejecutivos; greedy contra óptimo).
**Frase al jurado:** *"No llamamos a los de mayor probabilidad: llamamos a los de mayor valor esperado, respetando los cupos por zona. La lista convierte 2.6 veces más que la base."*

---

## 7. Cómo trabajamos durante el evento

| Momento | Nat | Hellen | Kath | Sophia | Liz |
|---|---|---|---|---|---|
| Antes de las 14:00 (vie) | cerrar la base de conocimiento | — | — | — | — |
| 15:30 llegan los datos | leer el enunciado en voz alta; definir fila, target, corte y métrica | correr el paso 1 con los datos reales | leer el diccionario de datos con Nat | revisar la métrica oficial: ¿es Gini? | revisar el formato de entrega y las reglas de priorización |
| +1 h | `ajustes.py` + paso 2 en verde | bitácora de limpieza | paso 3 + prueba de fuga | — | plantilla del CSV con IDs reales |
| +2 h | — | apoyo en variables nuevas | 3–5 variables nuevas | paso 4: primer modelo | paso 5: **primera entrega válida** |
| ~22:00 | **primera entrega** (aunque sea la regla simple) | | | | |
| Noche | historia y diapositivas | conciliar montos | más variables, con fugas revisadas | `mas_modelos.py`, métrica oficial | priorización con restricciones, hallazgos |
| 9:00 (sáb) | **congelar**: ya no se cambia el modelo | | | | |
| 9:00–10:30 | ensayo de la exposición; cada una explica su parte | | | | |

**Reglas del equipo:**
1. **Primero una entrega válida, después una buena.** Una regla simple entregada vale más que un LightGBM sin terminar.
2. **Un solo `ajustes.py`.** Lo edita Nat; las demás le piden los cambios.
3. **Cada cambio se mide** con la misma validación. Si no sube el OOF, no entra.
4. **Si algo da "demasiado bien"** (Gini > 0.8, una variable > 0.5): se detiene todo y se busca la fuga.
5. **Cada una puede explicar su script línea por línea.** Lo que no se pueda explicar, no se usa.
6. **Declarar el uso de IA** según las reglas del evento.

## 8. Índice de todo el kit

| Carpeta | Qué hay |
|---|---|
| `scripts/` | los 5 pasos + `ajustes.py` |
| `scripts/extra/` | `metricas.py`, `mas_modelos.py`, `uno_o_varios.py`, `limpieza_pandas.py` |
| `scripts/temporal/` | `pronostico.py`, `arima_paso_a_paso.py`, `varios_cortes.py`, `datos_temporales.py` |
| `scripts/optimizacion/` | `priorizar_restricciones.py` |
| `apuntes/` | 00 plan · 01–13 base · 14 métricas · 15 modelos · 16 limpieza · 17 series · 18 optimización · 19 casos · 20 uno o varios modelos |
| `papers/` | referencias con resumen y enlace |
