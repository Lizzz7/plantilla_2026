# Guía de MODELOS (rol de Sophia) — para Liz

> **Qué es:** todo lo que hace la Data Scientist 1 ("qué modelo y cuánto mide"), explicado a fondo para que tú puedas hacerlo, defenderlo y reemplazarla en cualquier momento.
> **Qué NO es:** limpieza de datos, construcción de variables, priorización comercial ni submission (eso lo tienen tus otras guías).
> **Código:** dos scripts nuevos, **probados hoy (13/11)** con los datos de prueba de la plantilla (20 000 empresas):
> - `sophia_modelos.py` → el torneo completo (regla, logística, LightGBM y variantes, ensamble, elección, calibración, monto, importancia). **No depende de la plantilla**: si la plantilla falla o no se permite, esto corre solo con pandas, scikit-learn y LightGBM.
> - `sophia_extras.py` → fugas, Optuna, ¿uno o varios modelos?, K-means, Tweedie.
>
> Ambos dan los **mismos números que la plantilla** (logística Gini OOF 0.3225 vs 0.3224; examen 0.349 vs 0.348). Eso es una prueba de reproducibilidad que puedes contar al jurado: "lo reimplementamos de forma independiente y dio lo mismo".

---

## Índice

**PARTE A — EL FLOW: qué hacer cuando presentan el problema**
- A1. Los primeros 40 minutos (ficha del problema)
- A2. Del enunciado a la "frase-modelo"
- A3. Árbol: tipo de problema → modelos a comparar
- A4. Reloj de Sophia con compuertas
- A5. El flow paso a paso (14 pasos)
- A6. 10 enunciados posibles y cómo traducirlos

**PARTE B — FUNDAMENTOS**
- B1. Qué es aprender de datos (y por qué casi todo es validar)
- B2. Validación: OOF, estratificada, fuera de tiempo, por bloques
- B3. Métricas con código y lectura

**PARTE C — LOS MODELOS, UNO POR UNO**
- C0 Regla sin modelo · C1 Logística · C2 Árbol de decisión · C3 Random Forest · C4 LightGBM · C5 XGBoost · C6 CatBoost
- C7 Desbalance · C8 Ensamble · C9 Calibración · C10 Monto (dos partes, Duan, Tweedie)
- C11 ¿Uno o varios modelos? · C12 Optuna · C13 K-means · C14 Series de tiempo · C15 Optimización de la lista

**PARTE D — DIAGNÓSTICO Y DECISIÓN**
- D1 Fugas · D2 Elegir el modelo · D3 Importancia y explicación · D4 Tablero "si ves X → haces Y" · D5 Errores de modelado

**PARTE E — DEFENSA Y APOYO**
- E1 Frases · E2 Preguntas técnicas · E3 Copilot para modelos · E4 Tarjeta de bolsillo

**ANEXO** — código completo de `sophia_modelos.py` y `sophia_extras.py`

---

## Cómo se corre (2 minutos)

Copia los dos `.py` a `trabajo/` del repo del evento (son código nuevo: commit propio y línea en `docs/USO_DE_IA.md`). Desde la raíz:

```bash
S=~/datafest_trabajo/salidas         # Windows PowerShell: $S="$HOME\datafest_trabajo\salidas"
# torneo completo: entrena con el corte anterior, puntúa (y examina) el corte actual
python trabajo/sophia_modelos.py --tabla $S/tabla_modelo_t1.parquet --destino $S/tabla_modelo.parquet \
       --seleccion $S/seleccion_variables.csv --salida ~/datafest_trabajo/sophia
# rápido (sin importancia ni monto), para iterar
python trabajo/sophia_modelos.py --tabla $S/tabla_modelo_t1.parquet --destino $S/tabla_modelo.parquet --rapido --salida ~/datafest_trabajo/sophia
# si NO hay corte anterior: solo validación cruzada
python trabajo/sophia_modelos.py --tabla $S/tabla_modelo.parquet --salida ~/datafest_trabajo/sophia
# extras
python trabajo/sophia_extras.py fugas    --tabla $S/tabla_modelo_t1.parquet --destino $S/tabla_modelo.parquet
python trabajo/sophia_extras.py segmento --tabla $S/tabla_modelo_t1.parquet --seleccion $S/seleccion_variables.csv --segmento <variable>
python trabajo/sophia_extras.py optuna   --tabla $S/tabla_modelo_t1.parquet --seleccion $S/seleccion_variables.csv --segundos 300
python trabajo/sophia_extras.py tweedie  --tabla $S/tabla_modelo_t1.parquet --seleccion $S/seleccion_variables.csv
python trabajo/sophia_extras.py kmeans   --tabla $S/tabla_modelo_t1.parquet --seleccion $S/seleccion_variables.csv --k 4
```

Tiempos medidos (20 000 filas, 32 variables, laptop de 2 núcleos): torneo completo **16 s**, Optuna 60 s = 40 pruebas.

Salidas en `--salida`: `comparacion.csv`, `deciles_oof.csv`, `coeficientes.csv` (si gana la logística), `importancia.csv`, `predicciones.csv`.

---

# PARTE A — EL FLOW

## A1. Los primeros 40 minutos: la ficha del problema

La organización recomendó usar los primeros 30–40 min para planificar. Para Sophia eso significa **llenar esta ficha antes de tocar código**. Cada casilla vacía es un riesgo de entrenar el modelo equivocado durante horas.

| # | Pregunta | Por qué decide el modelo | Ejemplo (caso factoring) |
|---|---|---|---|
| 1 | **¿Qué es una fila?** (unidad) | define el grano de la tabla y qué se predice | una empresa (RUC) |
| 2 | **¿Qué se predice exactamente?** (target) | binario → clasificación; monto → regresión; ambos → dos partes | "hizo ≥ 1 operación de factoring no anulada" |
| 3 | **¿En qué ventana?** (horizonte) | el target mira `[corte, corte + horizonte)` | 6 meses: jul–dic 2025 |
| 4 | **¿Desde qué día se decide?** (corte) | todo lo que entra como variable debe ser < corte | 2025-07-01 |
| 5 | **¿Para quién?** (población) | a quién se entrena y a quién se puntúa | todas / no clientes / lista del banco |
| 6 | **¿Cómo nos miden?** (métrica oficial) | Gini → orden; R² → monto; F1 → umbral; valor → prob × monto | Gini (+ R² si hay monto) |
| 7 | **¿Qué se decide con el modelo?** | si hay capacidad/cupos, la salida final es una lista | 2.5% de la base con cupos por zona |

Y tres preguntas de datos (pregúntalas al mentor si no está claro):
- ¿Las tablas de perfil son una **foto al corte** o **de hoy**? (si son de hoy → fuga)
- ¿Hay operaciones vistas **dos veces** (registro interno + otra fuente)? (duplican el target)
- ¿Hasta qué fecha llegan los datos de **cada** tabla? (el corte no puede pasar la fecha más chica)

**Entregable de Sophia a los 40 min (compuerta C0):** la ficha completa en `trabajo/notas_modelo.md` + la "frase-modelo" (A2).

## A2. Del enunciado a la "frase-modelo"

Toda la noche se resume en una frase. Escríbela y que el equipo la apruebe:

> **"Para cada [UNIDAD] de [POBLACIÓN], con lo que el banco sabía al [CORTE], estimamos [P(EVENTO) y/o MONTO] en los [HORIZONTE] siguientes, medido con [MÉTRICA], para decidir [DECISIÓN] con [CAPACIDAD]."**

Ejemplo:
> "Para cada empresa del maestro, con lo que el banco sabía al 1 de julio de 2025, estimamos la probabilidad de que haga factoring con el BCP entre julio y diciembre, y el monto si lo hace; medimos con Gini y R², para decidir a qué 2.5% contactar respetando cupos por zona."

De la frase salen directamente:
- `FECHA_CORTE`, `HORIZONTE_MESES`, `TARGET` (en la config del pipeline).
- El tipo de modelo (A3).
- La validación: si la evaluación del banco es un periodo **posterior**, la validación **tiene** que ser fuera de tiempo.

## A3. Árbol: tipo de problema → modelos a comparar

```
¿Qué se predice?
│
├── 0/1 (convierte, compra, se va, cae en mora)  ──► CLASIFICACIÓN BINARIA
│      Comparar SIEMPRE: regla_1var → regla_top3 → logística → LightGBM (+pesos, +submuestra) → ensamble
│      ├─ tasa < 1%            → reportar AUC-PR y captura@k; probar submuestra con corrección de prior
│      ├─ filas < 3 000 o EPV < 10 → favorecer logística / regla; LightGBM con min_child_samples alto
│      ├─ categorías con cientos de valores (CIIU, ubigeo, pagador) → sumar CatBoost
│      └─ segmentos que se comportan distinto → C11 (global vs por segmento)
│
├── Monto (soles)  ──► REGRESIÓN
│      ├─ > 50% ceros  → DOS PARTES: P(monto>0) × E[monto | >0] en log + Duan  vs  Tweedie directo
│      └─ casi todo > 0 → LightGBM sobre log1p(monto) + Duan; línea base: mediana por rubro × tamaño
│
├── Probabilidad Y monto ("valor esperado")  ──► dos modelos; la probabilidad debe estar CALIBRADA
│
├── Varias opciones (canal, producto)  ──► un modelo por opción (o la opción como variable) → elegir la de mayor valor
│
├── Cantidad en el tiempo (efectivo por agencia/día)  ──► PRONÓSTICO: rezagos + LightGBM, validación por bloques (C14)
│
└── "Grupos / perfiles" sin target  ──► K-means (descriptivo) (C13)
```

**Siempre** la primera fila de la tabla de comparación es una regla sin modelo. Si el modelo no le gana, eso **también** es un resultado.

## A4. Reloj de Sophia con compuertas

Inicio = 15:30 vie (T+0). Cierre de modelo = 09:00 sáb.

| Compuerta | Hora aprox. | Qué debe existir | Si no existe… |
|---|---|---|---|
| **C0** | T+0:40 (16:10) | ficha + frase-modelo + config del target revisada | no se corre nada hasta tenerla |
| **C1** | T+2:30 (18:00) | `tabla_modelo.parquet` (del DE) con las 6 pruebas de A5-paso 3 en verde | ayudar al DE; mientras, preparar comandos |
| **C2** | T+3:00 (18:30) | `tabla_modelo_t1.parquet` (corte anterior) | seguir con CV y anotarlo como limitación |
| **C3** | T+3:30 (19:00) | primer torneo `--rapido` + revisión de fugas | — |
| **C4** | **T+6:30 (22:00)** | **modelo elegido v1 → primer submission válido en `main`** | entregar la regla si hace falta: algo válido > nada |
| **C5** | T+10 (01:30) | torneo completo, segmentos, monto, importancia | — |
| **C6** | T+13 (04:30) | Optuna (si sobra), bootstrap, decisión final | saltar Optuna |
| **C7** | **09:00 sáb** | **modelo congelado**; números finales en `notas_modelo.md` | — |

Regla de oro: **después de C4, cada mejora tiene que justificar su riesgo**. Cambiar de modelo a las 08:00 por +0.003 de Gini no vale la pena.

## A5. El flow paso a paso (14 pasos)

### Paso 1 · Leer el enunciado con la ficha (A1)
- **Haces:** subrayar unidad, evento, ventana, métrica, capacidad.
- **Decides:** frase-modelo.
- **Escribes:** `notas_modelo.md` → sección "Definiciones".
- **Error típico:** asumir que "cliente que hizo factoring" incluye otros bancos. Pregunta.

### Paso 2 · Traducir a configuración (con Nat y el DE)
- `FECHA_CORTE`, `HORIZONTE_MESES`, `TARGET` (tabla, id, fecha, **filtro**, monto).
- **Corte anterior** = corte − horizonte (para la tabla `_t1`).
- **Error típico:** el filtro `estado <> 'ANULADA'` con mayúsculas distintas a los datos → tasa 100%. Verifica con el `top5` del perfil.

### Paso 3 · Recibir la tabla del DE y hacer las 6 pruebas (contrato)

```python
import pandas as pd
t = pd.read_parquet(".../tabla_modelo.parquet")
assert t["id"].is_unique                                   # 1) grano: una fila por empresa
print(t["target"].mean())                                  # 2) tasa de positivos: ¿razonable? (no 0, no 0.9)
print(t["target"].value_counts())
print(t.filter(like="fecha").columns.tolist())             # 3) ¿quedó alguna fecha cruda? -> debería ser "días desde"
print(t.isna().mean().sort_values().tail(10))              # 4) cobertura: columnas casi vacías
# 5) Gini individual > 0.5 -> sospecha de fuga  (sophia_extras.py fugas)
# 6) PSI entre cortes > 0.25 -> variable inestable (seleccion_variables.csv, columna psi)
```

| Variable del código | Qué es |
|---|---|
| `t` | la tabla de modelo: filas = empresas, columnas = variables + `target` (+ `target_monto`) |
| `t["id"].is_unique` | `True` si ninguna empresa se repite. Si es `False`, un JOIN duplicó filas → el Gini se infla |
| `t["target"].mean()` | proporción de 1 = probabilidad base |
| `t.isna().mean()` | % de nulos por columna |

### Paso 4 · Diagnóstico: qué dice la data (2 min)
Mira estos 5 números (los imprime la primera línea de `sophia_modelos.py`):

```
train 20,000 filas · 32 variables (30 num, 2 cat) · tasa 18.93% · positivos 3,785 · EPV 118
```

| Número | Regla | Decisión |
|---|---|---|
| filas | < 3 000 → modelos simples; > 2 M → muestra para elegir | tamaño cómodo |
| tasa | < 1% severo; 1–10% moderado; > 10% leve | métrica secundaria (AUC-PR) |
| positivos | < 200 → cuidado con segmentos y con diferencias chicas | — |
| EPV = positivos / variables | < 10 → riesgo de sobreajuste | menos variables o más regularización |
| num / cat | muchas cat de alta cardinalidad → CatBoost | — |

### Paso 5 · Fugas antes de modelar
`sophia_extras.py fugas` → toda variable con Gini individual > 0.5 en train **o** en el corte actual se revisa a mano (D1). Resultado real de la prueba:

```
                          variable  gini_train  gini_actual  sospecha
   perfilclie__ops_ultimo_semestre       0.158        0.914      True   <- tabla "foto" tomada HOY
perfilclie__total_operaciones_hist       0.647        0.655      True   <- incluye operaciones futuras
        maestrocli__ventas_anuales       0.263        0.290     False
```
Ambas se sacan (DROP). La primera es la trampa clásica: parece inocente en el corte anterior y en el actual "sabe" el futuro.

### Paso 6 · Primer torneo rápido
`sophia_modelos.py ... --rapido`. Lees la tabla de comparación (B3 y D2).

### Paso 7 · Elegir v1 y avisar a Liz/Nat (C4)
Regla: mayor Gini, salvo que uno más simple esté a ≤ 0.005 → el simple. Frase: "regla X, modelo Y".

### Paso 8 · Torneo completo
Sin `--rapido`: importancia por permutación + monto.

### Paso 9 · ¿Uno o varios modelos?
`sophia_extras.py segmento` (C11).

### Paso 10 · Monto
Dos partes vs Tweedie (C10).

### Paso 11 · Calibración
Tabla de deciles: `p_media` vs `tasa` (C9).

### Paso 12 · Robustez
Bootstrap del Gini (D2), OOF vs examen, PSI de las top variables.

### Paso 13 · Optuna (solo si sobra)
`sophia_extras.py optuna --segundos 300` (C12). Si no gana en 5 pliegues, no se usa.

### Paso 14 · Congelar y documentar (C7)
`notas_modelo.md`: modo de validación, tabla de comparación, elegido y motivo, examen, top 5 variables, fugas excluidas, limitaciones.

## A6. 10 enunciados posibles y cómo traducirlos

| Enunciado (cómo lo dirían) | Unidad | Target | Modelo | Métrica natural | Trampa |
|---|---|---|---|---|---|
| "¿Qué empresas contratarán factoring en los próximos 6 meses?" | empresa | 0/1 en ventana | binario | Gini | operaciones anuladas / otros bancos |
| "Estimen el monto de factoring por empresa" | empresa | soles en ventana | dos partes / Tweedie | R² | muchos ceros, cola larga |
| "Valor esperado para priorizar con capacidad limitada" | empresa | prob y monto | binario + monto | Gini + valor capturado | probabilidad calibrada |
| "Identifiquen nuevos leads (no clientes)" | empresa no cliente | 0/1 | binario sobre no clientes | Gini | no tienen historial interno → variables de transacciones/red |
| "Empresas que ya hacen factoring en otro banco: ¿cuáles migran?" | empresa con factoring externo | 0/1 BCP | binario en ese segmento | Gini | pocos positivos |
| "¿Qué pagadores conviene atacar (confirming)?" | **pagador** | n.º/monto de proveedores que convierten | regresión o binario por pagador | Spearman / Gini | cambiar el grano completo |
| "¿Qué canal usar con cada empresa?" | empresa × canal | acepta por canal | un modelo por canal | Gini por canal + valor | sin datos por canal no se puede |
| "¿Cuándo contactar?" | empresa × mes | convierte ese mes | binario con variables de mes | Gini | fuga temporal |
| "Pronostiquen la demanda de factoring por zona/mes" | zona × mes | monto | LightGBM con rezagos | MAE / MAPE | validación al azar prohibida |
| "Segmenten la cartera" | empresa | — | K-means | silueta + tasa por grupo | presentar como descriptivo |

---

# PARTE B — FUNDAMENTOS

## B1. Qué es aprender de datos (y por qué casi todo es validar)

**Aprendizaje supervisado:** tienes ejemplos del pasado con la respuesta conocida (empresas con su target) y buscas una función f(variables) → respuesta que funcione en ejemplos **nuevos**.

Tres ideas que sostienen todo lo demás:

1. **Error en datos vistos ≠ error en datos nuevos.** Un modelo puede memorizar (sobreajuste). Por eso solo vale lo que se mide en datos que el modelo **no vio**.
2. **Sesgo vs varianza.**
   - Sesgo alto: modelo demasiado simple, no capta la forma (una regla de una variable).
   - Varianza alta: modelo demasiado flexible, cambia mucho con pequeñas diferencias en los datos (un árbol profundo).
   - La regularización (C en la logística, `min_child_samples` en LightGBM, early stopping) es el control de ese balance.
3. **El tiempo manda.** El banco usará el modelo en el **futuro**. Toda variable debe existir **antes** del corte, y la mejor validación imita ese salto de tiempo.

**Cadena de un proyecto de propensión:**
```
ventana de variables (pasado) │ CORTE │ ventana del target (futuro)
 ─────────────────────────────┼───────┼──────────────────────────►
   features: RFM, saldos,     │ día de│ ¿hizo factoring en los
   red, plazos (< corte)      │decidir│  próximos 6 meses?
```

## B2. Validación

### B2.1 Validación cruzada estratificada y predicciones OOF

```python
def pliegues(y, k=5):
    return list(StratifiedKFold(k, shuffle=True, random_state=SEMILLA).split(np.zeros(len(y)), y))

def oof(ajustar, X, y, folds, **kw):
    p = np.zeros(len(y))
    for a, b in folds:
        p[b] = ajustar(X.iloc[a], y.iloc[a], X.iloc[b], **kw)
    return p
```

| Variable | Qué es | Por qué así |
|---|---|---|
| `y` | vector 0/1 del target | se usa para estratificar |
| `k=5` | número de pliegues | 5 es el estándar: 80% entrena, 20% valida, 5 veces |
| `StratifiedKFold` | divide manteniendo la tasa de positivos en cada pliegue | con 2% de positivos, un pliegue podría quedar casi sin positivos |
| `shuffle=True` | mezcla antes de dividir | si la tabla viene ordenada (por fecha, por id), los pliegues no quedan sesgados |
| `random_state=SEMILLA` (42) | semilla | mismos pliegues en cada corrida = mismos números = defendible |
| `np.zeros(len(y))` | "X falso" | StratifiedKFold solo necesita el tamaño y `y` |
| `folds` | lista de 5 pares `(a, b)` | `a` = índices de entrenamiento, `b` = de validación |
| `ajustar` | cualquier función `(Xtr, ytr, Xva) → predicciones` | así **todos** los modelos usan el mismo esquema |
| `p` | vector de predicciones OOF | cada `p[i]` lo hizo un modelo que no vio la fila `i` |
| `**kw` | parámetros extra del modelo | ej. `k=1` para la regla, `peso=True` para LightGBM |

**Por qué OOF y no un 70/30:** usa el 100% de las filas para medir (más estable) y permite comparar modelos con **exactamente las mismas particiones** (comparación justa). Además las predicciones OOF sirven para calibrar (C9) y para ensamblar (C8) sin fuga.

### B2.2 Fuera de tiempo (out-of-time) — la más honesta

```
tabla_modelo_t1 (corte 2025-01-01, target ene–jun 2025)  ──entrena──►  modelo
tabla_modelo    (corte 2025-07-01, target jul–dic 2025)  ◄─puntúa──    (si trae target: EXAMEN)
```
- Dentro de `_t1` se eligen los modelos con OOF.
- El corte actual es el **examen**: no se usa para elegir nada (si se usa, deja de ser examen).
- Lectura: OOF 0.3225, examen 0.3490 → sano. Si el examen cae mucho → sobreajuste, fuga o cambio de mundo.

En el evento real, el corte actual probablemente **no** tendrá target (el futuro no ha pasado). Entonces el examen fuera de tiempo se arma con **dos cortes pasados**: entrenar con `corte − 2·horizonte` y examinar con `corte − horizonte`. Pide al DE una tabla `_t2` si hay historia suficiente.

### B2.3 Por bloques de tiempo (pronóstico)
Para series (C14): entrenar con fechas < X y validar con fechas ≥ X. **Nunca** al azar: mezclaría el futuro en el entrenamiento.

### B2.4 Tabla de decisión de validación

| Situación | Validación |
|---|---|
| Hay corte anterior con target | OOF dentro de `_t1` para elegir + examen en el corte actual |
| El banco da una lista a puntuar | OOF en el resto + puntuar la lista |
| Solo una tabla | OOF 5 pliegues estratificados (decirlo como limitación) |
| Pronóstico | bloques de tiempo |
| **Nunca** | elegir variables o modelo mirando el examen |

## B3. Métricas con código y lectura

```python
def gini(y, p):
    return float(2 * roc_auc_score(y, p) - 1) if 0 < y.sum() < len(y) else np.nan

def lift(y, p, top=0.10):
    k = max(int(len(y) * top), 1)
    return float(y[np.argsort(-p)[:k]].mean() / y.mean())

def captura(y, p, top=0.10):
    k = max(int(len(y) * top), 1)
    return float(y[np.argsort(-p)[:k]].sum() / y.sum())

def brier(y, p):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))
```

| Variable | Qué es |
|---|---|
| `y` | 0/1 reales |
| `p` | puntaje del modelo (probabilidad o cualquier número que ordene) |
| `roc_auc_score` | AUC = probabilidad de que un positivo al azar tenga más puntaje que un negativo al azar |
| `0 < y.sum() < len(y)` | protección: si todos son 0 o todos 1, el AUC no existe |
| `top=0.10` | fracción de la base que se mira (el "top 10%") |
| `k` | número de empresas en el top |
| `np.argsort(-p)[:k]` | índices de las k empresas con mayor puntaje (el `-` ordena de mayor a menor) |
| `y[...].mean()` | tasa de positivos dentro del top |
| `y.mean()` | tasa base |

**Tabla de deciles real** (logística, OOF en el corte anterior):

| decil | tasa | p_media | lift | captura acumulada |
|---|---|---|---|---|
| 1 | 39.5% | 41.0% | 2.09 | 20.9% |
| 2 | 26.9% | 28.4% | 1.42 | 35.1% |
| 3 | 23.6% | 23.6% | 1.25 | 47.6% |
| 5 | 18.0% | 17.7% | 0.95 | 68.4% |
| 10 | 7.7% | 7.2% | 0.41 | 100% |

Cómo se lee (todas son lecturas válidas de la misma tabla):
- **Orden:** la tasa baja de forma monótona del decil 1 al 10 → el modelo ordena bien en toda la lista, no solo arriba.
- **Lift:** el 10% de arriba convierte 2.1 veces la base (39.5% vs 18.9%).
- **Captura:** con el 30% de la base se atrapa casi la mitad (47.6%) de los que convierten.
- **Calibración:** `p_media` ≈ `tasa` en cada decil (41.0 vs 39.5; 7.2 vs 7.7) → las probabilidades son creíbles → se pueden multiplicar por montos.
- **Decil 10:** 7.7%, nadie es "imposible": ojo con decir "no llamen a estos"; di "llamar después".

Relación útil: **captura@k = lift@k × k**. Lift 2.09 × 10% = 20.9% ✓.

---

# PARTE C — LOS MODELOS, UNO POR UNO

> Para cada modelo: **intuición → lo mínimo de matemática → cuándo → código con cada variable explicada → cómo leer la salida → errores → cómo explicarlo al jurado.**

## C0. Regla sin modelo (línea base)

**Intuición:** lo que haría un ejecutivo sin modelo: "llamo primero a las empresas que más venden".

```python
def regla(Xtr, ytr, Xva, k=1):
    g = {}
    for v in Xtr.select_dtypes("number").columns:
        x = Xtr[v]
        if x.notna().mean() > 0.5 and x.nunique() > 1:
            g[v] = gini(ytr, x.fillna(x.median()))
    top = sorted(g, key=lambda v: -abs(g[v]))[:k]
    s = np.zeros(len(Xva))
    for v in top:
        x = Xva[v].fillna(Xtr[v].median())
        s += _rank(x if g[v] > 0 else -x)
    return s / len(top)
```

| Variable | Qué es | Por qué |
|---|---|---|
| `Xtr, ytr` | variables y target de entrenamiento | la regla **se elige con train**, no con validación |
| `Xva` | variables a puntuar | — |
| `k` | cuántas variables combina (1 = `regla_1var`, 3 = `regla_top3`) | top3 ≈ "scorecard manual" |
| `x.notna().mean() > 0.5` | exige ≥ 50% de datos | una variable casi vacía no sirve de regla |
| `x.nunique() > 1` | no constante | — |
| `g[v]` | Gini **con signo** de la variable sola | negativo = "más es peor" |
| `fillna(x.median())` | nulos → mediana de **train** | no aprender de validación |
| `top` | las k de mayor \|Gini\| | — |
| `_rank(...)` | percentil 0–1 | sumar variables de escalas distintas (soles + días) |
| `-x` si `g[v] < 0` | invierte la dirección | así todas "suben" con la probabilidad |
| `s / len(top)` | promedio de percentiles | puntaje final 0–1 (**no** es probabilidad) |

**Resultado real:** `regla_1var` Gini 0.263, `regla_top3` 0.288.
**Cómo explicarlo:** "Si ordenáramos solo por ventas, ya tendríamos Gini 0.26. Nuestro modelo llega a 0.32: es 23% mejor que lo que haría un ejecutivo con una sola variable."
**Errores:** presentar el Gini del modelo sin la regla (el jurado no sabe si 0.32 es mucho).

## C1. Regresión logística

### Intuición
Una **balanza**: cada variable empuja hacia "sí" o hacia "no" con un peso. La suma de empujes pasa por una curva en S que la convierte en probabilidad.

### Matemática mínima
- z = b0 + b1·x1 + … + bp·xp (puntaje lineal = log-odds)
- p = 1 / (1 + e^(−z))
- Se entrena minimizando la **log-loss**: −Σ [y·ln p + (1−y)·ln(1−p)] + penalización.
- **Regularización L2** (la de scikit-learn por defecto): suma λ·Σ b². En scikit-learn el parámetro es **C = 1/λ**: C chico = más regularización = coeficientes más pequeños y estables.
- **Odds ratio** = e^b: multiplica las chances (p/(1−p)) cuando la variable sube 1 unidad (aquí, 1 desviación estándar).

### Cuándo
Pocos datos, EPV bajo, señal casi lineal, necesidad de explicar. En la prueba **ganó** (0.3225 vs 0.2986 de LightGBM): la señal sintética es casi lineal.

### Preprocesamiento (lo que la hace funcionar)

La logística mide **distancias**: un monto de S/ 50 M aplasta todo. Por eso:

```python
pasos_num = Pipeline([
    ("winsor", Winsor(0.01, 0.99)),
    ("log", LogSigno()),
    ("imputar", SimpleImputer(strategy="median", add_indicator=True)),
    ("escalar", StandardScaler()),
])
pasos_cat = Pipeline([
    ("imputar", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=0.01, sparse_output=False)),
])
prep = ColumnTransformer([("num", pasos_num, num), ("cat", pasos_cat, cat)], verbose_feature_names_out=False)
modelo = LogisticRegression(C=C, max_iter=3000, class_weight="balanced" if peso else None)
pipe = Pipeline([("prep", prep), ("modelo", modelo)])
```

| Pieza / parámetro | Qué hace | Por qué | Si lo cambias |
|---|---|---|---|
| `Winsor(0.01, 0.99)` | recorta cada variable a sus percentiles 1 y 99 **de train** | extremos no dominan los coeficientes | 0.05/0.95 = más agresivo |
| `LogSigno` | sign(x)·log(1+\|x\|) | montos con cola larga → escala de órdenes de magnitud; respeta 0 y negativos | quitarlo si las variables ya son tasas o conteos chicos |
| `SimpleImputer(median)` | nulo → mediana de train | la logística no acepta nulos | `mean` es sensible a extremos |
| `add_indicator=True` | agrega columna "era nulo" (0/1) | **la ausencia informa** (no tener operaciones ≠ tener 0) | quitarlo pierde esa señal |
| `StandardScaler` | (x − media)/desv | coeficientes comparables entre variables; regularización justa | sin él, C penaliza distinto a cada variable |
| `fill_value="SIN_DATO"` | categoría propia para nulos | — | — |
| `OneHotEncoder` | una columna 0/1 por categoría | la logística necesita números | — |
| `handle_unknown="ignore"` | categoría nueva en el destino → todo 0 | no se cae al puntuar el corte actual | — |
| `min_frequency=0.01` | categorías con < 1% se juntan en "infrequent" | evita coeficientes ruidosos de categorías raras | subir si hay muchas categorías |
| `ColumnTransformer` | aplica cada receta a sus columnas | — | — |
| `num`, `cat` | listas de nombres de columnas numéricas y de texto | las arma `tipos()` | — |
| `C=1.0` | inverso de la regularización | 1 es un buen punto de partida | probar 0.1 y 10 si hay tiempo |
| `max_iter=3000` | iteraciones del optimizador | evitar "ConvergenceWarning" | — |
| `class_weight` | reponderar clases | **no** se usa por defecto: infla probabilidades | — |
| `Pipeline` | encadena preparación + modelo | `fit` aprende **todo** solo con train (sin fuga) | — |

> **Clave anti-fuga:** todo lo que "aprende" (percentiles, medianas, media/desv., categorías) se ajusta dentro de `pipe.fit(Xtr)`. Al hacer OOF, cada pliegue reaprende con su propio train. Por eso usamos `Pipeline` y no preprocesamos la tabla entera antes.

### Leer los coeficientes (salida real)

| variable | coef | odds_ratio | lectura |
|---|---|---|---|
| `operacione__n_total` | +0.566 | 1.76 | +1 desv. en n.º de operaciones previas → chances ×1.76 (+76%) |
| `maestrocli__ventas_anuales` | +0.398 | 1.49 | más ventas → +49% chances por desviación |
| `rubro_economico_CONSTRUCCION` | −0.313 | 0.73 | ser de construcción → −27% chances (comparado con los otros rubros) |
| `rubro_economico_COMERCIO` | +0.300 | 1.35 | comercio → +35% |
| `rubro_pagador_principal_MINERIA` | −0.308 | 0.73 | si su pagador principal es minero → −27% |

Cuidados:
- Son efectos **manteniendo lo demás constante**. Si dos variables están muy correlacionadas, se reparten el efecto y un signo puede salir "raro".
- Las categorías se leen **contra las demás** (one-hot sin columna eliminada + regularización): compara entre categorías, no en absoluto.
- Las numéricas están en log y estandarizadas: "1 desviación" no es "1 sol". Para negocio, usa la tabla de tasas por quintil.

### Errores típicos
| Síntoma | Causa | Arreglo |
|---|---|---|
| `ConvergenceWarning` | escalas enormes o pocas iteraciones | revisar que el Scaler esté; `max_iter` mayor |
| `ValueError: Input contains NaN` | se saltó el imputador | usar el `Pipeline` completo |
| Gini muy bajo vs LightGBM | relación no lineal o interacción | normal; o agregar variables en tramos |
| Coeficiente gigante (±8) | separación casi perfecta → posible fuga | revisar esa variable |

### Cómo explicarlo
"Es una balanza: cada característica suma o resta puntos. Las que más suman son la historia de operaciones y el tamaño de ventas; ser de construcción resta. Lo elegimos porque rindió igual o mejor que modelos más complejos y se puede auditar variable por variable."

## C2. Árbol de decisión (para explicar, no para entregar)

**Intuición:** preguntas sí/no en cascada: "¿ventas > 1 M? → ¿tiene operaciones previas? → …". Cada hoja da una tasa.

```python
from sklearn.tree import DecisionTreeClassifier, export_text
arbol = DecisionTreeClassifier(max_depth=3, min_samples_leaf=200, random_state=42)
arbol.fit(X_num.fillna(-1), y)            # X_num: solo numéricas; -1 = "sin dato"
print(export_text(arbol, feature_names=list(X_num.columns)))
```

| Parámetro | Qué hace |
|---|---|
| `max_depth=3` | máximo 3 preguntas seguidas → legible en una diapositiva |
| `min_samples_leaf=200` | cada hoja con ≥ 200 empresas → tasas confiables |
| `fillna(-1)` | el árbol de scikit-learn no acepta nulos; −1 los separa |

**Uso:** un gráfico para el jurado ("así piensa, en simple") o para descubrir segmentos. **No** suele ganar en Gini: un árbol solo tiene varianza alta.

## C3. Random Forest (bagging)

**Intuición:** cientos de árboles profundos, cada uno con una muestra distinta de filas y columnas; se promedian. Promediar reduce la **varianza**.

```python
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(n_estimators=500, min_samples_leaf=50, max_features="sqrt", n_jobs=-1, random_state=42)
```
| Parámetro | Qué hace |
|---|---|
| `n_estimators` | número de árboles (más = más estable, más lento) |
| `min_samples_leaf` | freno contra memorizar |
| `max_features="sqrt"` | cada corte mira √p columnas al azar → árboles distintos entre sí |

**Por qué no está en el torneo:** en tabulares suele rendir igual o menos que el boosting, es más pesado y no maneja nulos tan bien. Si te preguntan: "lo consideramos; el boosting corrige errores en serie y suele ganar en este tipo de datos".

## C4. LightGBM (gradient boosting)

### Intuición
Árboles **en serie**: el primero predice algo; el segundo aprende **en qué se equivocó** el primero; el tercero corrige al segundo… Cada árbol es pequeño y aporta un poco (`learning_rate`). Al final se suman.

### Matemática mínima
- Empieza con la log-odds de la tasa base.
- En cada ronda calcula el **gradiente** de la log-loss por fila: (p − y). Es "cuánto y hacia dónde me equivoqué".
- Ajusta un árbol a esos gradientes; el valor de cada hoja es la corrección.
- z_nuevo = z_anterior + learning_rate × árbol(x).
- LightGBM crece los árboles **por hoja** (la hoja que más reduce el error), usa **histogramas** (agrupa valores en ~255 tramos → muy rápido) y manda los **nulos** a la rama que más conviene.

### Cuándo
> 5 000 filas, relaciones no lineales, interacciones (plazo largo **y** pagador grande), nulos frecuentes, categorías.

### Código y cada parámetro

```python
LGBM = dict(n_estimators=2000, learning_rate=0.05, num_leaves=31, min_child_samples=50,
            subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
            deterministic=True, force_col_wise=True, n_jobs=-1, verbose=-1)

def fit_lgbm(Xtr, ytr, Xva, params=None, peso=False, submuestra=None, regresion=False, objetivo=None, devolver=False):
    import lightgbm as lgb
    p = {**LGBM, **(params or {}), "random_state": SEMILLA}
    if objetivo:
        p["objective"] = objetivo
    Xt, yt, k = Xtr, ytr, 1
    if submuestra:
        rng = np.random.default_rng(SEMILLA)
        keep = (ytr.values == 1) | (rng.random(len(ytr)) < 1 / submuestra)
        Xt, yt, k = Xtr[keep], ytr[keep], submuestra
    es = np.random.default_rng(SEMILLA + 1).random(len(yt)) < 0.10
    M = lgb.LGBMRegressor(**p) if regresion else lgb.LGBMClassifier(**p, **({"is_unbalance": True} if peso else {}))
    M.fit(Xt[~es], yt[~es], eval_set=[(Xt[es], yt[es])], callbacks=[lgb.early_stopping(100, verbose=False)])
    pred = M.predict(Xva) if regresion else M.predict_proba(Xva)[:, 1]
    if submuestra and not regresion:
        pred = pred / (pred + (1 - pred) * k)
    return (pred, M) if devolver else pred
```

| Parámetro / variable | Valor | Qué hace | Si sobreajusta | Si subajusta |
|---|---|---|---|---|
| `n_estimators` | 2000 | **techo** de árboles; el early stopping decide | — | — |
| `learning_rate` | 0.05 | cuánto aporta cada árbol | bajar (0.02) | subir (0.1) |
| `num_leaves` | 31 | hojas por árbol = complejidad / interacciones | bajar (7–15) | subir (63) |
| `min_child_samples` | 50 | filas mínimas por hoja | **subir** (100–300) | bajar (20) |
| `subsample` + `subsample_freq=1` | 0.8 | cada árbol ve 80% de filas | bajar (0.6) | 1.0 |
| `colsample_bytree` | 0.8 | cada árbol ve 80% de columnas | bajar (0.5) | 1.0 |
| `reg_lambda` | 1.0 | penalización L2 de las hojas | subir (5–20) | bajar |
| `deterministic`, `force_col_wise` | True | mismo resultado en cada corrida | — | — |
| `n_jobs=-1` | todos los núcleos | velocidad | — | — |
| `params` | dict | sobrescribe los de arriba (ej. los de Optuna) | — | — |
| `peso` | False | `is_unbalance`: repondera positivos (C7) | — | — |
| `submuestra` | None o 4 | 1 de cada 4 negativos + corrección (C7) | — | — |
| `regresion` | False | regresor (monto) en vez de clasificador | — | — |
| `objetivo` | None | ej. `"tweedie"` para montos con ceros | — | — |
| `es` | máscara 10% | filas internas para **early stopping** (no son la validación) | — | — |
| `early_stopping(100)` | 100 rondas | para si en 100 árboles seguidos no mejora la log-loss interna | — | — |
| `predict_proba(...)[:, 1]` | — | probabilidad de la clase 1 | — | — |

**Por qué el early stopping usa un 10% interno:** si parara mirando el pliegue de validación, ese pliegue dejaría de ser "no visto" → Gini optimista.

**Categorías:** al venir como `pd.Categorical` (lo hace `tipos()`), LightGBM las trata de forma nativa (agrupa categorías por su efecto). Por eso en `tipos()` se fijan **los mismos niveles** en train y destino: si no, el código interno de "COMERCIO" podría ser 3 en train y 5 en destino → predicciones basura sin error.

### Salida real
`lgbm` Gini OOF 0.2986 vs logística 0.3225. Con Optuna llegó a 0.317 (3 pliegues) y aun así no superó a la logística → señal casi lineal en estos datos. **En los datos reales puede ser al revés**; por eso se mide.

### Cómo explicarlo
"Son cientos de árboles pequeños de preguntas sí/no; cada uno corrige los errores del anterior. Captura combinaciones que una balanza no ve, por ejemplo que el plazo largo importa más cuando el pagador es grande."

## C5. XGBoost

Mismo principio que LightGBM, con árboles que crecen **por niveles** y regularización en el objetivo. Suele empatar con LightGBM. Inclúyelo como referencia si está instalado (la plantilla ya lo hace en modo completo):

```python
import xgboost as xgb
m = xgb.XGBClassifier(n_estimators=2000, learning_rate=0.05, max_depth=6, min_child_weight=5,
                      subsample=0.8, colsample_bytree=0.8, tree_method="hist", enable_categorical=True,
                      early_stopping_rounds=100, eval_metric="logloss", random_state=42)
```
`max_depth` (profundidad) reemplaza a `num_leaves`; `min_child_weight` cumple el papel de `min_child_samples`; `tree_method="hist"` = histogramas como LightGBM.

## C6. CatBoost

Boosting con árboles **simétricos** (la misma pregunta en todo un nivel → más estables) y **codificación ordenada** de categorías: cada fila se codifica con la tasa de las filas "anteriores" en una permutación aleatoria → target encoding **sin fuga**.

**Cuándo:** categorías de alta cardinalidad (CIIU de 4 dígitos, distrito, RUC del pagador). Más lento.
```python
from catboost import CatBoostClassifier
m = CatBoostClassifier(iterations=2000, learning_rate=0.05, depth=6, l2_leaf_reg=3,
                       early_stopping_rounds=100, verbose=False, random_seed=42)
m.fit(Xtr, ytr, cat_features=cat, eval_set=(Xes, yes))      # cat: lista de columnas de texto (sin nulos: "NA")
```

## C7. Desbalance: pesos vs submuestreo con corrección de prior

| Técnica | Qué hace | Efecto en el Gini | Efecto en la probabilidad | Usar cuando |
|---|---|---|---|---|
| Nada | — | — | real | **por defecto** |
| Pesos (`is_unbalance`, `class_weight="balanced"`) | cada positivo "vale" más | igual o **peor** (medido) | **inflada** | métrica con umbral (F1, recall) |
| Submuestreo + corrección | se quedan 1 de cada k negativos; luego se corrige | ≈ igual | real (tras corregir) | datos enormes (velocidad) |
| SMOTE | crea positivos sintéticos | — | distorsionada | **no** usar |

**Corrección de prior** (por qué funciona): al quedarte con 1 de cada k negativos, las odds aparentes se multiplican por k. Para volver: odds_real = odds_modelo / k →

```python
pred = pred / (pred + (1 - pred) * k)
```
| Variable | Qué es |
|---|---|
| `pred` | probabilidad del modelo entrenado con negativos submuestreados |
| `k` | factor de submuestreo (4 = se quedó 1 de cada 4 negativos) |

Ejemplo: k = 4, pred = 0.40 → 0.40 / (0.40 + 0.60·4) = 0.143.

**Medido hoy:**

| modelo | Gini | prob media | tasa real |
|---|---|---|---|
| lgbm | 0.2986 | 0.189 | 0.189 |
| lgbm_pesos | **0.2207** | **0.210** (inflada) | 0.189 |
| lgbm_submuestra | 0.2903 | 0.186 (corregida) | 0.189 |

Frase: "Probamos reponderar: bajó el Gini y distorsionó las probabilidades. No lo usamos."

## C8. Ensamble de rangos

```python
P["ensamble"] = (_rank(P["logistica"]) + _rank(P["lgbm"])) / 2
```
- Promedia **percentiles**, no probabilidades (las escalas pueden diferir).
- Gana cuando los modelos se equivocan en empresas distintas.
- El resultado **no es probabilidad** → si se elige, calibrar (C9).
- Medido: 0.3173 (< logística 0.3225) → no se elige. Es el resultado típico cuando un modelo es claramente mejor.

## C9. Calibración

**Problema:** el modelo puede ordenar bien y aun así decir "40%" a empresas que convierten 30%. Si después multiplicas por montos, el valor esperado sale inflado.

```python
from sklearn.isotonic import IsotonicRegression
cal = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p_oof, y)
prob = cal.predict(p_final)
```
| Variable | Qué es |
|---|---|
| `p_oof` | predicciones OOF del modelo elegido (nunca del examen) |
| `y` | target de train |
| `IsotonicRegression` | aprende una función **creciente** puntaje → tasa real (por tramos) |
| `out_of_bounds="clip"` | puntajes fuera del rango visto se recortan |
| `p_final` | puntajes del modelo final sobre el destino |

- **Isotónica:** flexible, necesita bastantes datos (miles). **Platt** (una logística sobre el puntaje) si hay pocos.
- Cómo verificar: tabla de deciles → `p_media` vs `tasa`.
- En la prueba la logística ya estaba calibrada (Brier 0.1449 vs 0.1534 sin modelo). El script calibra automáticamente solo si el elegido es regla o ensamble.

## C10. Monto: dos partes, Duan y Tweedie

### Por qué no una regresión simple
`target_monto`: 80% ceros, máximo S/ 1.3 M, media S/ 11 k. Una regresión normal aprende "casi cero para todos" y los gigantes dominan el error.

### Dos partes
**E[monto] = P(monto > 0) × E[monto | monto > 0]**

```python
def monto_dos_partes(Xtr, mtr, Xdest, params=None):
    pos = (mtr > 0).values
    Xp, lp = Xtr[pos], np.log1p(mtr[pos])
    folds = pliegues((lp > lp.median()).astype(int).reset_index(drop=True))
    Xp, lp = Xp.reset_index(drop=True), lp.reset_index(drop=True)
    pred_oof = oof(lambda a, b, c: fit_lgbm(a, b, c, params=params, regresion=True), Xp, lp, folds)
    duan = float(np.mean(np.exp(lp - pred_oof)))
    _, M = fit_lgbm(Xp, lp, Xp.iloc[:5], params=params, regresion=True, devolver=True)
    return np.expm1(M.predict(Xdest)) * duan, duan, r2_log
```

| Variable | Qué es | Por qué |
|---|---|---|
| `mtr` | monto real en la ventana | — |
| `pos` | máscara de quienes convirtieron | la parte 2 solo aprende de ellos |
| `lp = log1p(monto)` | log(1 + monto) | comprime la cola larga; el modelo aprende órdenes de magnitud |
| `folds` | pliegues estratificados por "monto sobre/bajo la mediana" | cada pliegue con grandes y chicos |
| `pred_oof` | predicción en log, fuera de pliegue | para medir y para Duan sin fuga |
| `duan` | promedio de e^(residuo) | corrige que e^(media del log) < media real |
| `M` | modelo final con todos los convertidos | se aplica a **todas** las empresas del destino |
| `np.expm1(...) * duan` | vuelve a soles y corrige | `monto_si_convierte` |

**Factor de Duan (medido: 1.33):** sin él, subestimas el monto ~25%. Por qué: el promedio de los logaritmos es el log de la **media geométrica**, que siempre es ≤ la media aritmética.

**Lectura real:** R² condicional en log 0.46 → hay señal en el **tamaño** (quién hace operaciones grandes). Si saliera ≈ 0, el monto solo aportaría su promedio y bastaría la mediana por rubro × tamaño.

### Tweedie (alternativa en un solo modelo)
```python
fit_lgbm(X, monto, Xva, regresion=True, objetivo="tweedie", params=dict(tweedie_variance_power=1.5))
```
- Distribución con masa en 0 y cola larga. `tweedie_variance_power` entre 1 (Poisson) y 2 (Gamma); 1.5 es el punto medio estándar.

**Medido hoy (OOF honesto):** R² en soles dos partes 0.118 vs Tweedie 0.125; Spearman 0.236 vs 0.232 → **empate**. Se elige dos partes por explicabilidad ("¿convierte?" y "¿cuánto?" por separado).

> ⚠ Error que cometí y corregí al probar: medir la parte 2 con el modelo entrenado sobre los mismos convertidos da R² 0.200 (optimista). Para quienes convirtieron hay que usar la predicción **OOF**. Si un número de monto "se ve muy bien", revisa esto.

## C11. ¿Uno o varios modelos?

**Pregunta:** ¿conviene un modelo por segmento (con lead / sin lead, cliente / no cliente, MIPE / grande)?

```python
glob = oof(fit_lgbm, X, y, folds)                 # global: todos, con el segmento como variable
for g in segmentos:
    m = (s == g).to_numpy(dtype=bool)             # filas del segmento
    gini_global = gini(y[m], glob[m])             # el global medido SOLO dentro del segmento
    gini_propio = gini(yg, oof(fit_lgbm, Xg, yg, pliegues(yg)))   # modelo entrenado solo con el segmento
```

**Salida real** (segmento = `flag_lead_factoring`):

| segmento | n | positivos | log global | log propio | lgbm global | lgbm propio |
|---|---|---|---|---|---|---|
| 0 | 17 501 | 3 298 | 0.318 | 0.319 | 0.290 | 0.307 |
| 1 | 2 499 | 487 | **0.348** | 0.297 | 0.339 | 0.304 |

Lectura: en el segmento chico (lead = 1) el modelo propio **pierde** 0.05: con 487 positivos no alcanza para aprender solo; el global aprovecha lo que comparte con el resto. En el segmento grande, empate. → **1 modelo global**.

Reglas:
- Separar solo si: (a) cada segmento tiene ≥ ~200 positivos, (b) el propio gana por > 0.005 **dentro** del segmento, (c) idealmente alguna variable cambia de signo entre segmentos.
- Separar ayuda sobre todo a la **logística** (no puede representar interacciones); LightGBM global ya aprende la interacción solo (experimento A de la plantilla: logística 0.15 → 0.63 al separar; LightGBM sin cambio).
- "Varios modelos" también puede ser **varias preguntas**: P(convierte) + E[monto] = 2 modelos; P por canal = 1 por canal.

## C12. Optuna (hiperparámetros)

```python
def objetivo(trial):
    params = dict(
        learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        num_leaves=trial.suggest_int("num_leaves", 7, 127, log=True),
        min_child_samples=trial.suggest_int("min_child_samples", 10, 300, log=True),
        subsample=trial.suggest_float("subsample", 0.5, 1.0),
        colsample_bytree=trial.suggest_float("colsample_bytree", 0.3, 1.0),
        reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 30, log=True))
    return gini(y, oof(fit_lgbm, X, y, folds, params=params))

est = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
est.enqueue_trial(dict(learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8,
                       colsample_bytree=0.8, reg_lambda=1.0))
est.optimize(objetivo, n_trials=60, timeout=segundos)
```

| Pieza | Qué es |
|---|---|
| `trial` | una prueba: Optuna le propone valores |
| `suggest_float(..., log=True)` | busca en escala logarítmica (0.01 y 0.1 igual de probables): correcto para tasas y penalizaciones |
| `suggest_int` | enteros (hojas, filas por hoja) |
| `folds` (k=3) | 3 pliegues: más pruebas en el mismo tiempo |
| `TPESampler` | búsqueda **bayesiana**: aprende de las pruebas anteriores dónde buscar |
| `enqueue_trial(default)` | la prueba 0 es la configuración por defecto → se ve cuánto se ganó |
| `n_trials`, `timeout` | se detiene por número de pruebas o por segundos (lo que ocurra primero) |
| `get_param_importances` | qué perilla explicó más la variación del Gini (fANOVA) |

**Salida real (60 s):**
```
40 pruebas · default 0.2884 -> mejor 0.3174 (+0.0290)
importancia de perillas: min_child_samples 0.36, colsample_bytree 0.26, num_leaves 0.25, learning_rate 0.06
mejores: num_leaves 7, min_child_samples 11, learning_rate 0.037, colsample 0.53
```
Lectura: el mejor LightGBM es **muy simple** (7 hojas) → otra señal de que la relación es casi lineal y la logística es la elección correcta. +0.029 en 3 pliegues, pero 0.317 sigue < 0.3225 de la logística en 5 pliegues → no cambia la decisión.

Reglas: Optuna **al final**; siempre revalidar los mejores parámetros con los 5 pliegues del torneo antes de usarlos; con 30–40 pruebas, el ranking de perillas no es estable.

## C13. K-means (perfiles descriptivos)

```python
Z = tr[cols].fillna(tr[cols].median())
Z = np.sign(Z) * np.log1p(np.abs(Z))
Z = StandardScaler().fit_transform(Z)
lab = KMeans(k, n_init=10, random_state=42).fit_predict(Z)
```
| Pieza | Por qué |
|---|---|
| `cols` | ≤ 8 numéricas con ≥ 80% de datos: perfiles legibles |
| log | sin él, la variable en soles decide sola los grupos |
| `StandardScaler` | K-means usa distancias: todas en la misma escala |
| `n_init=10` | 10 arranques distintos; se queda con el mejor (K-means depende del inicio) |
| silueta | qué tan separados están los grupos (−1 a 1). Elegir k con silueta alta **y** contable |

**Salida real:** silueta k=2 0.273, k=3 0.290, **k=4 0.293**, k=5 0.259 → k = 4:

| grupo | ventas (mediana) | facturas 12m | share top contraparte | n | conversión |
|---|---|---|---|---|---|
| 2 | S/ 2.7 M | 17 | 0.24 | 3 914 | **30%** |
| 0 | S/ 479 k | 7 | 0.42 | 4 200 | 23% |
| 1 | S/ 286 k | 6 | 0.44 | 10 958 | 14% |
| 3 | S/ 164 k | 2 | 0.72 | 928 | 13% |

Historia: "Medianas diversificadas" (grupo 2) convierten 30%; "micro dependientes de un cliente" (grupo 3) 13%. Es **descriptivo**: sirve para la presentación, no reemplaza al modelo.

## C14. Series de tiempo (si el caso es de pronóstico)

Probado con datos sintéticos (agencia × día):

```python
df = df.sort_values(["agencia", "fecha"])
g = df.groupby("agencia")["y"]
for L in (1, 7, 14, 28):
    df[f"lag_{L}"] = g.shift(L)
df["media_7"] = g.transform(lambda s: s.shift(1).rolling(7).mean())
df["dow"] = df.fecha.dt.dayofweek
df["mes"] = df.fecha.dt.month
df = df.dropna()
corte = pd.Timestamp("2025-05-01")
tr, va = df[df.fecha < corte], df[df.fecha >= corte]
m = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, verbose=-1).fit(tr[vs], tr.y)
pred = m.predict(va[vs]); ingenuo = va["lag_7"]
```
| Pieza | Qué es | Cuidado |
|---|---|---|
| `shift(L)` dentro de cada agencia | valor de hace L días | **L debe ser ≥ horizonte**: si pronosticas a 7 días, `lag_1` no existe ese día → fuga |
| `shift(1).rolling(7)` | media de los 7 días anteriores | sin `shift(1)` incluirías el día a predecir |
| `dow`, `mes` | estacionalidad | agregar feriados si hay |
| `corte` | validación por **bloque** | nunca al azar |
| `ingenuo = lag_7` | línea base "igual que la semana pasada" | el modelo debe ganarle |

Resultado: MAE modelo 4.72 vs ingenuo 5.65 → 16% mejor. Métricas: MAE (en unidades), MAPE (%), y en negocio el **costo** (efectivo ocioso vs quedarse sin efectivo).

## C15. Optimización de la lista (el "modelo de decisión")

El modelo da probabilidades; la decisión necesita una **lista**. Dos métodos (detalle en la guía de Liz):
- **Voraz:** ordenar por valor esperado y llenar cupos por zona → óptimo con **una** restricción por grupo.
- **Programación entera (PuLP + HiGHS):** maximizar Σ valor·x sujeto a Σx ≤ capacidad, cupos por zona, mínimo de pymes… → cuando las restricciones **se cruzan**.

```python
import pulp
prob = pulp.LpProblem("priorizar", pulp.LpMaximize)
x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in cand.index}     # 1 = la contacto
prob += pulp.lpSum(x[i] * cand.at[i, "valor_esperado"] for i in cand.index)   # objetivo
prob += pulp.lpSum(x.values()) <= N                                          # capacidad
for z, cupo in cupos.items():
    prob += pulp.lpSum(x[i] for i in cand.index if cand.at[i, "zona"] == z) <= cupo
prob += pulp.lpSum(x[i] * cand.at[i, "es_pyme"] for i in cand.index) >= 0.6 * N   # política
prob.solve(pulp.HiGHS(msg=False))
```
Lo que aporta Sophia aquí: que el `valor_esperado` use **probabilidades calibradas**.

---

# PARTE D — DIAGNÓSTICO Y DECISIÓN

## D1. Fugas (lo que más hace perder concursos)

**Definición:** una variable que contiene información que **no existía el día de decidir**. El modelo "adivina" en la validación y fracasa en la evaluación real del banco.

### Cómo se ven
| Señal | Ejemplo |
|---|---|
| Gini individual > 0.5 | `total_operaciones_hist` 0.65 (cuenta operaciones de la ventana del target) |
| Gini bajo en el corte anterior, alto en el actual | `ops_ultimo_semestre` 0.16 → 0.91 (tabla "foto" tomada hoy) |
| Gini del modelo > 0.8 en propensión comercial | casi siempre fuga |
| Permutación altísima de una variable | el modelo depende solo de ella |
| Nombre sospechoso | `estado_actual`, `fecha_cancelacion`, `resultado`, `desembolso`, `ultimo_*`, `flag_*_activo` |
| Examen fuera de tiempo ≪ OOF | aprendió algo que no se repite |

### Las 5 familias de fuga en este caso
1. **Ventana:** la variable se calculó con fechas ≥ corte (conteos "históricos" sin filtro de fecha).
2. **Tabla foto:** perfiles sin fecha, extraídos hoy (saldo actual, productos actuales, estado actual).
3. **Definición:** la variable es casi el target (ej. "tiene línea de factoring aprobada").
4. **Agregados con el target:** target encoding hecho con toda la tabla (no fuera de muestra).
5. **Duplicados entre train y validación:** la misma empresa dos veces (grano roto).

### Protocolo (5 min por variable)
1. ¿Qué significa la columna? (`diccionario_variables.csv`, mentor)
2. ¿Tiene fecha? ¿Es anterior al corte?
3. ¿Su Gini cambia mucho entre cortes?
4. Sacarla y volver a medir: si el Gini cae de 0.9 a 0.3, era la fuga.
5. Anotar en `notas_modelo.md` y en `DECISIONES_MANUAL` (DROP).

**Frase de defensa:** "Detectamos dos variables que el banco no habría tenido el día de decidir y las excluimos aunque subían el Gini a 0.65. Preferimos un modelo honesto."

## D2. Elegir el modelo

### La regla
```python
def elegir(tabla, tolerancia=0.005):
    mejor = tabla.gini.max()
    ok = tabla[tabla.gini >= mejor - tolerancia].copy()
    ok["orden"] = ok.modelo.map({m: i for i, m in enumerate(SIMPLICIDAD)})
    return ok.sort_values("orden").modelo.iloc[0]
```
| Variable | Qué es |
|---|---|
| `tabla` | una fila por modelo con su Gini OOF |
| `tolerancia` | 0.005: diferencia que consideramos "empate práctico" |
| `ok` | modelos a ≤ 0.005 del mejor |
| `SIMPLICIDAD` | orden regla_1var < regla_top3 < logística < lgbm < … < ensamble |
| retorno | el **más simple** de los empatados |

**Por qué parsimonia:** se explica mejor, se rompe menos ante cambios, el jurado lo entiende y el riesgo de sobreajuste es menor.

### ¿La diferencia es real? (bootstrap)
Medido hoy (B = 100):
```
regla_1var  0.2629 [0.2448, 0.2828]
logistica   0.3224 [0.3063, 0.3405]
lgbm        0.2962 [0.2817, 0.3149]
logistica − regla: [+0.0453, +0.0745]  -> gana de verdad
lgbm − logística:  [−0.0349, −0.0188]  -> diferencia real (a favor de la logística)
```
Regla práctica: con < 500 positivos, diferencias < 0.02 suelen ser ruido.

### Tabla de decisión final
| Situación | Elección |
|---|---|
| Un modelo gana por > 0.005 y el examen lo confirma | ese |
| Empate (≤ 0.005) | el más simple |
| LightGBM gana en OOF pero pierde en el examen | el que gane en el examen (y revisar fugas/PSI) |
| Ningún modelo gana a la regla de forma significativa | **la regla** (y decirlo con orgullo) |
| Ensamble gana | ensamble + calibración isotónica |
| Gana por segmento | modelos por segmento (C11) |

## D3. Importancia y explicación

| Medida | Pregunta | Fuerte en | Débil en |
|---|---|---|---|
| Coeficiente / OR (logística) | dirección y tamaño del efecto | explicación exacta | colinealidad reparte el efecto |
| gain (árboles) | ¿cuánto la usó al entrenar? | rápido | premia variables con muchos valores |
| **permutación** | ¿cuánto cae el Gini en datos no vistos si la desordeno? | la más honesta | variables correlacionadas se reparten el crédito |
| SHAP | aporte de cada variable a **cada** predicción | explicar una empresa; dirección | costo (LightGBM lo da nativo) |

**Salida real (LightGBM de referencia, pliegue de validación):**

| variable | gain | permutación | SHAP | dirección | lectura |
|---|---|---|---|---|---|
| ventas_anuales | 0.088 | **0.094** | 0.279 | +0.95 | la más importante, más ventas → más prob |
| rubro_economico | 0.051 | 0.028 | 0.207 | (cat.) | importa el rubro |
| monto_financiado_total | 0.069 | 0.017 | 0.108 | +0.84 | historia de factoring |
| saldo_ultimo | 0.040 | **0.000** | 0.058 | +0.68 | el modelo la usa, pero otra dice lo mismo |
| var_buro_07 | 0.050 | −0.007 | 0.042 | +0.10 | gain alto, permutación negativa → ruido |

Lección: **gain alto ≠ importante**. `var_buro_07` tiene más gain que `saldo_tend` y permutación negativa (desordenarla no empeora nada).

**Explicar una empresa** (SHAP o aporte lineal): "su probabilidad es 72% (base 19%): suma por ventas altas y operaciones previas; resta un poco porque su principal pagador es minero".

> Explica **el modelo que entregas**. Si entregas la logística, muestra coeficientes; el SHAP de LightGBM sirve como "segunda opinión" de qué variables importan.

## D4. Tablero "si ves X → haces Y"

| Si ves… | Probable causa | Haces |
|---|---|---|
| Gini > 0.8 | fuga | D1 |
| Gini < 0.05 | target mal definido, variables vacías, fechas mal | revisar tasa, top5, corte |
| Regla ≈ modelo | señal concentrada en 1 variable | presentar la regla + modelo como confirmación |
| Logística ≫ LightGBM | pocos datos o señal lineal; o LightGBM sobreajusta | subir `min_child_samples`, bajar hojas; elegir logística |
| LightGBM ≫ logística | interacciones / no linealidad | elegir LightGBM; explicar con SHAP |
| OOF ≫ examen (> 0.05) | sobreajuste, fuga, cambio de mundo | PSI, fugas, simplificar |
| examen > OOF | normal en rangos chicos; más historia en el corte actual | seguir |
| `lgbm_pesos` < `lgbm` | esperado | no reponderar |
| prob media ≠ tasa real | modelo no calibrado (pesos, ensamble, regla) | C9 |
| deciles no monótonos | modelo inestable o pocos datos | modelo más simple |
| Variable top con dirección contraria a la intuición | colinealidad, fuga o hallazgo | revisar tabla por quintiles; si es real → **hallazgo inesperado** |
| Una categoría nueva en el destino | categorías distintas entre cortes | `handle_unknown="ignore"` / niveles fijos (ya lo hace el código) |
| Optuna +0.03 en 3 pliegues | optimismo de búsqueda | revalidar en 5 pliegues |
| Gini por segmento muy bajo en un grupo | el modelo no sirve para ese grupo | regla propia o modelo propio si hay datos |
| Resultados distintos entre laptops | versiones de librerías | correr el final en una sola laptop |

## D5. Errores de modelado más comunes (y arreglos)

| # | Error | Consecuencia | Arreglo |
|---|---|---|---|
| 1 | Preprocesar (escalar, imputar, target encoding) con toda la tabla antes de validar | Gini optimista | `Pipeline` dentro de cada pliegue |
| 2 | Validación aleatoria cuando la evaluación es un periodo futuro | Gini que se cae | fuera de tiempo |
| 3 | Elegir variables mirando el examen | examen deja de ser ciego | elegir solo con train |
| 4 | Comparar modelos con pliegues distintos | comparación injusta | mismos `folds` para todos |
| 5 | Reportar accuracy | 98% "falso" | Gini, lift, captura |
| 6 | Reponderar y luego multiplicar por monto | valor esperado inflado | sin pesos o calibrar |
| 7 | Volver de log sin Duan | montos subestimados ~25% | × Duan |
| 8 | Ids con `.0` o sin ceros a la izquierda | no cruzan con el submission | `astype(str)`, nunca Excel |
| 9 | Categorías con niveles distintos entre train y destino | predicciones basura sin error | niveles fijos (`tipos()`) |
| 10 | Afinar antes de tener un submission | horas perdidas | Optuna al final |
| 11 | Cambiar de modelo a última hora | riesgo sin beneficio | congelar a las 09:00 |
| 12 | Explicar un modelo distinto al entregado | contradicción ante el jurado | explicar el entregado |
| 13 | Sacar conclusiones de segmentos con 20 empresas | ruido presentado como hallazgo | ≥ 100 empresas y ≥ 30 positivos |
| 14 | Medir el monto con el modelo entrenado sobre los mismos datos | R² optimista (0.20 vs 0.12) | OOF |
| 15 | Usar rezagos más cortos que el horizonte (series) | fuga temporal | lag ≥ horizonte |

---

# PARTE E — DEFENSA Y APOYO

## E1. Frases listas (rellena con tus números)

- **Base:** "Una regla simple (ordenar por ventas) da Gini 0.26; nuestro modelo da 0.32 (+23%), y el bootstrap confirma que la mejora no es azar."
- **Validación:** "Entrenamos con lo que se sabía en enero y probamos con lo que pasó desde julio: Gini 0.32 en entrenamiento y 0.35 en el periodo nuevo. El modelo no se cae con el tiempo."
- **Elección:** "Comparamos siete modelos con la misma validación. La logística empató o ganó a los modelos complejos, así que la elegimos por ser auditable."
- **Lift:** "El 10% de empresas con mayor puntaje convierte 39.5%, el doble de la base."
- **Fuga:** "Excluimos dos variables que contenían información posterior a la fecha de decisión."
- **Monto:** "Separamos '¿contratará?' de '¿cuánto?'; el monto se modela en logaritmo y se corrige el sesgo al volver a soles."
- **Desbalance:** "Probamos reponderar las clases: empeoró el Gini y distorsionó las probabilidades; no lo usamos."
- **Calibración:** "Cuando el modelo dice 40%, las empresas convierten 39.5%: podemos usar sus probabilidades para proyectar soles."

## E2. Preguntas técnicas probables (respuesta en ≤ 30 s)

| Pregunta | Respuesta |
|---|---|
| ¿Qué es el Gini? | "2·AUC − 1: mide qué tan bien ordena. 0 es azar, 1 perfecto. Es la métrica estándar de scoring en banca." |
| ¿Por qué no accuracy? | "Con 19% de positivos, decir 'nadie convierte' da 81% de accuracy y no sirve para elegir a quién llamar." |
| ¿Cómo evitaron sobreajuste? | "Validación cruzada fuera de pliegue, early stopping con datos internos, regularización y examen en un periodo posterior." |
| ¿Por qué 5 pliegues estratificados? | "Usa todas las filas para medir y cada pliegue mantiene la tasa de positivos." |
| ¿Qué es OOF? | "Cada empresa se predice con un modelo que no la vio. Así comparamos modelos de forma justa." |
| ¿Por qué no redes neuronales? | "En datos tabulares de este tamaño los árboles con boosting suelen igualarlas o superarlas y son más explicables." |
| ¿Qué hiperparámetros importan? | "min_child_samples, columnas por árbol y número de hojas, según Optuna. Afinar dio poco; las variables pesan más." |
| ¿Qué es SHAP? | "Reparte la predicción de cada empresa entre sus variables; la suma da exactamente la predicción." |
| ¿Cómo interpretan un odds ratio? | "1.76 significa que, al subir una desviación la variable, las chances de convertir se multiplican por 1.76." |
| ¿Qué es el factor de Duan? | "Al volver de logaritmo a soles se subestima la media; Duan la corrige multiplicando por el promedio de los residuos exponenciados (1.33 aquí)." |
| ¿Por qué dos partes y no Tweedie? | "Empataron; dos partes separa probabilidad y tamaño, más fácil de explicar y de usar." |
| ¿Uno o varios modelos? | "Lo medimos: el modelo por segmento perdió 0.05 de Gini en el segmento chico; un global con el segmento como variable fue mejor." |
| ¿Qué pasa si cambian los datos? | "Monitoreamos el PSI; si una variable pasa 0.25 o el Gini cae, se reentrena." |
| ¿Es reproducible? | "Semillas fijas y LightGBM determinista; lo reimplementamos de forma independiente y dio el mismo Gini." |
| ¿Qué limitaciones tiene? | "Parte de los datos es sintética; solo observamos a quien fue contactado (sesgo de selección); empresas sin historia tienen menos señal." |

## E3. Copilot para modelos (sin pegar datos)

Abre el archivo relevante en VS Code antes de preguntar y anota cada uso en `docs/USO_DE_IA.md`.

| Momento | Prompt |
|---|---|
| Al leer el caso | "Con este resumen del objetivo [en tus palabras, sin datos], ¿cuál es la unidad, el target, el horizonte y qué tipo de modelo corresponde?" |
| Frase-modelo | "Revisa esta frase-modelo y dime si hay ambigüedad en target, corte o población: [frase]." |
| Validación | "En `sophia_modelos.py`, ¿por qué `oof()` evita sobreestimar el Gini? ¿Qué pasaría si escalara toda la tabla antes?" |
| Fuga | "Una variable tiene Gini 0.16 en el corte anterior y 0.91 en el actual. ¿Qué tipos de fuga explican eso?" |
| Logística | "Explícame cada paso de `pipeline_logistica` y qué pasaría si quito `add_indicator=True`." |
| LightGBM | "Mi LightGBM tiene Gini OOF 0.40 y 0.29 fuera de tiempo. ¿Qué hiperparámetros de `LGBM` ajusto primero y por qué?" |
| Desbalance | "¿Por qué `pred / (pred + (1 - pred) * k)` corrige la probabilidad después de submuestrear negativos?" |
| Monto | "Explica el factor de Duan en `monto_dos_partes` con un ejemplo numérico." |
| Segmentos | "Tengo esta tabla de Gini global vs propio por segmento: [solo números]. ¿Uso uno o varios modelos?" |
| Optuna | "Optuna ganó +0.03 con 3 pliegues pero no en 5. ¿Por qué pasa y qué reporto?" |
| Error | "Me sale este traceback en `fit_logistica`: [traceback sin datos]. ¿Qué lo causa?" |
| Defensa | "Hazme 10 preguntas difíciles sobre validación fuera de tiempo y fugas en un modelo de propensión bancaria." |
| Nuevo caso | "Si el problema fuera pronosticar efectivo por agencia y día, ¿cómo adapto `sophia_modelos.py`? Usa la sección C14 de la guía." |

## E4. Tarjeta de bolsillo

```
FICHA:     unidad · target · horizonte · corte · población · métrica · decisión   (C0 a los 40 min)
FRASE:     "Para cada __ de __, con lo sabido al __, estimamos __ en __, medido con __, para decidir __."
VALIDAR:   OOF 5 pliegues estratificados dentro del corte anterior + examen en el corte actual
TORNEO:    regla_1var → regla_top3 → logística → lgbm (+pesos, +submuestra) → ensamble
ELEGIR:    mayor Gini; si uno más simple está a ≤ 0.005 → el simple; bootstrap si hay duda
FUGA:      Gini individual > 0.5, o bajo en t1 y alto en t0 → ¿existía el día de decidir?
DESBALANCE: no reponderar (baja Gini, infla prob) · submuestreo SOLO con corrección de prior
MONTO:     dos partes (log + Duan) vs Tweedie · OOF para medir
CALIBRAR:  p_media ≈ tasa por decil; si no → isotónica sobre OOF
SEGMENTOS: separar solo si ≥ 200 positivos y gana > 0.005 dentro del segmento
OPTUNA:    al final, con tiempo límite, revalidar en 5 pliegues
CONGELAR:  09:00 sáb · explicar EL modelo entregado
HORAS:     C0 16:10 · C3 19:00 · C4 22:00 (submission) · C5 01:30 · C7 09:00
```

---

# ANEXO — Código completo (probado el 13/11 con los datos de prueba)

Guárdalos en `trabajo/` con estos nombres exactos (`sophia_extras.py` importa a `sophia_modelos.py`).

## `trabajo/sophia_modelos.py`

```python
"""
TORNEO DE MODELOS DE SOPHIA (independiente de la plantilla: solo pandas, numpy, scikit-learn, lightgbm).

Entrada : una tabla con UNA fila por entidad (empresa), columnas de variables, `target` (0/1)
          y opcionalmente `target_monto` (soles en la ventana del target).
Salida  : comparacion.csv, importancia.csv, predicciones.csv (en --salida)

Uso típico (desde la raíz del repo del evento):
    python trabajo/sophia_modelos.py --tabla ~/datafest_trabajo/salidas/tabla_modelo_t1.parquet \
        --destino ~/datafest_trabajo/salidas/tabla_modelo.parquet \
        --seleccion ~/datafest_trabajo/salidas/seleccion_variables.csv --salida ~/datafest_trabajo/sophia
    (sin --destino: solo validación cruzada sobre --tabla)
"""
import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")
sys.dont_write_bytecode = True

SEMILLA = 42                     # misma semilla = mismos pliegues = mismos números en cada corrida
META = {"id", "target", "target_monto", "fecha_corte", "split"}   # columnas que NUNCA son variables


# =============================================================================================
# 1. MÉTRICAS
# =============================================================================================
def gini(y, p):
    """Gini = 2·AUC − 1. y: 0/1 reales; p: puntaje (cualquier escala, solo importa el ORDEN)."""
    y = np.asarray(y)
    return float(2 * roc_auc_score(y, p) - 1) if 0 < y.sum() < len(y) else np.nan


def lift(y, p, top=0.10):
    """Tasa de positivos en el top `top` (fracción) dividida entre la tasa de toda la base."""
    y, p = np.asarray(y), np.asarray(p)
    k = max(int(len(y) * top), 1)                 # k = cuántas empresas hay en el top
    return float(y[np.argsort(-p)[:k]].mean() / y.mean())


def captura(y, p, top=0.10):
    """% de TODOS los positivos que quedan dentro del top."""
    y, p = np.asarray(y), np.asarray(p)
    k = max(int(len(y) * top), 1)
    return float(y[np.argsort(-p)[:k]].sum() / y.sum())


def brier(y, p):
    """Error cuadrático medio de la probabilidad. Solo tiene sentido si p ES probabilidad."""
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def resumen(y, p, es_prob=True):
    return dict(gini=gini(y, p), auc_pr=float(average_precision_score(y, p)), lift_d1=lift(y, p),
                captura_10=captura(y, p), brier=brier(y, p) if es_prob else np.nan,
                prob_media=float(np.mean(p)) if es_prob else np.nan, tasa_real=float(np.mean(y)))


def deciles(y, p):
    d = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    d["decil"] = 10 - pd.qcut(d.p.rank(method="first"), 10, labels=False)   # 1 = mejor decil
    t = d.groupby("decil").agg(n=("y", "size"), positivos=("y", "sum"), tasa=("y", "mean"), p_media=("p", "mean"))
    t["lift"] = t.tasa / d.y.mean()
    t["captura_acum"] = t.positivos.cumsum() / d.y.sum()
    return t.reset_index()


# =============================================================================================
# 2. DATOS Y VALIDACIÓN
# =============================================================================================
def cargar(ruta, seleccion=None):
    df = pd.read_parquet(ruta)
    df = df.sort_values("id", kind="stable").reset_index(drop=True) if "id" in df else df   # orden fijo
    vs = [c for c in df.columns if c not in META]
    if seleccion and Path(seleccion).exists():                  # usar solo las que pasaron el embudo
        s = pd.read_csv(seleccion)
        vs = [v for v in s.loc[s.decision == "QUEDA", "variable"] if v in df.columns]
    return df, vs


def tipos(train, otros, vs):
    """num = numéricas; cat = texto. Las categóricas reciben LOS MISMOS niveles en train y destino."""
    num = [v for v in vs if pd.api.types.is_numeric_dtype(train[v])]
    cat = [v for v in vs if v not in num]
    for v in cat:
        niveles = train[v].astype("string").dropna().unique().tolist()
        for d in [train] + [o for o in otros if o is not None]:
            d[v] = pd.Categorical(d[v].astype("string"), categories=niveles)
    return num, cat


def pliegues(y, k=5):
    """StratifiedKFold: cada pliegue conserva la tasa de positivos. Devuelve lista de (idx_train, idx_valid)."""
    return list(StratifiedKFold(k, shuffle=True, random_state=SEMILLA).split(np.zeros(len(y)), y))


def oof(ajustar, X, y, folds, **kw):
    """Predicción fuera de pliegue: cada fila la predice un modelo que NO la vio al entrenar."""
    p = np.zeros(len(y))
    for a, b in folds:
        p[b] = ajustar(X.iloc[a], y.iloc[a], X.iloc[b], **kw)
    return p


# =============================================================================================
# 3. MODELOS
# =============================================================================================
def _rank(x):
    return pd.Series(x).rank(pct=True).values          # percentil 0..1 (para promediar escalas distintas)


# ---- 3.0 Regla sin modelo (línea base)
def regla(Xtr, ytr, Xva, k=1):
    g = {}
    for v in Xtr.select_dtypes("number").columns:
        x = Xtr[v]
        if x.notna().mean() > 0.5 and x.nunique() > 1:
            g[v] = gini(ytr, x.fillna(x.median()))       # Gini con signo: negativo = ordena al revés
    top = sorted(g, key=lambda v: -abs(g[v]))[:k]         # las k variables que más separan
    s = np.zeros(len(Xva))
    for v in top:
        x = Xva[v].fillna(Xtr[v].median())
        s += _rank(x if g[v] > 0 else -x)                 # invierte si la relación es negativa
    return s / len(top)


# ---- 3.1 Logística
class Winsor(BaseEstimator, TransformerMixin):
    """Recorta cada columna a sus percentiles p_bajo/p_alto aprendidos en TRAIN (los extremos no dominan)."""
    def __init__(self, p_bajo=0.01, p_alto=0.99):
        self.p_bajo, self.p_alto = p_bajo, p_alto

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        self.lo_, self.hi_ = X.quantile(self.p_bajo), X.quantile(self.p_alto)
        return self

    def transform(self, X):
        return pd.DataFrame(X).clip(self.lo_, self.hi_, axis=1).values

    def get_feature_names_out(self, input_features=None):   # para poder nombrar los coeficientes
        return np.asarray(input_features, dtype=object)


class LogSigno(BaseEstimator, TransformerMixin):
    """sign(x)·log(1+|x|): comprime montos con cola larga sin romper ceros ni negativos."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return np.sign(X) * np.log1p(np.abs(X))

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features, dtype=object)


def pipeline_logistica(num, cat, C=1.0, peso=None):
    pasos_num = Pipeline([
        ("winsor", Winsor(0.01, 0.99)),                                   # 1) recortar extremos
        ("log", LogSigno()),                                              # 2) comprimir cola larga
        ("imputar", SimpleImputer(strategy="median", add_indicator=True)),  # 3) nulo -> mediana + columna "era nulo"
        ("escalar", StandardScaler()),                                    # 4) media 0, desv. 1 (coef comparables)
    ])
    pasos_cat = Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="SIN_DATO")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=0.01, sparse_output=False)),
    ])
    prep = ColumnTransformer([("num", pasos_num, num), ("cat", pasos_cat, cat)], verbose_feature_names_out=False)
    modelo = LogisticRegression(C=C, max_iter=3000, class_weight="balanced" if peso else None)
    return Pipeline([("prep", prep), ("modelo", modelo)])


def fit_logistica(Xtr, ytr, Xva, num, cat, C=1.0, devolver=False):
    pipe = pipeline_logistica(num, cat, C)
    Xtr2 = Xtr.copy(); Xva2 = Xva.copy()
    for c in cat:                                            # OneHotEncoder quiere texto, no Categorical
        Xtr2[c] = Xtr2[c].astype("string").astype(object)
        Xva2[c] = Xva2[c].astype("string").astype(object)
    Xtr2[cat] = Xtr2[cat].where(Xtr2[cat].notna(), None)
    Xva2[cat] = Xva2[cat].where(Xva2[cat].notna(), None)
    pipe.fit(Xtr2, ytr)
    p = pipe.predict_proba(Xva2)[:, 1]
    return (p, pipe) if devolver else p


def coeficientes(pipe):
    nombres = pipe.named_steps["prep"].get_feature_names_out()
    b = pipe.named_steps["modelo"].coef_[0]
    t = pd.DataFrame({"variable": nombres, "coef": b, "odds_ratio": np.exp(b)})
    return t.reindex(t.coef.abs().sort_values(ascending=False).index).reset_index(drop=True)


# ---- 3.2 LightGBM
LGBM = dict(n_estimators=2000,        # techo; el early stopping decide cuántos usa de verdad
            learning_rate=0.05,       # paso de aprendizaje de cada árbol
            num_leaves=31,            # hojas por árbol = complejidad
            min_child_samples=50,     # filas mínimas por hoja = freno contra sobreajuste
            subsample=0.8, subsample_freq=1,   # 80% de filas por árbol
            colsample_bytree=0.8,     # 80% de columnas por árbol
            reg_lambda=1.0,           # penalización L2 de los valores de hoja
            deterministic=True, force_col_wise=True, n_jobs=-1, verbose=-1)


def fit_lgbm(Xtr, ytr, Xva, params=None, peso=False, submuestra=None, regresion=False, objetivo=None,
             devolver=False):
    import lightgbm as lgb
    p = {**LGBM, **(params or {}), "random_state": SEMILLA}
    if objetivo:
        p["objective"] = objetivo
    Xt, yt, k = Xtr, ytr, 1
    if submuestra:                                     # me quedo con 1 de cada `submuestra` negativos
        rng = np.random.default_rng(SEMILLA)
        keep = (ytr.values == 1) | (rng.random(len(ytr)) < 1 / submuestra)
        Xt, yt, k = Xtr[keep], ytr[keep], submuestra
    es = np.random.default_rng(SEMILLA + 1).random(len(yt)) < 0.10   # 10% interno para early stopping
    M = lgb.LGBMRegressor(**p) if regresion else lgb.LGBMClassifier(**p, **({"is_unbalance": True} if peso else {}))
    M.fit(Xt[~es], yt[~es], eval_set=[(Xt[es], yt[es])], callbacks=[lgb.early_stopping(100, verbose=False)])
    pred = M.predict(Xva) if regresion else M.predict_proba(Xva)[:, 1]
    if submuestra and not regresion:
        pred = pred / (pred + (1 - pred) * k)          # corrección de prior: vuelve a la escala real
    return (pred, M) if devolver else pred


# =============================================================================================
# 4. ELECCIÓN, CALIBRACIÓN, MONTO, IMPORTANCIA
# =============================================================================================
SIMPLICIDAD = ["regla_1var", "regla_top3", "logistica", "lgbm", "lgbm_submuestra", "lgbm_pesos", "ensamble"]


def elegir(tabla, tolerancia=0.005):
    """Gana el de mayor Gini, salvo que uno más simple esté a ≤ tolerancia: entonces el simple."""
    mejor = tabla.gini.max()
    ok = tabla[tabla.gini >= mejor - tolerancia].copy()
    ok["orden"] = ok.modelo.map({m: i for i, m in enumerate(SIMPLICIDAD)})
    return ok.sort_values("orden").modelo.iloc[0]


def calibrador(p_oof, y):
    """Isotónica: aprende 'puntaje -> tasa real' sobre predicciones OOF (nunca sobre el examen)."""
    return IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p_oof, y)


def monto_dos_partes(Xtr, mtr, Xdest, params=None, devolver_oof=False):
    """E[monto | convierte] con LightGBM en log1p, solo entre quienes convirtieron, + factor de Duan."""
    pos = (mtr > 0).values
    Xp, lp = Xtr[pos], np.log1p(mtr[pos])
    folds = pliegues((lp > lp.median()).astype(int).reset_index(drop=True))
    Xp, lp = Xp.reset_index(drop=True), lp.reset_index(drop=True)
    pred_oof = oof(lambda a, b, c: fit_lgbm(a, b, c, params=params, regresion=True), Xp, lp, folds)
    duan = float(np.mean(np.exp(lp - pred_oof)))        # promedio de exp(residuo): corrige el sesgo del log
    _, M = fit_lgbm(Xp, lp, Xp.iloc[:5], params=params, regresion=True, devolver=True)
    r2_log = 1 - np.sum((lp - pred_oof) ** 2) / np.sum((lp - lp.mean()) ** 2)
    cond = np.expm1(M.predict(Xdest)) * duan
    if devolver_oof:
        return cond, duan, float(r2_log), np.expm1(pred_oof) * duan
    return cond, duan, float(r2_log)


def importancia(M, Xva, yva, top=25, rep=3):
    """gain (entrenamiento), permutación (caída de Gini en validación) y |SHAP| medio con dirección."""
    vs = list(Xva.columns)
    base = gini(yva, M.predict_proba(Xva)[:, 1])
    gain = pd.Series(M.booster_.feature_importance("gain"), index=vs)
    rng = np.random.default_rng(0)
    perm = pd.Series(0.0, index=vs)
    for v in gain.sort_values(ascending=False).index[:top]:
        caidas = []
        for _ in range(rep):
            Xp = Xva.copy()
            Xp[v] = Xp[v].values[rng.permutation(len(Xp))]
            caidas.append(base - gini(yva, M.predict_proba(Xp)[:, 1]))
        perm[v] = np.mean(caidas)
    contrib = M.booster_.predict(Xva, pred_contrib=True)[:, :-1]
    shap = pd.Series(np.abs(contrib).mean(0), index=vs)
    dirc = {}
    for j, v in enumerate(vs):
        if pd.api.types.is_numeric_dtype(Xva[v]) and Xva[v].nunique() > 1:
            dirc[v] = pd.Series(contrib[:, j]).corr(Xva[v].reset_index(drop=True).astype(float), method="spearman")
    t = pd.DataFrame({"gain": gain / gain.sum(), "permutacion": perm, "shap": shap, "direccion": pd.Series(dirc)})
    return t.sort_values("shap", ascending=False).reset_index(names="variable")


# =============================================================================================
# 5. MAIN
# =============================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabla", required=True, help="tabla de ENTRENAMIENTO (corte anterior si hay)")
    ap.add_argument("--destino", default=None, help="tabla a PUNTUAR (corte actual); si trae target = examen")
    ap.add_argument("--seleccion", default=None, help="seleccion_variables.csv (usa solo QUEDA)")
    ap.add_argument("--salida", default="salidas_sophia")
    ap.add_argument("--rapido", action="store_true", help="sin permutación ni monto")
    a = ap.parse_args()
    t0 = time.time()
    out = Path(a.salida); out.mkdir(parents=True, exist_ok=True)

    tr, vs = cargar(a.tabla, a.seleccion)
    de = cargar(a.destino)[0] if a.destino else None
    num, cat = tipos(tr, [de], vs)
    X, y = tr[vs], tr["target"].astype(int)
    print(f"train {len(tr):,} filas · {len(vs)} variables ({len(num)} num, {len(cat)} cat) · "
          f"tasa {y.mean():.2%} · positivos {y.sum():,} · EPV {y.sum() / len(vs):.0f}")

    folds = pliegues(y)
    P = {}
    P["regla_1var"] = oof(regla, X, y, folds, k=1)
    P["regla_top3"] = oof(regla, X, y, folds, k=3)
    P["logistica"] = oof(fit_logistica, X, y, folds, num=num, cat=cat)
    P["lgbm"] = oof(fit_lgbm, X, y, folds)
    P["lgbm_pesos"] = oof(fit_lgbm, X, y, folds, peso=True)
    P["lgbm_submuestra"] = oof(fit_lgbm, X, y, folds, submuestra=4)
    P["ensamble"] = (_rank(P["logistica"]) + _rank(P["lgbm"])) / 2
    filas = [dict(modelo=m, **resumen(y, p, es_prob=not m.startswith(("regla", "ensamble")))) for m, p in P.items()]
    tabla = pd.DataFrame(filas)
    elegido = elegir(tabla)
    print(tabla.round(4).to_string(index=False))
    print(f"\nELEGIDO: {elegido}")
    tabla.to_csv(out / "comparacion.csv", index=False)
    deciles(y, P[elegido]).to_csv(out / "deciles_oof.csv", index=False)

    destino = de if de is not None else tr
    Xd = destino[vs]
    if elegido == "logistica":
        p_final, pipe = fit_logistica(X, y, Xd, num, cat, devolver=True)
        coeficientes(pipe).to_csv(out / "coeficientes.csv", index=False)
    elif elegido.startswith("regla"):
        p_final = regla(X, y, Xd, k=1 if elegido == "regla_1var" else 3)
    elif elegido == "ensamble":
        p_final = (_rank(fit_logistica(X, y, Xd, num, cat)) + _rank(fit_lgbm(X, y, Xd))) / 2
    else:
        kw = dict(peso=elegido == "lgbm_pesos", submuestra=4 if elegido == "lgbm_submuestra" else None)
        p_final = fit_lgbm(X, y, Xd, **kw)
    cal = calibrador(P[elegido], y)                       # si es regla/ensamble, ESTO la vuelve probabilidad
    prob = cal.predict(p_final) if elegido.startswith(("regla", "ensamble")) else p_final
    res = pd.DataFrame({"id": destino["id"].astype(str), "prob": prob})

    if "target" in destino and de is not None and destino.target.nunique() > 1:
        ex = resumen(destino.target, prob)
        oof_g = tabla.set_index("modelo").gini[elegido]
        print(f"EXAMEN fuera de tiempo: Gini {ex['gini']:.4f} (OOF {oof_g:.4f}) · lift D1 {ex['lift_d1']:.2f}x")

    if not a.rapido:
        a_, b_ = folds[0]
        _, M = fit_lgbm(X.iloc[a_], y.iloc[a_], X.iloc[b_], devolver=True)
        imp = importancia(M, X.iloc[b_], y.iloc[b_])
        imp.to_csv(out / "importancia.csv", index=False)
        print("\nTop 10 importancia (LightGBM de referencia, pliegue de validación):")
        print(imp.head(10).round(4).to_string(index=False))
        if "target_monto" in tr:
            m_si, duan, r2l = monto_dos_partes(X, tr["target_monto"].astype(float), Xd)
            res["monto_si_convierte"] = m_si
            res["valor_esperado"] = res.prob * res.monto_si_convierte
            print(f"\nMonto: factor de Duan {duan:.2f} · R² condicional en log {r2l:.3f}")
    res.sort_values("prob", ascending=False).to_csv(out / "predicciones.csv", index=False)
    print(f"\nListo en {time.time() - t0:.0f} s -> {out}")


if __name__ == "__main__":
    main()
```

## `trabajo/sophia_extras.py`

```python
"""
EXTRAS DE SOPHIA: fugas, Optuna, ¿uno o varios modelos?, K-means de perfiles, Tweedie y validación temporal.
Importa las piezas de sophia_modelos.py (mismo folder).

    python trabajo/sophia_extras.py fugas    --tabla T1 [--destino T0]
    python trabajo/sophia_extras.py optuna   --tabla T1 --segundos 120
    python trabajo/sophia_extras.py segmento --tabla T1 --segmento maestrocli__flag_lead_factoring
    python trabajo/sophia_extras.py kmeans   --tabla T1 --k 4
    python trabajo/sophia_extras.py tweedie  --tabla T1
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sophia_modelos as S  # noqa: E402


def fugas(tr, vs, de=None, umbral=0.5):
    """Gini INDIVIDUAL de cada variable (en train y, si hay, en el corte actual). > umbral = sospecha."""
    filas = []
    for v in vs:
        x = tr[v]
        if not pd.api.types.is_numeric_dtype(x):                      # categórica -> tasa de su categoría
            x = x.astype("string").map(x.astype("string").value_counts(normalize=True)).astype(float)
        if x.notna().sum() < 10 or x.nunique() < 2:
            continue                                             # vacía o constante: no se puede medir
        g = abs(S.gini(tr.target, x.fillna(x.min() - 1)))
        f = dict(variable=v, gini_train=g, pct_nulo=float(tr[v].isna().mean()))
        if de is not None and "target" in de and v in de and de.target.nunique() > 1:
            xd = de[v]
            if not pd.api.types.is_numeric_dtype(xd):
                xd = xd.astype("string").map(xd.astype("string").value_counts(normalize=True)).astype(float)
            if xd.notna().sum() >= 10 and xd.nunique() > 1:
                f["gini_actual"] = abs(S.gini(de.target, xd.fillna(xd.min() - 1)))
        filas.append(f)
    t = pd.DataFrame(filas)
    t["sospecha"] = (t.gini_train > umbral) | (t.get("gini_actual", 0) > umbral)
    t["peor"] = t[[c for c in ("gini_train", "gini_actual") if c in t]].max(axis=1)   # la peor de las dos
    return t.sort_values("peor", ascending=False).drop(columns="peor")


def optuna_lgbm(X, y, segundos=120, pruebas=60):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    folds = S.pliegues(y, k=3)                       # 3 pliegues: más pruebas en el mismo tiempo

    def objetivo(trial):
        params = dict(
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            num_leaves=trial.suggest_int("num_leaves", 7, 127, log=True),
            min_child_samples=trial.suggest_int("min_child_samples", 10, 300, log=True),
            subsample=trial.suggest_float("subsample", 0.5, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.3, 1.0),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 30, log=True))
        return S.gini(y, S.oof(S.fit_lgbm, X, y, folds, params=params))

    est = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=S.SEMILLA))
    est.enqueue_trial(dict(learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8,
                           colsample_bytree=0.8, reg_lambda=1.0))          # prueba 0 = default
    est.optimize(objetivo, n_trials=pruebas, timeout=segundos)
    default = est.trials[0].value
    print(f"{len(est.trials)} pruebas · default {default:.4f} -> mejor {est.best_value:.4f} "
          f"(+{est.best_value - default:.4f})\nmejores: {est.best_params}")
    try:
        print("importancia de perillas:", {k: round(v, 2) for k, v in optuna.importance.get_param_importances(est).items()})
    except Exception:
        pass
    return est.best_params


def uno_o_varios(tr, vs, num, cat, seg):
    """Gini dentro de cada segmento: modelo GLOBAL (todos, con el segmento como variable) vs uno PROPIO."""
    X, y = tr[vs], tr.target.astype(int)
    folds = S.pliegues(y)
    glob = {"logistica": S.oof(S.fit_logistica, X, y, folds, num=num, cat=cat), "lgbm": S.oof(S.fit_lgbm, X, y, folds)}
    s = tr[seg].astype("string").fillna("NA")
    vs2 = [v for v in vs if v != seg]
    num2, cat2 = [v for v in num if v != seg], [v for v in cat if v != seg]
    filas = []
    for g in s.unique():
        m = (s == g).to_numpy(dtype=bool)
        yg = y[m].reset_index(drop=True)
        f = dict(segmento=g, n=int(m.sum()), positivos=int(yg.sum()), tasa=float(yg.mean()))
        if yg.sum() >= 30 and len(yg) - yg.sum() >= 30:
            Xg, fg = tr.loc[m, vs2].reset_index(drop=True), S.pliegues(yg)
            f["log_global"] = S.gini(yg, glob["logistica"][m])
            f["log_propio"] = S.gini(yg, S.oof(S.fit_logistica, Xg, yg, fg, num=num2, cat=cat2))
            f["lgbm_global"] = S.gini(yg, glob["lgbm"][m])
            f["lgbm_propio"] = S.gini(yg, S.oof(S.fit_lgbm, Xg, yg, fg))
        filas.append(f)
    return pd.DataFrame(filas)


def kmeans_perfiles(tr, num, k=4, max_vars=8):
    """Perfiles DESCRIPTIVOS (no predicen): variables numéricas estandarizadas en log -> K-means."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    cols = [v for v in num if tr[v].notna().mean() > 0.8 and tr[v].nunique() > 10][:max_vars]
    Z = tr[cols].fillna(tr[cols].median())
    Z = np.sign(Z) * np.log1p(np.abs(Z))                     # cola larga -> log
    Z = StandardScaler().fit_transform(Z)                     # misma escala: si no, manda la de soles
    for kk in range(2, 7):                                    # elegir k: silueta más alta (y que se pueda contar)
        lab = KMeans(kk, n_init=10, random_state=S.SEMILLA).fit_predict(Z)
        print(f"  k={kk}: silueta {silhouette_score(Z, lab, sample_size=min(5000, len(Z)), random_state=0):.3f}")
    lab = KMeans(k, n_init=10, random_state=S.SEMILLA).fit_predict(Z)
    perfil = tr[cols].assign(grupo=lab).groupby("grupo").median()
    perfil["n"] = pd.Series(lab).value_counts().sort_index()
    if "target" in tr:
        perfil["tasa_conversion"] = tr.target.groupby(lab).mean()
    return perfil


def tweedie_vs_dos_partes(tr, vs):
    """Monto directo con Tweedie (muchos ceros + cola larga) vs dos partes; R² en soles y Spearman."""
    from scipy.stats import spearmanr
    X, y, m = tr[vs], tr.target.astype(int), tr.target_monto.astype(float)
    folds = S.pliegues(y)
    p = S.oof(S.fit_lgbm, X, y, folds)
    tw = S.oof(lambda a, b, c: S.fit_lgbm(a, b, c, regresion=True, objetivo="tweedie",
                                          params=dict(tweedie_variance_power=1.5)), X, m, folds)
    cond, duan, _, oof_pos = S.monto_dos_partes(X, m, X, devolver_oof=True)
    pos = (m > 0).values
    cond[pos] = oof_pos                       # en quienes convirtieron, usar la predicción OOF (honesta)
    dp = p * cond
    r2 = lambda a, b: 1 - np.sum((a - b) ** 2) / np.sum((a - a.mean()) ** 2)
    print(f"R² soles: dos partes {r2(m, dp):.3f} · Tweedie {r2(m, tw):.3f} | "
          f"Spearman: {spearmanr(m, dp).statistic:.3f} · {spearmanr(m, tw).statistic:.3f} | Duan {duan:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["fugas", "optuna", "segmento", "kmeans", "tweedie"])
    ap.add_argument("--tabla", required=True)
    ap.add_argument("--destino", default=None)
    ap.add_argument("--seleccion", default=None)
    ap.add_argument("--segmento", default=None)
    ap.add_argument("--segundos", type=int, default=120)
    ap.add_argument("--k", type=int, default=4)
    a = ap.parse_args()
    tr, vs = S.cargar(a.tabla, a.seleccion)
    de = S.cargar(a.destino)[0] if a.destino else None
    if a.segmento and a.segmento not in vs:
        vs.append(a.segmento)
    num, cat = S.tipos(tr, [de], vs)
    pd.set_option("display.width", 200)
    if a.accion == "fugas":
        print(fugas(tr, vs, de).head(15).round(3).to_string(index=False))
    elif a.accion == "optuna":
        optuna_lgbm(tr[vs], tr.target.astype(int), a.segundos)
    elif a.accion == "segmento":
        print(uno_o_varios(tr, vs, num, cat, a.segmento).round(4).to_string(index=False))
    elif a.accion == "kmeans":
        print(kmeans_perfiles(tr, num, a.k).round(2).to_string())
    elif a.accion == "tweedie":
        tweedie_vs_dos_partes(tr, vs)
```
