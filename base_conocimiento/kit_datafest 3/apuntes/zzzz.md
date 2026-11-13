# GUÍA DE LIZ · Data Scientist 2
## "¿Por qué predice el modelo y a quién llamamos?"

> Repo base: `github.com/Lizzz7/plantilla_2026` (carpeta `plantilla_avanzada/` + kit simple en `base_conocimiento/kit_datafest 3/`).
> Todo lo marcado con **(probado)** lo corrí con los datos sintéticos de la plantilla (8 000 empresas, `run_modelo.py --rapido`) el 13/11. Los números de ejemplo salen de ahí; con los datos reales cambiarán.

---

## ÍNDICE

0. [Lee esto primero (hoy es viernes 13)](#0-lee-esto-primero)
1. [Tu rol en una frase y tus contratos](#1-tu-rol)
2. [Mapa del repo: qué carpeta usar](#2-mapa-del-repo)
3. [Flujo general del evento (de los datos al jurado)](#3-flujo-general)
4. [Archivo por archivo: qué hace cada uno](#4-archivo-por-archivo)
5. [TUS archivos, bloque por bloque y línea por línea](#5-tus-archivos-línea-por-línea)
6. [Probabilidad y estadística que necesitas (concepto → ejemplo → interpretación)](#6-probabilidad-y-estadística)
7. [Métricas: qué mide cada una, cómo se relacionan, cómo leerlas](#7-métricas)
8. [Banca, factoring y riesgos: lo que debes saber](#8-banca-factoring-y-riesgos)
9. [Decisiones de negocio: del score a la lista de llamadas](#9-decisiones-de-negocio)
10. [Hallazgos de negocio: cómo encontrarlos y explicarlos](#10-hallazgos-de-negocio)
11. [Tu cronograma y tareas, hora por hora](#11-cronograma-y-tareas)
12. [Pruebas y tests (con scripts listos)](#12-pruebas-y-tests)
13. [Errores comunes y arreglos en cada paso tuyo](#13-errores-comunes-y-arreglos)
14. [Escenarios: si el caso cambia, qué haces](#14-escenarios)
15. [Qué puedes agregar o quitar (de lo simple a lo complejo)](#15-qué-agregar-o-quitar)
16. [Cómo modificar archivos sin romper las reglas](#16-cómo-modificar-archivos)
17. [Preguntas para Copilot en cada paso](#17-preguntas-para-copilot)
18. [Preguntas para el organizador / mentor](#18-preguntas-al-organizador)
19. [Lo que el jurado espera + preguntas y respuestas](#19-jurado)
20. [Lenguaje de negocio: frases listas](#20-lenguaje-de-negocio)
21. [Glosario](#21-glosario)
22. [Hoja de bolsillo (1 página)](#22-hoja-de-bolsillo)

---

## 0. Lee esto primero

| Hora (vie 13 / sáb 14) | Qué pasa | Qué significa para ti |
|---|---|---|
| **antes de 13:30 vie** | último PR a `main` con `base_conocimiento/` | si quieres esta guía dentro de la base, va en `base_conocimiento/notas/` **y** se declara en `INVENTARIO.md` como preparada con ayuda de IA (solo si la organización lo aprobó) |
| **14:00 vie** | se cierra `base_conocimiento/` | desde aquí **no se edita nada ahí**. Todo lo nuevo va en `trabajo/` |
| 14:30 vie | presentan el caso | tú anotas: **formato de entrega, capacidad comercial, cupos, métrica** |
| 15:30 vie | inicio | durante el evento **solo puedes usar el Copilot del evento**. Esta guía es para leer ANTES |
| ~22:00 vie | primer `submission.csv` válido | es TU responsabilidad principal |
| 09:00 sáb | se congela el modelo | ya no cambias el modelo; solo entrega, presentación y bitácoras |
| **10:30 sáb** | cierre: solo cuenta lo que está en `main` | |
| 11:30 sáb | evaluación técnica (te pueden preguntar a ti) | sección 19 |

**Tres reglas que no se rompen:**
1. Primero una entrega **válida**, después una **buena**.
2. No pegues datos ni el enunciado en ningún servicio (Copilot no ve los datos; tú no se los des).
3. Si algo da "demasiado bien" (Gini > 0.8 o una variable con Gini > 0.5) → **para todo y busca la fuga**.

---

## 1. Tu rol

**En una frase:** conviertes probabilidades en una **decisión de negocio** (a quién llamar, cuánto vale, por qué) que cumpla las reglas del concurso, y la **explicas** en lenguaje de banco.

### Lo que recibes y lo que entregas (contratos)

| De → a | Archivo | Qué debe cumplir |
|---|---|---|
| Sophia (DS1) → **tú** | `salidas/modelo/predicciones.csv` (plantilla avanzada) o `prob.parquet` (kit simple) | `id` único, `prob` entre 0 y 1, una fila por empresa a puntuar |
| Kath (DE2) → **tú** | `tabla_modelo.parquet`, `diccionario_variables.csv` | 1 fila por empresa, variables con frase de negocio |
| **tú** → jurado | `entregas/submission.csv` | columnas exactas del enunciado, 1 fila por empresa, sin nulos, exactamente K priorizadas |
| **tú** → Nat | 3 hallazgos + diapositivas "A quiénes priorizamos", "Hallazgo", "Impacto" | cada hallazgo con número y acción |

### Tus 6 responsabilidades

| # | Responsabilidad | Archivo de la plantilla | Pregunta que respondes |
|---|---|---|---|
| 1 | Importancia de variables | `pipeline/modelado/importancia.py` | ¿qué mira el modelo y en qué dirección? |
| 2 | Uno o varios modelos (segmentos) | `pipeline/modelado/segmentos_monto.py` | ¿con lead y sin lead se comportan distinto? |
| 3 | Monto esperado | `segmentos_monto.dos_partes` | si convierte, ¿cuánto financia? |
| 4 | Priorización con capacidad | `pipeline/modelado/priorizar.py` | ¿a quién llamamos con K llamadas? |
| 5 | Entrega | `evento/exportar_submission.py` + `python -m datafest.validar` | ¿el CSV pasa el validador? |
| 6 | Historia de negocio | `evento/presentacion_index.html` (láminas 4–7) | ¿qué ganó el banco? |

---

## 2. Mapa del repo

Hay **dos** caminos. Usen **uno** como principal y el otro como plan B.

```
plantilla_2026/
├── plantilla_avanzada/          ← CAMINO PRINCIPAL (automático, robusto, 8 GB)
│   ├── config.py                ← parámetros del caso (en el evento NO se edita: se usa trabajo/config_evento.py)
│   ├── run_pipeline.py          ← datos crudos → tabla_modelo.parquet + monitor.html
│   ├── run_modelo.py            ← tabla_modelo → modelos, importancia, monto, priorización, predicciones.csv
│   ├── pipeline/                ← ingesta, perfil, limpieza, llaves, features, seleccion, monitor
│   │   └── modelado/            ← datos, diagnostico, candidatos, afinamiento, importancia(TÚ),
│   │                              segmentos_monto(TÚ), priorizar(TÚ), metricas, reporte_modelo
│   ├── evento/                  ← config_evento.py, exportar_submission.py(TÚ), presentacion_index.html(TÚ)
│   ├── docs/                    ← MODELADO, ESCENARIOS, PASOS_EVENTO, GUIA_EJECUCION, CAMBIOS_REVISION
│   └── experimentos/            ← pruebas de escenarios (segmentos opuestos, desbalance severo...)
└── base_conocimiento/kit_datafest 3/   ← PLAN B (5 scripts cortos, uno por persona)
    ├── scripts/5_entregar.py    ← TU script del kit simple
    ├── scripts/optimizacion/priorizar_restricciones.py ← TU plan B de restricciones
    └── apuntes/08, 01, 12, 18   ← lo que debes dominar
```

**¿Cuál uso?** La plantilla avanzada. El kit simple te sirve para **entender** (son 40 líneas, se explica en 1 minuto) y como plan B si la avanzada falla por algo raro.

---

## 3. Flujo general

```
USB / data/                (crudo, NO se toca)
   │  run_pipeline.py      Hellen + Kath
   ▼
bronze (texto) → perfil → silver (limpio) → llaves → variables (< corte) → selección (embudo)
   │                                                        │
   │                                         tabla_modelo.parquet  (+ tabla_modelo_t1 = corte anterior)
   ▼                                                        │  run_modelo.py   Sophia + TÚ
monitor.html                     1 diagnóstico → 2 candidatos → 3 Optuna (opcional)
                                 4 SEGMENTOS (tú) → 5 IMPORTANCIA (tú) → 6 MONTO (tú)
                                 7 predicción final → 8 PRIORIZACIÓN (tú)
                                                            │
                                     salidas/modelo/predicciones.csv + reporte_modelo.html
                                                            │  exportar_submission.py   TÚ
                                                            ▼
                                     entregas/submission.csv → python -m datafest.validar → PR a main
                                                            │
                                     presentacion/index.html (láminas de negocio)   TÚ + Nat
```

### Comandos del evento (desde la raíz del repo del evento)

```bash
# 15:30 — una sola vez
mkdir -p trabajo && cp base_conocimiento/plantilla/evento/config_evento.py base_conocimiento/plantilla/evento/exportar_submission.py trabajo/

# Hellen/Kath
python base_conocimiento/plantilla/run_pipeline.py --config trabajo/config_evento.py
python base_conocimiento/plantilla/run_pipeline.py --config trabajo/config_evento.py --desde features --corte AAAA-MM-DD --sufijo _t1

# Sophia (primero rápido)
python base_conocimiento/plantilla/run_modelo.py --config trabajo/config_evento.py --rapido

# TÚ
python trabajo/exportar_submission.py --config trabajo/config_evento.py
python -m datafest.validar
```

Windows: igual, cambiando `/` por `\` en `copy` y usando `py` si `python` no existe.

---

## 4. Archivo por archivo

Para cada archivo: **qué hace**, **qué miras tú** y **si lo tocas**. (Los tuyos van en detalle en la sección 5.)

### Raíz de `plantilla_avanzada/`

| Archivo | Qué hace | Qué miras tú | ¿Tocas? |
|---|---|---|---|
| `config.py` | Única fuente de verdad: rutas, RAM, `FECHA_CORTE`, `HORIZONTE_MESES`, `TARGET`, `SEGMENTO`, `CAPACIDAD`, `CUPOS_ZONA`, `COLUMNA_ZONA`, umbrales `U` | `CAPACIDAD`, `CUPOS_ZONA`, `COLUMNA_ZONA`, `SEGMENTO`, `TARGET["monto"]` | **No** en el evento. Se cambia en `trabajo/config_evento.py` (lo cuida Nat; tú le pides los cambios) |
| `run_pipeline.py` | Orquesta 7 pasos; `--desde` retoma; `--corte`+`--sufijo _t1` crea la tabla del corte anterior | que termine con "Listo" | No |
| `run_modelo.py` | Orquesta el modelado en 8 pasos (detalle en §5.1) | pasos 4–8 son tuyos | No (en el evento) |
| `generar_datos_prueba.py` | Crea datos SUCIOS sintéticos con trampas (fuga, centinelas, USD) | para practicar | No |
| `preparar_offline.py` | Instala y prueba todo, imprime OK/FALTA | correrlo en tu laptop con internet | No |
| `requirements.txt` | Librerías | — | No |

### `pipeline/` (datos)

| Archivo | Qué hace (en una línea) | Lo que te importa |
|---|---|---|
| `ingesta.py` | Excel/CSV → Parquet todo como TEXTO (nunca falla por tipos); une hojas y archivos partidos | si una tabla quedó en 0 filas, nada de lo tuyo sirve |
| `perfil.py` | Ficha por columna: vacía, constante, llave, fecha, número, categoría; marca nombres sospechosos "¿POSTERIOR AL CORTE?" | `perfil_columnas.csv` te dice qué significa cada columna (para explicar hallazgos) |
| `db.py` | Conexión DuckDB + macros `txt`, `idn`, `num`, `fecha` | `idn` quita el `.0` del RUC: si el `id` de tu entrega no calza con el del banco, mira aquí |
| `limpieza.py` | bronze → silver con las macros; concilia montos antes/después | — |
| `llaves.py` | grano (qué identifica una fila) y relaciones entre tablas | — |
| `features.py` | 1 fila por empresa: RFM, ventanas 3/6/12m, tendencia, recencia, HHI, contagio de red, target en `[corte, corte+horizonte)` | **la fuente de tus hallazgos**: cada variable tiene frase en `diccionario_variables.csv` |
| `regularizar.py` | Lo que aprende de los datos (percentiles, medianas, target encoding) SOLO con train; modo árbol vs lineal | explica por qué aparecen `__te`, `__frec`, `==VALOR`, `__nulo` en los coeficientes |
| `seleccion.py` | Embudo F1–F5: copias, PSI, fuga (Gini>0.5 o IV>0.5), sin señal, redundancia | `seleccion_variables.csv`: si una variable "estrella" está en REVISAR_FUGA, **no la uses en la historia** |
| `monitor.py` | HTML con KPIs, línea de tiempo, rubros (Pareto), llaves | gráfico de rubros = hallazgo de negocio gratis |
| `bitacora.py` | registra filas/columnas/sumas por paso | conciliación: "no perdimos plata" |
| `plataforma.py` | diferencias Windows/macOS/Linux | — |
| `features_polars.py` | alternativa en Polars (mismo resultado) | — |

### `pipeline/modelado/`

| Archivo | Qué hace | Dueña |
|---|---|---|
| `datos.py` | decide train/puntuar: (1) lista `EVALUAR`, (2) fuera de tiempo con `_t1`, (3) validación cruzada | Sophia |
| `diagnostico.py` | mide la data y recomienda: desbalance, EPV, ceros del monto, segmentos con efectos invertidos, PSI | Sophia (tú lees la parte de segmentos y monto) |
| `candidatos.py` | regla_1var, regla_top3, logística, lgbm, lgbm_pesos, lgbm_submuestra, xgb, catboost, ensamble — mismos pliegues OOF | Sophia (tú usas `explicar_logistica`) |
| `afinamiento.py` | Optuna (TPE) + importancia de hiperparámetros (fANOVA) | Sophia |
| `metricas.py` | Gini, AUC-PR, lift, captura, Brier, calibración, deciles, R² | **ambas** |
| `importancia.py` | gain, permutación, SHAP, estabilidad, sentido | **TÚ** |
| `segmentos_monto.py` | global vs por segmento; monto en dos partes vs Tweedie | **TÚ** |
| `priorizar.py` | voraz por zona y PuLP+HiGHS con restricciones | **TÚ** |
| `reporte_modelo.py` | HTML del modelado | ambas |

### `evento/`

| Archivo | Qué hace | Dueña |
|---|---|---|
| `config_evento.py` | hereda `config.py`, manda datos a `data/` y salidas a `~/datafest_trabajo/`, apaga los ejemplos (`SEGMENTO`, `CUPOS_ZONA`, `EVALUAR`... = None) | Nat |
| `exportar_submission.py` | `predicciones.csv` → `entregas/submission.csv` con el FORMATO del enunciado + controles | **TÚ** |
| `presentacion_index.html` | 9 láminas sin internet; tecla `t` oculta el anexo técnico | Nat + **TÚ** |
| `copiar_a_base.py` | arma `base_conocimiento/` + `INVENTARIO.md` | Nat (antes de 14:00) |
| `USO_DE_IA_ejemplo.md`, `BITACORA_FUENTES_inicial.md` | formato de bitácoras obligatorias | todas |

### `docs/` — qué leer

| Doc | Para qué | Prioridad para ti |
|---|---|---|
| `MODELADO.md` | §1 regla vs modelo, §2 desbalance, §4 importancia, §5 varios modelos, §6 monto | ★★★ |
| `ESCENARIOS.md` | §5 métrica y capacidad, §3 qué falta | ★★★ |
| `PASOS_EVENTO.md` | horario y comandos | ★★ |
| `CAMBIOS_REVISION.md` | por qué explicar la logística y no LightGBM si gana la logística | ★★ |

---

## 5. Tus archivos línea por línea

### 5.1 `run_modelo.py` — los pasos que te tocan

```python
SIMPLICIDAD = ["regla_1var", "regla_top3", "logistica", "lgbm", ...]
```
Orden de "más simple a más complejo". **`elegir()`** toma el de mayor Gini, *salvo* que uno más simple esté a menos de 0.005: gana el simple (parsimonia). Por eso a veces se entrega la logística aunque LightGBM esté "casi igual".

**Paso 4 · segmentos**
```python
seg, ganan_seg = segmentos_monto.comparar_segmentos(D, preds, params, elegido)
```
Compara global vs un modelo por segmento (`config.SEGMENTO`). `ganan_seg` = lista de segmentos donde ganó "separado" → se usan en la predicción final.

**Paso 5 · importancia**
```python
if D["examen"]:            # hay corte actual con target → mide en datos NO vistos (fuera de tiempo)
    _, mod = candidatos.fit_lgbm(tr[vs], y, Xva, ...)
else:                      # si no, mide en el primer pliegue de validación
```
- `fold_models`: 3 LightGBM entrenados en 3 pliegues → para ver si el ranking es **estable**.
- `importancia.calcular(...)` → `importancia_variables.csv`.
- `i = argmax(prob)` → toma **la empresa con mayor probabilidad** y descompone su predicción (`R["caso"]`): es tu ejemplo de "¿por qué esta empresa?".
- `if elegido == "logistica":` → explica con **coeficientes de la logística** (`coeficientes_logistica.csv`), no con LightGBM. Regla: **se explica el modelo que se entrega**.

**Paso 6 · monto**
```python
mon, mod_monto = segmentos_monto.dos_partes(D, preds[base], params)
```
Si el `TARGET` tiene `monto=`, entrena E[monto | convierte]. Si no hay monto, `mod_monto = None` y el valor esperado es solo la probabilidad.

**Paso 7 · predicción final**
```python
destino["monto_si_convierte"] = expm1(lp_pred) * factor_duan   # vuelve de log a soles, corregido
if elegido.startswith(("regla", "ensamble")):                    # no son probabilidades
    prob_cal = IsotonicRegression(...)                           # se calibran: percentil → tasa real
destino["valor_esperado"] = prob_cal * monto_si_convierte
```
Si hay examen: imprime `Gini` y `lift D1` en el corte actual vs OOF en train. **Esa comparación es tu prueba de honestidad.**

**Paso 8 · priorización**
```python
pv = priorizar.voraz(destino, zona=zona, cupos=C.CUPOS_ZONA)
pe, estado = priorizar.entero(destino, zona=zona, cupos=C.CUPOS_ZONA)
```
Corre los dos. Si dan el mismo valor → presentas el **voraz** (más fácil de explicar). Si difieren → **PuLP** (óptimo). Guarda `predicciones.csv` ordenado por `valor_esperado`.

Salida real (probado):
```
voraz: 200 empresas, valor 17,718,370 · PuLP (Optimal): valor 17,718,370 -> iguales: usar voraz
conversion_priorizados 0.42, conversion_base 0.1905   → 2.2x
```

### 5.2 `pipeline/modelado/importancia.py` — línea por línea

```python
gain  = modelo.booster_.feature_importance("gain")
```
Cuánto bajó el error **en entrenamiento** cada vez que el árbol cortó por esa variable. Rápido pero **sesgado** hacia variables con muchos valores distintos (montos, ids).

```python
split = modelo.booster_.feature_importance("split")
```
Cuántas veces se usó para cortar. Solo informativo.

```python
base = M.gini(yva, modelo.predict_proba(Xva)[:, 1])
for v in gain...[:top_perm]:                  # solo las top 30 por gain (ahorra tiempo)
    for _ in range(repeticiones):              # 3 veces, porque desordenar es aleatorio
        Xp[v] = Xp[v].values[rng.permutation(len(Xp))]   # desordena SOLO esa columna
        caidas.append(base - M.gini(yva, ...)) # ¿cuánto cayó el Gini?
    perm[v] = mean(caidas)
```
**Permutación** = la medida más honesta: "si borro la información de esta variable en datos que el modelo no vio, ¿cuánto empeora?". ≈0 → sobra. Muy alta + frase rara → **fuga**.
⚠ Con `--rapido`, `top_perm=0` → toda la permutación sale **0.0** (probado). No es un bug: corre sin `--rapido` para tener permutación.

```python
contrib = modelo.booster_.predict(Xva, pred_contrib=True)[:, :-1]
```
**SHAP nativo de LightGBM**: para cada empresa, cuánto aportó cada variable a su log-odds. La última columna es el "sesgo" (promedio) y se descarta. Suma exacta: sesgo + Σ aportes = predicción en log-odds.

```python
shap_abs = abs(contrib).mean(0)            # importancia global
direccion[v] = corr_spearman(contrib[:, j], x)   # ¿cuando x sube, el aporte sube?
t["sentido"] = "más -> sube prob" si direccion > 0.2, "más -> baja prob" si < -0.2, si no "mixto/categ."
```
`sentido` es **tu frase de negocio** ("a más ventas, más probabilidad").

```python
ranks = ...rank(ascending=False) por pliegue; rank_min, rank_max
```
Si una variable es #1 en un pliegue y #40 en otro → **frágil**, no la pongas como hallazgo principal.

**Cómo leer `importancia_variables.csv` (tabla de decisión):**

| gain | permutación | SHAP | Lectura | Acción |
|---|---|---|---|---|
| alto | alta | alto | importante de verdad | hallazgo principal |
| alto | baja | medio | el modelo la usa, pero otra dice lo mismo (correlacionadas) | menciónala junto a su "gemela" |
| bajo | ~0 | bajo | sobra | puede salir (pregunta a Sophia) |
| alto | **muy** alta | alto + frase rara ("cierre", "resultado") | **fuga** | avisa a Kath/Sophia YA |
| rank_min 1, rank_max 30 | — | — | frágil | no la uses en la historia |

### 5.3 `candidatos.explicar_logistica` — cuando gana la logística

```python
A = Regularizador("lineal").fit_transform(Xtr, ytr)   # winsoriza p1/p99, log si sesgo>2, mediana+indicador, ESTANDARIZA
m = LogisticRegression().fit(A, ytr)
coef        → cuánto suben los log-odds si la variable sube 1 desviación estándar
odds_ratio  = exp(coef) → multiplica las chances (1.5 = +50 %; 0.7 = −30 %)
aporte caso = coef × (valor − promedio)               # SHAP exacto de un modelo lineal
```
Salida real (probado):

| variable | coef | odds_ratio | lectura |
|---|---|---|---|
| `operacione__n_total` | +0.48 | 1.62 | cada desviación estándar más de operaciones previas multiplica las chances por 1.6 |
| `maestrocli__ventas_anuales` | +0.41 | 1.51 | empresas más grandes: +51 % de chances por desviación |
| `rubro==MANUFACTURA` | +0.43 | 1.54 | manufactura tiene 54 % más chances que la referencia |
| `rubro__te` | −1.32 | 0.27 | ⚠ **no lo leas solo** |

⚠ **Trampa:** el rubro aparece dos veces (`__te` = tasa del rubro y `==VALOR` = one-hot). Se reparten el efecto y uno puede salir con signo "raro". **Para explicar un rubro, mira la tasa real por rubro** (gráfico de rubros del monitor o un `groupby`), no el coeficiente suelto.

### 5.4 `pipeline/modelado/segmentos_monto.py`

**`familia_de(elegido)`** → si el elegido es logística o regla, compara logísticas; si no, LightGBM.

**`comparar_segmentos`** línea por línea:
```python
for g in s.unique():                                  # cada segmento (p.ej. con lead / sin lead)
    if yg.sum() >= 30 and (len(yg)-yg.sum()) >= 30:   # mínimo 30 positivos y 30 negativos
        gini_global_f   = gini del modelo GLOBAL evaluado SOLO dentro del segmento
        gini_separado_f = gini de un modelo entrenado SOLO con ese segmento (OOF)
    if separado > global + 0.005 → "separado" (y se usa en la predicción final)
    else → "global"
    else (pocos datos) → "global (pocos positivos)"
n_modelos_recomendado = 1 + segmentos que ganan separado
```
**Interpretación:** LightGBM global casi siempre empata porque aprende la interacción solo. Separar le sirve a la **logística** cuando una variable **cambia de signo** entre segmentos (experimento A del repo: 0.15 → 0.63).

**`predecir_por_segmento`**: entrena un modelo por cada segmento ganador y reemplaza la probabilidad SOLO en esas filas.

**`dos_partes`** (el monto) línea por línea:
```python
pos = (m > 0)                                  # solo los que convirtieron
lp  = log1p(m[pos])                            # log: los montos tienen cola larga
pred_log OOF con LightGBM regresor             # E[log monto | convierte]
duan = mean(exp(lp - pred_log))                # factor de Duan: exp(media de log) < media → se corrige hacia arriba
cond_todos = expm1(mod.predict(...)) * duan    # monto si convierte, para TODAS las empresas
esperado = p_conv * cond_todos                 # VALOR ESPERADO
directo  = LightGBM Tweedie sobre todos        # alternativa: una sola regresión que tolera ceros
compara R² en soles, Spearman y R² condicional en log → gana el de mayor R²
```
Salida real (probado): `R² dos partes 0.121 vs directo 0.109 · Spearman 0.225 vs 0.225 · R² condicional log 0.466`.
**Lectura:** "El tamaño de la operación sí tiene señal (R² 0.47 en log entre quienes convierten), pero predecir soles exactos de todos es difícil (R² 0.12) porque el 81 % no convierte. Por eso separamos: ¿convierte? y ¿cuánto?".

### 5.5 `pipeline/modelado/priorizar.py`

**`voraz`** línea por línea:
```python
n_total = int(cap * len(df)) if cap < 1 else int(cap)   # CAPACIDAD: fracción (0.025) o número (500)
df = df.sort_values(valor, ascending=False)             # mayor valor esperado primero
cupos = _normalizar_cupos(...)                          # 'Lima' → 'LIMA' (los datos vienen en MAYÚSCULAS)
for z, pct in cupos.items():
    k = round(n_total * pct / tot)                      # cupo de la zona
    idx = primeras k de esa zona → priorizado = 1
resto = n_total - priorizadas                           # si una zona no tiene suficientes
if resto > 0: completa con las de mayor valor SIN cupo  # ⚠ avisa en consola
```
Es **óptimo** cuando cada empresa pertenece a una sola zona y la única regla es el cupo por zona.

⚠ **Detalle:** `round()` por zona puede hacer que la suma de cupos no dé exactamente `n_total` (p.ej. 3 zonas con 33.3 %). El kit simple usa el **método del resto mayor** (siempre suma exacto). Si el validador exige "exactamente K", revisa la suma (test en §12).

**`entero`** (PuLP + HiGHS):
```python
cand = df.nlargest(n_total*20)        # poda: el óptimo está arriba (más rápido)
x_i ∈ {0,1}                           # ¿llamo a la empresa i?
max Σ x_i · valor_i                   # objetivo
Σ x_i ≤ n_total                       # capacidad
Σ x_i (zona z) ≤ cupo_z               # cupos
Σ x_i · col_i ≥ mínimo · n_total      # restricciones_extra, p.ej. ("es_pyme", 0.6)
```
Úsalo cuando hay **restricciones que se cruzan** (zona Y mínimo Pyme Y tope por ejecutivo Y presupuesto). Ahí ordenar y cortar deja de ser óptimo.

### 5.6 `pipeline/modelado/metricas.py` (lo que usas)

| Función | Fórmula / idea | Para qué la usas |
|---|---|---|
| `gini(y,p)` | 2·AUC − 1 | ¿ordena bien? |
| `auc_pr` | precisión promedio | desbalance severo |
| `lift(y,p,0.10)` | tasa en top 10 % / tasa base | **frase del jurado** |
| `captura(y,p,0.10)` | % de positivos que caen en el top 10 % | "con 10 % de las llamadas capturamos X % de las conversiones" |
| `brier` | promedio de (p − y)² | ¿la probabilidad es real? |
| `calibracion` | por decil: prob media vs tasa real | gráfico de calibración |
| `deciles` | tasa, lift y captura acumulada por decil | tabla de la lámina "Qué tan bien prioriza" |
| `r2` | 1 − SSE/SST | monto |

### 5.7 `evento/exportar_submission.py` — línea por línea

```python
FORMATO = dict(
    columnas={"id_empresa": "id", "probabilidad": "prob"},  # nombre_en_entrega: nombre_en_predicciones
    orden=None,          # "probabilidad" si piden ordenar
    decimales=6,
    separador=",",
)
```
**Esto es lo ÚNICO que ajustas**, leyendo `entregas/README.md` del repo del evento.

```python
df = pd.read_csv(pred, dtype={"id": str})   # id como TEXTO: un RUC no pierde ceros ni gana ".0"
faltan = [...]                              # si pides una columna que no existe → se detiene y lista las disponibles
sub = df[...]; sub.columns = [...]          # selecciona y renombra
dup = sub[id_col].duplicated().sum()        # control: ids duplicados → se detiene
nulos = sub.isna().sum()                    # control: nulos → se detiene
sub.to_csv(destino, index=False, ...)       # sin índice de pandas
```
Columnas disponibles en `predicciones.csv`: `id, prob, valor_esperado, priorizado, monto_si_convierte, <zona>`.

**Ejemplos de FORMATO según lo que pidan:**
```python
# A) solo probabilidad
columnas={"id_empresa": "id", "prob_factoring": "prob"}
# B) probabilidad + lista
columnas={"id_empresa": "id", "prob_factoring": "prob", "priorizado": "priorizado"}
# C) todo
columnas={"id_empresa": "id", "prob_factoring": "prob", "monto_esperado": "valor_esperado", "priorizado": "priorizado"}
```
Si piden `priorizado` como "SI/NO" o un `ranking` 1..N → ver §16.

### 5.8 Kit simple: `scripts/5_entregar.py` (plan B, 40 líneas)

```python
d = te[["id", ZONA, RUBRO, "target"]].merge(prob.parquet, on="id")   # empresas a puntuar + prob
mediana_rubro = positivos.groupby(RUBRO).target_monto.median()       # monto típico por rubro (corte anterior)
d["monto"] = d[RUBRO].map(mediana_rubro).fillna(mediana_global)      # rubro sin historia → mediana global
d["valor"] = d.prob * d.monto                                         # valor esperado
k = int(CAPACIDAD * len(d))
exacto = {z: k*v/sum(CUPOS)}; cupo = {z: int(x)}                     # parte entera
for z in ...sorted por resto decimal...[: k - sum(cupo)]: cupo[z] += 1   # RESTO MAYOR: suma exacta k
for z, n in cupo.items(): nlargest(n, "valor") de la zona → priorizado = 1
controles: id único, prob en [0,1], sin vacíos, priorizadas == k
gráfico 5_rubros.png: % que toma factoring por rubro vs promedio
```
**Por qué mediana y no media:** 3 empresas gigantes no mueven la mediana (robusta).
**Diferencia con la avanzada:** aquí el monto es "mediana de su rubro" (simple, explicable); en la avanzada es un modelo (más preciso, menos explicable).

---

## 6. Probabilidad y estadística

Formato: **concepto → fórmula → ejemplo con nuestros números → cómo se interpreta → con qué se relaciona.**

### 6.1 Probabilidad y tasa
- **Concepto:** proporción de veces que ocurre algo. En los datos, una **tasa** (positivos / total) estima la probabilidad.
- **Ejemplo:** 1 524 de 8 000 empresas tomaron factoring → tasa base **19.1 %**.
- **Interpretación:** si llamo al azar, 19 de cada 100 convierten. **Todo se compara contra este número.**

### 6.2 Probabilidad condicional P(A | B)
- **Fórmula:** P(A|B) = P(A y B) / P(B).
- **Ejemplo:** P(convierte | priorizada) = 42 %; P(convierte) = 19.1 %.
- **Interpretación:** saber que la empresa está en la lista cambia la probabilidad. **Eso es lo que vende el modelo.**
- **Relación:** lift = P(A|B) / P(A) = 42/19.1 = **2.2x**.

### 6.3 Odds y log-odds (para la logística)
- **Fórmula:** odds = p / (1 − p); log-odds = ln(odds). La logística modela: log-odds = b₀ + b₁x₁ + …
- **Ejemplo:** p = 0.20 → odds = 0.25 ("1 a 4"). Con odds ratio 1.5 → odds 0.375 → p = 0.375/1.375 = **27.3 %**.
- **Interpretación:** un odds ratio de 1.5 **no** sube la probabilidad 50 %; sube las **chances** 50 %. De 20 % pasa a 27 %, no a 30 %. **Error típico frente al jurado.**

### 6.4 Valor esperado
- **Fórmula:** E[X] = Σ valor × probabilidad. Aquí: **valor esperado = P(convierte) × E[monto | convierte]**.
- **Ejemplo (probado):** empresa top: 0.70 × S/ 211 434 = **S/ 148 192**.
- **Interpretación:** "en promedio, llamar a esta empresa trae S/ 148 mil de financiamiento". Una empresa con prob 0.90 y monto S/ 20 000 vale **S/ 18 000** → va **después**. Por eso priorizamos por valor, no por probabilidad.
- **Relación:** requiere probabilidad **calibrada** (6.11). Si la prob está inflada, el valor esperado está inflado.

### 6.5 Distribución, sesgo y escala log
- **Concepto:** los montos tienen **cola larga** (pocas empresas enormes). La media se va hacia la cola.
- **Ejemplo:** 81 % de los montos objetivo son 0; entre los positivos, la asimetría es alta.
- **Interpretación:** trabajar en **log** (log1p) vuelve la distribución más simétrica; el modelo aprende "orden de magnitud".
- **Relación:** al volver de log a soles se subestima → **factor de Duan** (6.17).

### 6.6 Media vs mediana vs percentiles
- **Media:** sensible a extremos. **Mediana:** el del medio, robusta. **Percentil p99:** el valor bajo el cual está el 99 %.
- **Ejemplo:** montos 10, 12, 15, 20, 5 000 → media 1 011, mediana 15.
- **Interpretación:** para el "monto típico por rubro" usa **mediana**. Para el total de cartera usa **suma/media** (es plata real).
- **Relación:** winsorizar p1/p99 (regularizar.py) recorta extremos para la logística.

### 6.7 Correlación (Pearson vs Spearman)
- **Pearson:** relación **lineal**. **Spearman:** relación de **orden** (monótona), robusta a extremos.
- **Ejemplo:** el embudo saca una variable si Spearman > 0.9 con otra de más Gini (F5). Ventas y facturación total suelen estar muy correlacionadas.
- **Interpretación:** dos variables muy correlacionadas **se reparten la importancia** (permutación baja en ambas).
- ⚠ Correlación ≠ causalidad: "las que facturan más toman factoring" no significa que facturar cause factoring.

### 6.8 AUC y Gini
- **AUC:** probabilidad de que una empresa positiva al azar tenga mayor score que una negativa al azar. 0.5 = azar, 1 = perfecto. (Es la prueba de Mann-Whitney; así lo calcula `seleccion.auc_rapido`.)
- **Gini = 2·AUC − 1.** 0 = azar, 1 = perfecto.
- **Ejemplo:** Gini 0.31 → AUC 0.655: en 65.5 % de los pares (positiva, negativa) el modelo pone primero a la positiva.
- **Interpretación:** mide **orden**, no probabilidad. Si multiplicas todas las probs por 2, el Gini no cambia.
- **Relación:** Gini alto ≠ lista buena si hay desbalance severo → mira AUC-PR y captura.

### 6.9 KS (Kolmogorov-Smirnov)
- **Concepto:** máxima distancia entre la curva acumulada de scores de positivos y la de negativos.
- **Interpretación (banca):** < 0.2 débil, 0.2–0.4 aceptable, > 0.4 bueno (referencias usuales, no ley). Se reporta junto al Gini.
- **Cómo calcularlo si lo piden:** `from scipy.stats import ks_2samp; ks_2samp(p[y==1], p[y==0]).statistic`.

### 6.10 PSI (estabilidad)
- **Fórmula:** Σ (act% − ref%) · ln(act% / ref%) por tramos.
- **Umbrales:** < 0.10 estable · 0.10–0.25 vigilar · > 0.25 cambió.
- **Ejemplo (probado):** 11 variables fuera por PSI > 0.25 entre cortes (conteos **acumulados**: crecen solo porque pasa el tiempo).
- **Interpretación:** si la población cambió, lo aprendido puede no aplicar. Úsalo para el **monitoreo** del modelo en producción (plan de acción).

### 6.11 Calibración y Brier
- **Calibración:** si el modelo dice 30 %, ¿convierte ~30 %? **Brier** = promedio de (p − y)²; menor es mejor.
- **Ejemplo (probado):** logística prob media 0.187 vs tasa real 0.187 → calibrada. `lgbm_pesos` 0.211 vs 0.187 → **inflada**, y su Gini bajó de 0.26 a 0.19.
- **Interpretación:** reponderar clases **rompe la calibración** → rompe el valor esperado → rompe la priorización.

### 6.12 IV y WoE (lenguaje de riesgo)
- **WoE** de un tramo = ln(%buenos / %malos). **IV** = Σ (%buenos − %malos) · WoE.
- **Umbrales:** < 0.02 nada · 0.02–0.1 débil · 0.1–0.3 media · 0.3–0.5 fuerte · > 0.5 **sospechosa** (fuga).
- **Ejemplo (probado):** `total_operaciones_hist` IV 1.18 → REVISAR_FUGA.

### 6.13 Lift y captura
- **Lift decil 1** = tasa en el top 10 % / tasa base. **Captura@k** = % de los positivos que caen en el top k %.
- **Ejemplo:** lift D1 1.93x en el examen; captura@10 % ≈ 19 % (si lift es 1.9 en el 10 %, captura ≈ 1.9 × 10 %).
- **Relación:** captura@k = lift@k × k. Son la misma información dicha distinto.

### 6.14 AUC-PR (precisión-recall)
- **Piso = tasa base** (no 0.5). Con 0.4 % de positivos, Gini 0.70 pero AUC-PR 0.066 (experimento del repo).
- **Interpretación:** con desbalance severo, el Gini "se ve bien" aunque el top tenga pocos aciertos.

### 6.15 Error estándar e intervalo de confianza de una tasa
- **Fórmula:** EE = √(p(1−p)/n); IC 95 % ≈ p ± 1.96·EE.
- **Ejemplo:** priorizadas 42 % con n = 200 → EE = 3.5 pp → IC **35 %–49 %**. Base 19.1 % con n = 8 000 → IC 18.2 %–20.0 %.
- **Interpretación:** aun en el peor caso (35 %) la lista convierte **1.8x** la base → el hallazgo es **robusto**.
- **Úsalo** para no presentar "hallazgos" de rubros con 15 empresas (EE enorme).

### 6.16 Prueba de diferencia de proporciones (¿el rubro A convierte distinto?)
```python
from statsmodels.stats.proportion import proportions_ztest   # si no está: usar la fórmula
# z = (p1 - p2) / sqrt(p(1-p)(1/n1 + 1/n2)), con p = tasa combinada; |z| > 1.96 → diferencia significativa al 95 %
```
Regla rápida: si los IC 95 % de dos rubros **no se cruzan**, la diferencia es real.

### 6.17 Factor de Duan (smearing)
- **Concepto:** exp(promedio de log) < promedio real (desigualdad de Jensen). Duan corrige multiplicando por el promedio de exp(residuos).
- **Ejemplo del repo:** ×1.33. Sin él, el monto esperado total sale ~25 % bajo.

### 6.18 Tweedie
- Distribución para variables con **muchos ceros exactos + positivos con cola larga** (montos, siniestros). Permite una sola regresión.

### 6.19 Sobreajuste, varianza y validación
- **Sobreajuste:** el modelo memoriza train. Señal: Gini train ≫ Gini validación.
- **OOF (out-of-fold):** cada fila se predice con un modelo que no la vio → comparación justa.
- **Fuera de tiempo:** entrena con un corte anterior, examina con el actual → lo que hará el banco.
- **Ejemplo (probado):** OOF 0.289 vs examen 0.313 → sano (no se cayó).

### 6.20 EPV (positivos por variable)
- EPV = positivos / variables. < 10 → riesgo de sobreajuste → modelo simple. Probado: EPV 38 → OK.

### 6.21 Sesgo de selección
- **Concepto:** los datos no son al azar. Ej.: los **leads** fueron elegidos por ejecutivos → convierten más **porque** alguien los eligió.
- **Interpretación:** "el lead convierte 3x" no significa que generar leads cause conversión. Por eso se compara global vs por segmento.

### 6.22 Paradoja de Simpson
- Un efecto puede **invertirse** al separar por grupos. Ej.: una variable sube la prob en "con lead" y la baja en "sin lead"; en total parece no importar. El diagnóstico lo detecta ("cambia de SIGNO").

### 6.23 Regresión a la media
- Empresas con un mes excepcional tienden a volver a lo normal. Por eso se usan ventanas (3/6/12 meses) y no un solo mes.

### Mapa de relaciones entre conceptos

```
probabilidad ──► condicional ──► lift ──► captura@k
     │                              ▲
     ├──► odds ──► log-odds ──► logística ──► odds ratio ──► explicación
     │
     ├──► calibración (Brier) ──► valor esperado = P × monto ──► priorización
     │                                              ▲
     │                     monto: cola larga ──► log ──► Duan
     │
     └──► AUC (orden) ──► Gini ──► KS
                          │
     desbalance ──────────┴──► AUC-PR
     estabilidad: PSI ──► fuera de tiempo ──► examen honesto
     fuga: Gini/IV > 0.5 ──► revisar "¿existía el día de decidir?"
```

---

## 7. Métricas

### 7.1 Tabla maestra

| Métrica | Pregunta | Rango / bueno | Cambia si reponderas | Cuándo es la principal |
|---|---|---|---|---|
| Gini | ¿ordena bien? | 0–1; banca: 0.3 ok, 0.5 bueno, > 0.8 sospechoso | no (en teoría) | scoring, priorización |
| AUC | igual que Gini | 0.5–1 | no | si la piden así |
| KS | ¿separa positivos de negativos? | 0–1 | no | riesgo |
| AUC-PR | ¿el top tiene aciertos? | piso = tasa base | no | desbalance < 1 % |
| Lift D1 | ¿cuántas veces mejor que al azar? | > 1; 2x ya es bueno | no | **jurado de negocio** |
| Captura@k | % de conversiones en las k llamadas | — | no | capacidad limitada |
| Brier | ¿probabilidad real? | menor es mejor | **sí (empeora)** | valor esperado |
| R² | % de variación del monto explicada | 0–1 | — | monto |
| Spearman (monto) | ¿ordena bien los montos? | — | — | si importa el orden |
| F1 / recall / precisión | aciertos con un umbral | — | **sí (puede ayudar)** | solo si es la métrica oficial |
| Conversión de la lista | % de priorizadas que convierte | vs tasa base | — | **resultado de negocio** |
| Valor capturado | Σ montos reales de priorizadas | — | — | ROI |

### 7.2 Relaciones que debes poder explicar
1. **Gini ↔ AUC:** Gini = 2·AUC − 1. Mismo número, otra escala.
2. **Lift ↔ captura:** captura@k = lift@k × k.
3. **Gini ↔ lift:** más Gini suele dar más lift, pero el lift mira **solo el top**; dos modelos con igual Gini pueden tener distinto lift D1. Para priorizar, el lift del top es lo que importa.
4. **Calibración ↔ valor esperado:** sin calibración, el valor esperado no es plata real.
5. **Reponderar:** no sube el Gini (en el repo lo **bajó**: 0.26 → 0.19) e infla la probabilidad (0.211 vs 0.187).
6. **OOF ↔ examen:** si el examen cae mucho bajo el OOF → sobreajuste o fuga. Si son parecidos → modelo honesto.
7. **Gini de la lista ↔ conversión de la lista:** el jurado entiende "42 % vs 19 %", no "Gini 0.31".

### 7.3 "Si ves X → haces Y"

| Si ves… | Probablemente… | Haces… |
|---|---|---|
| Gini > 0.8 | fuga | revisa `seleccion_variables.csv` REVISAR_FUGA y la importancia por permutación |
| Gini examen ≪ OOF (p.ej. 0.40 vs 0.20) | sobreajuste o cambio de población | revisa PSI; pide a Sophia un modelo más simple |
| lift D1 < 1.3 | el modelo casi no ayuda | compara con `regla_1var`; quizá la regla es tan buena como el modelo → dilo |
| prob media ≠ tasa real | descalibrado | usa la logística o la probabilidad calibrada (`prob_calibrada`) |
| priorizadas ≠ K | cupos por redondeo o zona sin empresas | test §12; resto mayor |
| una zona con 0 priorizadas | nombre de zona no calza ('Lima' vs 'LIMA') | mira el aviso `⚠ CUPOS_ZONA` |
| permutación = 0 en todo | corriste con `--rapido` | corre sin `--rapido` |
| un rubro con lift 3x y 20 empresas | ruido | calcula el IC (6.15) antes de presentarlo |

---

## 8. Banca, factoring y riesgos

### 8.1 Factoring en 5 líneas
1. Una empresa (**proveedor / cedente**) vende a otra (**pagador / adquirente / deudor**) y emite una **factura** que cobrará en 30, 60 o 90 días.
2. Necesita la plata **hoy** → "vende" la factura a un **factor** (el banco).
3. El banco le adelanta un porcentaje (**aforo**, p.ej. 80–90 %), cobra una **tasa de descuento** + comisiones y, al vencimiento, **cobra al pagador**.
4. En Perú la factura electrónica tiene una copia **negociable** que se registra en **CAVALI**; el pagador debe dar conformidad (si no objeta en el plazo legal, se presume conforme). Marco: Ley 29623 y sus modificatorias.
5. El riesgo principal **no** es del proveedor sino del **pagador** (es quien paga al banco).

| Concepto | Qué es | Por qué te importa |
|---|---|---|
| Factoring **sin recurso** | si el pagador no paga, pierde el banco | el riesgo es 100 % del pagador |
| **con recurso** / descuento de facturas | si el pagador no paga, el proveedor devuelve | es más un préstamo |
| **Confirming** (factoring reverso) | lo inicia el **pagador grande** para sus proveedores | variable de red: si mi pagador ya hace confirming con BCP, yo convierto más (contagio) |
| Plazo | días entre emisión y pago | "variable estrella": a más plazo, más necesidad de liquidez |
| Aforo | % adelantado | — |
| Tasa de descuento | precio del dinero | ingreso del banco |

### 8.2 Por qué al BCP le importa (el negocio)
- **Crecimiento:** captar empresas que hoy hacen factoring **con otro banco** (migrar) o que **nunca** lo hicieron (habilitar).
- **Venta cruzada:** quien hace factoring usa más productos (cuentas, cash management, comercio exterior).
- **Principalidad / share of wallet:** que el BCP sea el banco principal de la empresa.
- **Costo comercial:** cada llamada/visita de un ejecutivo cuesta → **capacidad limitada** → priorizar.

**Dos listas, dos discursos:**

| Lista | Quién | Discurso | Variable que la detecta |
|---|---|---|---|
| **Migrar** | ya hace factoring en otro banco | "mejor tasa, más rápido, todo en un solo banco" | factoring con otro banco (lift medido 4.5 en el manual 14 h) |
| **Habilitar** | nunca lo hizo | "convierte tus facturas en caja hoy" | plazo largo, uso de línea alto, saldo cayendo |

### 8.3 Riesgos (lo que un jurado de banco pregunta)

| Riesgo | Qué es | Cómo se mide | Dónde aparece en tus datos |
|---|---|---|---|
| **Crédito** | que el pagador no pague | PD (probabilidad de default), calificación SBS | variables de buró, calificación |
| **Concentración** | depender de pocos pagadores | **HHI** (Σ participación²; 1 = un solo pagador) | `hhi_contraparte`, `top_contraparte_share` |
| **Fraude** | factura falsa o doble cesión | validaciones CAVALI/SUNAT | — (menciónalo como limitación) |
| **Dilución** | devoluciones/notas de crédito que bajan el valor de la factura | — | — |
| **Operativo** | errores de proceso | — | — |
| **Modelo** | que el modelo falle en producción | PSI, monitoreo, Gini mensual | plan de monitoreo |
| **Sesgo / equidad** | castigar zonas o rubros sin razón | comparar tasas por grupo | cupos por zona |

**Pérdida esperada (fórmula clásica de riesgo):** **EL = PD × LGD × EAD**
- PD: probabilidad de incumplimiento · LGD: % que se pierde si incumple · EAD: exposición en soles.
- Ej.: PD 2 %, LGD 45 %, EAD S/ 100 000 → EL = **S/ 900**.
- **Úsalo** si te preguntan "¿y el riesgo?": "nuestro modelo es comercial (propensión); antes del desembolso aplica la evaluación de riesgo del banco. Un siguiente paso es valor esperado **neto**: P × monto × margen − EL − costo de contacto".

**Calificación SBS del deudor (Perú):** Normal (0) · CPP – con problemas potenciales (1) · Deficiente (2) · Dudoso (3) · Pérdida (4). Es **ordinal**: se usa "la peor en 12 meses".

### 8.4 Indicadores de negocio que puedes calcular

| Indicador | Fórmula | Ejemplo |
|---|---|---|
| Conversión | convertidos / contactados | 42 % |
| Lift | conversión lista / conversión base | 2.2x |
| Conversiones extra | (conv_lista − conv_base) × K | (0.42 − 0.191) × 200 = **46 empresas más** con las mismas llamadas |
| Valor esperado de la lista | Σ prob × monto | S/ 17.7 M |
| Costo por conversión | costo_llamada × K / convertidos | con S/ 50 por llamada: 10 000/84 = S/ 119 vs 10 000/38 = S/ 263 al azar |
| ROI | (ingreso − costo) / costo | ingreso = monto × margen (pide el margen al mentor o di "supuesto") |

---

## 9. Decisiones de negocio

### 9.1 Escalera de decisión (de lo simple a lo complejo)

| Nivel | Regla | Cuándo | Riesgo |
|---|---|---|---|
| 0 | llamar al azar | línea base | — |
| 1 | ordenar por 1 variable (ventas) | "lo que haría un ejecutivo" | `regla_1var` |
| 2 | ordenar por **probabilidad** | métrica = Gini, sin monto | ignora el tamaño |
| 3 | ordenar por **valor esperado** = P × monto | hay monto | necesita prob calibrada |
| 4 | valor esperado + **cupos por zona** | el enunciado da cupos | voraz es óptimo |
| 5 | + mínimos/máximos (Pyme ≥ 60 %, rubro ≤ 30 %) | restricciones cruzadas | PuLP |
| 6 | + **costo por canal** (llamada, visita, correo) | hay datos por canal | un modelo por canal |
| 7 | valor **neto** = P × monto × margen − EL − costo | hay margen/riesgo | más supuestos |

**Regla:** sube un nivel **solo** si el enunciado lo pide o si lo mides y gana. Siempre muestra el nivel 1 como comparación.

### 9.2 ¿Probabilidad o valor esperado?

| Si la métrica oficial es… | Ordenas por | Por qué |
|---|---|---|
| Gini / AUC de la probabilidad | `prob` | te evalúan el orden de la probabilidad |
| Monto capturado / soles | `valor_esperado` | te evalúan plata |
| Ambas / no dicen | entregas `prob` en la columna de probabilidad y priorizas por `valor_esperado` | cumples la métrica y das valor de negocio — **explícalo** |
| Conversiones en el top K | `prob` | cuenta empresas, no soles |

### 9.3 Costo de una restricción (decisión muy valorada)
Mide cuánto valor pierdes por cumplir una regla y dilo:
```
Sin cupos: S/ X · Con cupos: S/ Y · Costo de la regla: S/ X − Y (Z %)
```
Probado: exigir 60 % Pyme costó **S/ 3 153** de S/ 17.7 M (0.02 %) → "la regla de inclusión Pyme casi no cuesta". Script en §16.3.

---

## 10. Hallazgos de negocio

### 10.1 Fórmula de un hallazgo (QUÉ → CUÁNTO → POR QUÉ → QUÉ HACER)

> **QUÉ:** Las empresas de Comercio toman factoring más que el resto.
> **CUÁNTO:** 25 % vs 18 % (1.4x), con 1 600 empresas (IC ± 2 pp).
> **POR QUÉ (hipótesis de negocio):** venden a plazo a cadenas grandes que pagan a 60–90 días.
> **QUÉ HACER:** campaña específica para Comercio con discurso de liquidez; meta: +X conversiones.

### 10.2 Dónde buscar hallazgos (en orden de rapidez)

| Fuente | Qué buscar | Archivo |
|---|---|---|
| Tasa por rubro | rubros por encima/debajo del promedio | `monitor.html` sección rubros; `groupby` |
| Tasa por zona | zonas subatendidas | idem |
| Importancia + sentido | "a más X, más/menos prob" | `importancia_variables.csv`, `coeficientes_logistica.csv` |
| Deciles | "el top 10 % convierte X veces" | `reporte_modelo.html` |
| Segmentos | con lead vs sin lead | `segmentos.csv` |
| Red | contagio: si mis vecinos hacen factoring, yo también | `__contagio`, `__grado_red` |
| Concentración | HHI alto = dependo de un pagador | `__hhi_contraparte` |
| Tendencia | empresas que crecen (>1) convierten más | `__tendencia` |
| Plazo | plazo de cobro largo = necesidad de caja | `__plazo_prom` |
| **Inesperado** | algo que contradice la intuición | **es el que más impresiona al jurado** |

### 10.3 Código para un hallazgo por grupo (con intervalo de confianza)
```python
import numpy as np, pandas as pd
t = pd.read_parquet(OUT_DIR / "tabla_modelo_t1.parquet")   # corte anterior: el target YA ocurrió
col = "maestrocli__rubro_economico"                          # o zona, segmento, tramo de ventas
g = t.groupby(col).target.agg(tasa="mean", n="size")
g["ee"] = np.sqrt(g.tasa * (1 - g.tasa) / g.n)
g["ic_bajo"], g["ic_alto"] = g.tasa - 1.96 * g.ee, g.tasa + 1.96 * g.ee
g["lift"] = g.tasa / t.target.mean()
print(g[g.n >= 100].sort_values("lift", ascending=False).round(3))
```
**Para variables numéricas, por tramos:**
```python
t["tramo"] = pd.qcut(t["maestrocli__ventas_anuales"], 5, labels=["Q1 chicas", "Q2", "Q3", "Q4", "Q5 grandes"])
print(t.groupby("tramo", observed=True).target.agg(["mean", "size"]))
```

### 10.4 Ejemplos de hallazgos y cómo explicarlos

| Hallazgo técnico | Cómo lo dices al jurado |
|---|---|
| `ventas_anuales` odds ratio 1.51 | "Las empresas más grandes tienen 50 % más chances de tomar factoring por cada salto de tamaño: tienen más facturas para adelantar." |
| `n_total` (operaciones previas) OR 1.62 | "Quien ya usó factoring lo vuelve a usar: es un hábito. La lista de 'migrar' es la más rentable." |
| `hhi_contraparte` alto → sube prob | "Las que dependen de 1–2 compradores grandes necesitan más liquidez: si su comprador paga a 90 días, se quedan sin caja." |
| `contagio` alto | "Si los otros proveedores de mi comprador ya hacen factoring con el BCP, yo también convierto más: hay que entrar por el comprador grande (confirming)." |
| PSI > 0.25 en conteos acumulados | "Las variables que solo crecen con el tiempo las sacamos: el modelo no debe premiar a una empresa por ser más vieja en los datos." |
| Lista 42 % vs 19 % | "Con las mismas 200 llamadas, el banco consigue 84 conversiones en vez de 38: **46 empresas más**." |
| Regla de 1 variable casi igual que el modelo | "Una regla simple ya funciona; el modelo agrega X %. Recomendamos empezar con la regla y escalar." (honestidad = puntos) |

---

## 11. Cronograma y tareas

### Viernes 13

| Hora | Tarea de Liz | Hecho cuando… |
|---|---|---|
| 14:30–15:30 | Escuchar el caso. Anotar en `trabajo/notas_liz.md`: formato de entrega (columnas, nombres, separador, decimales, orden), capacidad K, cupos, ¿piden monto?, ¿piden priorizado?, métrica | tienes las 8 respuestas de §18 |
| 15:30–16:00 | Planificación. Leer `entregas/README.md`. Ajustar `FORMATO` en `trabajo/exportar_submission.py` | FORMATO refleja el README |
| 16:00–17:00 | Con Nat: confirmar `CAPACIDAD`, `CUPOS_ZONA`, `COLUMNA_ZONA`, `SEGMENTO`, `TARGET["monto"]` en `config_evento.py` (Nat edita) | los nombres de columna existen en `perfil_columnas.csv` |
| 17:00–18:30 | Mientras Hellen/Kath corren el pipeline: abrir `monitor.html` → rubros, zonas, línea de tiempo. Primer borrador de 3 hipótesis de hallazgo | 3 hipótesis escritas |
| ~18:30 | Sophia corre `--rapido`. Tú: `exportar_submission.py` → `datafest.validar` → **test §12** | validador OK |
| 19:00–22:00 | **PRIMERA ENTREGA VÁLIDA** (aunque sea la regla). PR a `main` | `submission.csv` en `main` |
| 22:00–02:00 | Corrida completa (sin `--rapido`): importancia con permutación, segmentos, monto. Hallazgos con IC (§10.3). Priorización con restricciones si las hay (§16.3) | 3 hallazgos con número |
| noche | Láminas 4–7 de `presentacion/index.html` | láminas con números reales |
| cada hora | `git push` de tu rama `liz/entrega` | — |
| cada 2 h | PR a `main` y aviso a la integradora | — |

### Sábado 14

| Hora | Tarea | Hecho cuando… |
|---|---|---|
| hasta 09:00 | Última entrega con el modelo final | validador OK |
| 09:00 | **Congelado**. Solo: submission final, presentación, `docs/USO_DE_IA.md`, `docs/BITACORA_FUENTES.md` | — |
| 09:00–10:00 | Ensayo: tú explicas "a quiénes y por qué" en 90 s | cronometrado |
| 10:00 | Todo en `main` | revisado en github.com |
| 10:30 | Cierre | — |
| 11:30 | Evaluación técnica: §19 | — |

### Checklist de entrega (pégalo en tu notas_liz.md)
- [ ] `FORMATO` igual a `entregas/README.md` (nombres, orden de columnas, separador, decimales)
- [ ] `python -m datafest.validar` → OK
- [ ] test `check_liz.py` → todo `[OK]`
- [ ] número de filas = número de empresas a puntuar
- [ ] priorizadas = K exacto (si lo piden)
- [ ] `id` como texto, sin `.0`, sin ceros perdidos
- [ ] commit con tu cuenta, PR a `main`, visto en GitHub
- [ ] línea en `docs/USO_DE_IA.md` por cada uso de Copilot

---

## 12. Pruebas y tests

### 12.1 ¿Son necesarios? Sí, estos 4 niveles

| Nivel | Qué prueba | Cuándo |
|---|---|---|
| 1. Formato | el CSV cumple el contrato | **cada** entrega |
| 2. Coherencia | priorizadas tienen más prob, cupos suman, valores ≥ 0 | cada entrega |
| 3. Negocio | la lista convierte más que la base (en el corte con target) | cuando hay examen |
| 4. Robustez | cambiar capacidad/cupos cambia la lista como se espera | una vez |

### 12.2 Script de controles (probado) — `trabajo/check_liz.py`

```python
"""Controles de Liz antes de entregar. Uso: python trabajo/check_liz.py RUTA/salidas [K]"""
import json, sys
from pathlib import Path
import pandas as pd

S = Path(sys.argv[1]); M = S / "modelo"
p = pd.read_csv(M / "predicciones.csv", dtype={"id": str})
r = json.load(open(M / "resumen.json", encoding="utf-8"))
K = int(sys.argv[2]) if len(sys.argv) > 2 else r["prior"]["n"]
pruebas = {
    "1 fila por empresa": p.id.is_unique,
    "prob entre 0 y 1": p.prob.between(0, 1).all(),
    "sin vacíos en id/prob/priorizado": p[["id", "prob", "priorizado"]].notna().all().all(),
    f"priorizadas = {K}": int(p.priorizado.sum()) == K,
    "priorizado solo 0/1": set(p.priorizado.unique()) <= {0, 1},
    "valor_esperado >= 0": (p.valor_esperado >= 0).all(),
    "las priorizadas tienen más prob media que el resto":
        p.loc[p.priorizado == 1, "prob"].mean() > p.loc[p.priorizado == 0, "prob"].mean(),
}
for t, ok in pruebas.items():
    print(("[OK] " if ok else "[!!] ") + t)
pr = r["prior"]
if "conversion_priorizados" in pr:
    print(f"Frase: las {K} priorizadas convierten {pr['conversion_priorizados']:.1%} vs "
          f"{pr['conversion_base']:.1%} de la base ({pr['conversion_priorizados']/pr['conversion_base']:.1f}x)")
zona = [c for c in p.columns if c.endswith("zona")]
if zona:
    print(p[p.priorizado == 1].groupby(zona[0]).size().rename("priorizadas").to_string())
sys.exit(0 if all(pruebas.values()) else 1)
```
Uso en el evento: `python trabajo/check_liz.py ~/datafest_trabajo/salidas 500`
Salida real:
```
[OK] 1 fila por empresa
[OK] prob entre 0 y 1
...
Frase: las 200 priorizadas convierten 42.0% vs 19.1% de la base (2.2x)
CENTRO 20 · LIMA 100 · NORTE 36 · ORIENTE 10 · SUR 34
```
(Este archivo es código nuevo del evento: escríbelo tú en `trabajo/`, con Copilot si hace falta, y regístralo en USO_DE_IA.)

### 12.3 Pruebas manuales (5 minutos)

| Prueba | Cómo | Esperado |
|---|---|---|
| ids del banco | `set(submission.id) == set(lista_oficial.id)` | True |
| no hay `.0` | `submission.id.str.contains(r"\.0$").sum()` | 0 |
| capacidad | cambiar `CAPACIDAD` de 0.025 a 0.05 | priorizadas se duplican |
| cupos | sumar priorizadas por zona / K | ≈ porcentajes de `CUPOS_ZONA` |
| reproducible | correr dos veces | mismo CSV (la plantilla es determinística) |
| fuga provocada | (Sophia) meter una columna = target | Gini salta y el embudo la marca REVISAR_FUGA |

### 12.4 Prueba de negocio en el corte anterior
Si no hay target en el corte actual, valida la **regla de priorización** en `tabla_modelo_t1` (el target ya ocurrió): ¿las priorizadas convirtieron más? Eso es tu "backtest" de negocio.

---

## 13. Errores comunes y arreglos

### Paso: leer el enunciado
| Error | Arreglo |
|---|---|
| no anotar el formato exacto | pregunta en la sesión de dudas (§18) |
| asumir que piden probabilidad cuando piden ranking/monto | leer `entregas/README.md` dos veces, en voz alta con Nat |

### Paso: configurar
| Error | Síntoma | Arreglo |
|---|---|---|
| `COLUMNA_ZONA` con nombre crudo (`zona`) | sin cupos, sin aviso | debe ser el nombre en `tabla_modelo` (`maestrocli__zona`) |
| `CUPOS_ZONA` con 'Lima' | `⚠ CUPOS_ZONA: ['LIMA'] no existen` o zona vacía | valores reales en `perfil_columnas.csv` (top5) |
| `CAPACIDAD = 10` queriendo 10 % | prioriza 10 empresas | fracción < 1 = %; ≥ 1 = número |
| `SEGMENTO` con nombre crudo | segmentos no corre | nombre de `tabla_modelo` |
| `config_evento.py` deja `CUPOS_ZONA = None` | no hay cupos | Nat debe definirlos tras el bloque `if DATAFEST_PRUEBA` |

### Paso: importancia
| Error | Arreglo |
|---|---|
| permutación 0 en todo | correr sin `--rapido` |
| explicar SHAP de LightGBM cuando se entrega la logística | usar `coeficientes_logistica.csv` |
| leer `__te` o `==VALOR` solos | mirar la tasa real por categoría |
| presentar una variable en REVISAR_FUGA | nunca; preguntar si existía el día de decidir |

### Paso: monto
| Error | Arreglo |
|---|---|
| `TARGET` sin `monto=` → no hay `monto_si_convierte` | pedir a Nat agregar `monto="columna"` |
| monto en USD y PEN mezclado | revisar columna de moneda y `TIPO_CAMBIO` |
| presentar R² 0.12 como "malo" sin contexto | explicar ceros + R² condicional |

### Paso: priorizar
| Error | Arreglo |
|---|---|
| priorizadas ≠ K | resto mayor (§16.2) |
| aviso "faltan N empresas para llegar a la capacidad" | una zona no tiene suficientes: dilo como limitación o redistribuye |
| PuLP no instalado / falla | el voraz basta si solo hay cupos por zona |
| PuLP lento | ya poda a 20×K; si sigue lento, baja a 5×K en tu copia |

### Paso: exportar y validar
| Error | Síntoma | Arreglo |
|---|---|---|
| `predicciones.csv no tiene [...]` | se detiene | el mensaje lista columnas disponibles: corrige FORMATO |
| `ids duplicados` | se detiene | grano mal (Kath): una empresa en 2 filas |
| `Hay nulos` | se detiene | `monto_si_convierte` nulo si no hay monto: no lo pidas o rellena |
| validador rechaza el nombre de columna | — | copiar el nombre **literal** del README (mayúsculas, tildes) |
| filas de más/menos | — | ¿lista de evaluación? `EVALUAR` en config |
| ruta: `No existe .../predicciones.csv` | — | misma `--config` que usó Sophia |

### Paso: Git
| Error | Arreglo |
|---|---|
| subir `predicciones.csv` o parquet | nunca: viven en `~/datafest_trabajo/`. Solo `entregas/submission.csv` |
| `git push --force` | prohibido |
| editar `base_conocimiento/` | prohibido después de las 14:00 → todo en `trabajo/` |
| commit gigante al final | commits pequeños y frecuentes |

---

## 14. Escenarios

### 14.1 Escenarios de entrega

| Si el enunciado pide… | Haces | Archivo |
|---|---|---|
| solo `id, probabilidad` | FORMATO A | `exportar_submission.py` |
| `id, prob, priorizado` con K | FORMATO B + K en `CAPACIDAD` | config + exportar |
| `priorizado` como SI/NO | transformar (§16.1) | `exportar_submission.py` (copia en trabajo) |
| un `ranking` 1..N | `sub["ranking"] = sub.prob.rank(ascending=False, method="first").astype(int)` | idem |
| top K ordenado (solo K filas) | `sub = sub[sub.priorizado == 1].sort_values(...)` | idem |
| monto esperado | `"monto_esperado": "valor_esperado"` o `"monto_si_convierte"` (pregunta cuál) | FORMATO |
| probabilidad **y** monto con 2 métricas | entregar ambas columnas | FORMATO |
| lista de empresas a puntuar | `EVALUAR = dict(tabla=, id=)` | config (Nat) |
| separador `;` o decimales con coma | `separador=";"`; decimales: `sub.to_csv(..., decimal=",")` | FORMATO / copia |

### 14.2 Escenarios de capacidad y restricciones

| Si dan… | Método | Cómo |
|---|---|---|
| capacidad total (% o N) | voraz | `CAPACIDAD` |
| cupos por zona | voraz por zona (óptimo) | `CUPOS_ZONA`, `COLUMNA_ZONA` |
| cupos "proporcionales al tamaño" | calcula cupos = % de empresas por zona | `CUPOS_ZONA = df.zona.value_counts(normalize=True)*100` |
| mínimo Pyme / máximo por rubro | PuLP | `liz_prioriza.py` (§16.3) |
| tope por ejecutivo | PuLP (una restricción por ejecutivo) | §16.3 o kit `priorizar_restricciones.py` |
| presupuesto en soles | PuLP: Σ x·monto ≤ presupuesto | kit `priorizar_restricciones.py` (PRESUPUESTO) |
| prob mínima para llamar | filtrar `prob >= umbral` antes | kit (PROB_MINIMA) |
| excluir a quienes ya son clientes de factoring BCP | filtrar antes de priorizar | kit (EXCLUIR) |
| canales con costo distinto | valor neto por canal = prob_canal × monto − costo | MODELADO.md §5 |

### 14.3 Escenarios de métrica
Ver §9.2. Si la métrica tiene **umbral** (F1, recall): elegir el umbral que maximiza la métrica en las predicciones OOF; ahí sí puede convenir reponderar.

### 14.4 Escenarios de datos que te afectan

| Si… | Impacto en ti | Qué haces |
|---|---|---|
| no hay columna de zona | no hay cupos | priorizar solo por valor; decirlo |
| no hay monto | valor esperado = prob | priorizar por prob; monto típico por rubro como estimación (kit simple) |
| no hay flag de lead | sin segmentos | `SEGMENTO = None`; hallazgos por rubro/tamaño |
| el target viene hecho | — | nada; verificar ventana con Nat |
| no hay corte con target para examen | no hay "convierte 42 %" en el actual | usa el corte anterior (§12.4) y dilo |
| problema NO es factoring (fuga, mora, canal) | cambia el discurso | §8 (riesgos) y misma priorización |
| pronóstico (caso 2024 efectivo) | la fila es agencia×día | tu parte: traducir error a soles y plan de abastecimiento |
| canal óptimo (caso 2025) | un modelo por canal | asignar a cada cliente el canal con mayor valor neto |

### 14.5 Flujo por escenario (árbol)
```
¿Piden lista de priorizados?
├─ no → entrega id + prob → validar → hallazgos
└─ sí → ¿hay monto?
        ├─ sí → valor esperado = P × monto
        └─ no → prob
        → ¿restricciones?
             ├─ solo capacidad → voraz
             ├─ cupos por zona → voraz por zona (comparar PuLP)
             └─ cruzadas (Pyme, rubro, ejecutivo, presupuesto) → PuLP + medir costo de cada regla
        → check_liz.py → exportar → validar → PR
```

---

## 15. Qué agregar o quitar

| Nivel | Qué | Cuándo agregar | Cuándo quitar |
|---|---|---|---|
| 1 simple | frase lista vs base + tabla de deciles | siempre | nunca |
| 1 | tasa por rubro/zona con IC | siempre | si n < 100 |
| 2 | valor esperado | si hay monto | si piden solo conversiones |
| 2 | cupos por zona | si el enunciado los da | si no los da (no inventes reglas) |
| 3 | listas "migrar" vs "habilitar" | si hay variable de factoring con otro banco | si no se puede distinguir |
| 3 | explicación de 1 caso (top) | siempre en la presentación | — |
| 4 | costo de cada restricción | si hay restricciones | — |
| 4 | segmentos (1 vs varios modelos) | si hay `SEGMENTO` con ≥ 200 positivos | si no ganan |
| 5 | KS, curva de ganancia acumulada | si el jurado es de riesgo | — |
| 5 | valor neto (margen − EL − costo) | si dan margen o costo | si sería puro supuesto |
| 6 | plan de monitoreo (PSI mensual, Gini mensual) | lámina "Impacto y plan" | — |

**Qué QUITAR siempre:** variables en REVISAR_FUGA, hallazgos de grupos chicos, métricas que no sabes explicar, gráficos sin frase.

---

## 16. Cómo modificar archivos

**Regla de oro:** después de las 14:00 del viernes, **nada** se edita en `base_conocimiento/`. Se copia a `trabajo/` y se edita la copia, o se escribe un script nuevo en `trabajo/` que **importa** de la base.

### 16.1 Cambiar el formato de entrega (copia en `trabajo/`)
Agregar después de `sub.columns = ...` en `trabajo/exportar_submission.py`:
```python
# priorizado como SI/NO
if "priorizado" in sub: sub["priorizado"] = sub["priorizado"].map({1: "SI", 0: "NO"})
# ranking 1..N por probabilidad
# sub["ranking"] = sub["probabilidad"].rank(ascending=False, method="first").astype(int)
# solo el top K
# sub = sub[sub["priorizado"] == "SI"]
```

### 16.2 Cupos que sumen exacto (resto mayor)
```python
def cupos_exactos(K, cupos):
    tot = sum(cupos.values())
    exacto = {z: K * v / tot for z, v in cupos.items()}
    c = {z: int(x) for z, x in exacto.items()}
    for z in sorted(exacto, key=lambda z: exacto[z] - c[z], reverse=True)[: K - sum(c.values())]:
        c[z] += 1
    return c          # cupos_exactos(100, {"A": 1, "B": 1, "C": 1}) -> {'A': 34, 'B': 33, 'C': 33}
```
Pásalo a `priorizar.entero(..., cupos=c)` o al voraz como **números** (el voraz los vuelve a escalar: con cupos ya en número y su suma = K, `k = round(K*c/K) = c`).

### 16.3 Restricciones extra sin tocar la base — `trabajo/liz_prioriza.py` (probado)
```python
"""trabajo/liz_prioriza.py — priorización con restricciones EXTRA sin tocar base_conocimiento/.
Uso: python trabajo/liz_prioriza.py --config trabajo/config_evento.py
"""
import argparse, importlib.util, sys
from pathlib import Path
import pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); a = ap.parse_args()
s = importlib.util.spec_from_file_location("config", a.config); C = importlib.util.module_from_spec(s)
sys.modules["config"] = C; s.loader.exec_module(C)
from pipeline.modelado import priorizar            # se importa DESPUÉS de cargar la config

# ===== AJUSTES (cambiar según el enunciado) =====
COL_SEGMENTO = "maestrocli__segmento"   # columna de tabla_modelo con el segmento
VALOR_PYME = "PYME"
MIN_PYME = 0.60                         # al menos 60% de la lista debe ser Pyme (None = sin regla)
# ================================================

pred = pd.read_csv(Path(C.OUT_DIR) / "modelo" / "predicciones.csv", dtype={"id": str})
tm = pd.read_parquet(Path(C.OUT_DIR) / "tabla_modelo.parquet")
tm["id"] = tm["id"].astype(str)
d = pred.drop(columns="priorizado").merge(tm[["id", COL_SEGMENTO]], on="id", how="left")
d["es_pyme"] = (d[COL_SEGMENTO].astype("string") == VALOR_PYME).astype(int)
zona = C.COLUMNA_ZONA if C.COLUMNA_ZONA in d else None
extra = [("es_pyme", MIN_PYME)] if MIN_PYME else None
sin, _ = priorizar.entero(d, zona=zona, cupos=C.CUPOS_ZONA)
con, estado = priorizar.entero(d, zona=zona, cupos=C.CUPOS_ZONA, restricciones_extra=extra)
for nombre, x in (("sin regla Pyme", sin), ("con regla Pyme", con)):
    p = x[x.priorizado == 1]
    print(f"{nombre:<15} n={len(p)}  valor={p.valor_esperado.sum():,.0f}  %pyme={p.es_pyme.mean():.0%}")
costo = sin.loc[sin.priorizado == 1, "valor_esperado"].sum() - con.loc[con.priorizado == 1, "valor_esperado"].sum()
print(f"Estado {estado}. Costo de la regla Pyme: {costo:,.0f} en valor esperado")
con.to_csv(Path(C.OUT_DIR) / "modelo" / "predicciones_restricciones.csv", index=False)
```
Salida real:
```
sin regla Pyme  n=200  valor=17,718,370  %pyme=58%
con regla Pyme  n=200  valor=17,715,217  %pyme=60%
Estado Optimal. Costo de la regla Pyme: 3,153 en valor esperado
```
Luego, en `exportar_submission.py` (copia), cambia el archivo leído a `predicciones_restricciones.csv`.
**Otras restricciones** con el mismo patrón: crea una columna binaria (`es_rubro_x`, `es_nuevo`) y agrégala a `extra` como `(columna, mínimo_fracción)`. Para **máximos** (p.ej. rubro ≤ 30 %) usa el kit `priorizar_restricciones.py` (MAX_POR_RUBRO) o pide a Copilot "agregar una restricción ≤ en PuLP".

### 16.4 Hacerlo legible e interpretable
- Nombres de columnas en la entrega: los del enunciado.
- En tus scripts: un bloque `AJUSTES` arriba, comentarios con el **porqué**, prints con `[OK]/[!!]`.
- Cada salida CSV con columnas en español claro (`prob`, `valor_esperado`, `priorizado`).
- Redondeo: probabilidades 4–6 decimales; soles sin decimales en la presentación.

---

## 17. Preguntas para Copilot

Reglas: **un chat nuevo por tarea**, nunca pegues datos ni el enunciado, describe columnas por nombre y tipo. Anota cada uso en `docs/USO_DE_IA.md` (hora, quién, tarea, qué pediste, qué hiciste con la respuesta).

| Paso | Pregunta para Copilot |
|---|---|
| formato | "Tengo un DataFrame con columnas id (texto), prob (float), priorizado (0/1). Necesito un CSV con columnas X, Y, Z, separador ';', priorizado como 'SI'/'NO'. Escribe el código pandas." |
| validar | "El validador dice: '<mensaje>'. ¿Qué suele significar este error en un CSV de entrega?" |
| ids | "¿Cómo detecto en pandas ids que terminan en '.0' o que perdieron ceros a la izquierda?" |
| cupos | "Escribe una función que reparta K entre zonas según porcentajes y que la suma sea exactamente K (método del resto mayor)." |
| PuLP | "En PuLP con variables binarias x_i, ¿cómo agrego la restricción 'como máximo 30 % de los seleccionados pueden ser del mismo rubro'?" |
| PuLP | "¿Cómo agrego un tope de 15 empresas por ejecutivo en un modelo PuLP binario?" |
| hallazgo | "Dada una columna categórica y un target 0/1, calcula tasa, n, intervalo de confianza 95 % y lift por categoría." |
| hallazgo | "¿Cómo pruebo si la diferencia entre dos tasas de conversión es estadísticamente significativa?" |
| importancia | "Explícame la diferencia entre importancia por gain, por permutación y SHAP en LightGBM, en 5 líneas." |
| logística | "Si un coeficiente estandarizado de una regresión logística es 0.41, ¿cómo lo explico en términos de odds ratio a un público de negocio?" |
| monto | "¿Por qué al predecir en log1p y volver con expm1 se subestima la media? ¿Qué es el factor de Duan?" |
| gráfico | "Escribe un gráfico de barras horizontales en matplotlib de tasa por rubro con una línea vertical en el promedio." |
| deciles | "Dado y (0/1) y p (score), calcula por decil: n, positivos, tasa, lift y captura acumulada." |
| KS | "¿Cómo calculo el estadístico KS entre scores de positivos y negativos con scipy?" |
| presentación | "Propón 3 formas de decir 'la lista convierte 2.2 veces más que la base' para un gerente comercial." (luego reescríbelo tú) |
| error Python | "Me sale KeyError: 'maestrocli__zona' al hacer groupby. ¿Qué reviso?" |
| git | "¿Cómo creo una rama, hago commit solo de entregas/submission.csv y abro un PR?" |

**Prompt útil para que Copilot use el criterio del equipo:** "Lee `base_conocimiento/plantilla/docs/MODELADO.md` sección 6 y explícame cuándo usar dos partes vs Tweedie."

---

## 18. Preguntas al organizador

Hazlas en la sesión de dudas (14:30) o al mentor en la primera hora. Las **8 obligatorias** para ti:

1. ¿Cuál es el formato exacto de `submission.csv` (columnas, nombres, orden, separador, decimales)?
2. ¿Se puntúan **todas** las empresas o una lista específica? ¿Nos dan esa lista?
3. ¿Piden una columna de priorizados? ¿Cuántas exactamente (K)? ¿K es un % o un número?
4. ¿Hay cupos por zona/segmento/ejecutivo? ¿Son obligatorios o referenciales?
5. ¿La métrica evalúa la probabilidad (Gini/AUC), el monto (R², error) o la lista (conversiones/soles en el top K)?
6. ¿El monto a predecir es el financiado, el facturado o el desembolsado? ¿En soles?
7. ¿Las operaciones anuladas cuentan? ¿Solo factoring BCP o también otros bancos?
8. ¿Un cliente que **ya** hace factoring con el BCP se puede priorizar o se excluye?

Opcionales (dan puntos de negocio):
- ¿Cuál es el costo aproximado de un contacto comercial? ¿y el margen típico del factoring?
- ¿Prefieren priorizar Pyme o hay alguna política de inclusión?
- ¿Las zonas tienen el mismo número de ejecutivos?
- ¿La columna X (con nombre ambiguo, p.ej. `estado_actual`) está al corte o es de hoy?

---

## 19. Jurado

### 19.1 Qué espera el jurado (lo que pesan)
1. **Entender el negocio:** qué es factoring, por qué importa al BCP, migrar vs habilitar.
2. **Rigor:** sin fuga, validación fuera de tiempo, comparación con línea base.
3. **Decisión accionable:** a quién llamar, cuántos, con qué discurso, cuánto vale.
4. **Hallazgos** con número y acción (y uno inesperado).
5. **Honestidad:** limitaciones dichas por ustedes antes de que pregunten.
6. **Que cualquiera del equipo explique cualquier parte.**

### 19.2 Preguntas que te tocan a ti (respuesta = qué hicimos + por qué + número)

| Pregunta | Respuesta modelo |
|---|---|
| ¿Por qué esas empresas y no otras? | "Ordenamos por valor esperado: probabilidad × monto esperado. Una empresa con 70 % y S/ 211 mil vale S/ 148 mil; una con 90 % y S/ 20 mil vale S/ 18 mil. Respetamos los cupos por zona." |
| ¿Cuál es el impacto? | "Las 200 priorizadas convierten 42 % contra 19 % de la base: 2.2 veces. Con las mismas llamadas son 46 empresas más." |
| ¿Es casualidad? | "Con 200 empresas el intervalo al 95 % es 35–49 %; incluso el peor caso es 1.8 veces la base." |
| ¿Qué variables importan? | "Tamaño (ventas), historia de factoring y rubro. Lo medimos de tres formas: gain, permutación en datos no vistos y SHAP; coinciden." |
| ¿Por qué explican con la logística? | "Porque es el modelo que entregamos. Explicar otro modelo sería engañoso." |
| ¿Qué es un odds ratio de 1.5? | "Las chances se multiplican por 1.5 por cada desviación estándar; de 20 % pasa a 27 %, no a 30 %." |
| ¿Cómo calcularon el monto? | "Dos partes: ¿convierte? × ¿cuánto si convierte? (en log, corregido con Duan). Lo comparamos con una regresión directa: empataron; elegimos dos partes porque se explica mejor." |
| ¿Por qué voraz y no optimización? | "Con una sola regla por zona, ordenar y llenar cupos es óptimo. Lo comprobamos con PuLP: mismo valor." |
| ¿Cuánto cuesta cumplir la regla Pyme? | "S/ 3 mil de S/ 17.7 millones: casi nada." |
| ¿Uno o varios modelos? | "Medimos global vs uno por segmento; el global ganó en ambos, así que un modelo con el segmento como variable." |
| ¿Y el riesgo de crédito? | "Nuestro modelo es de propensión comercial. Antes de desembolsar aplica la evaluación de riesgo del banco; el siguiente paso es valor neto: P × monto × margen − pérdida esperada − costo." |
| ¿Qué harían mañana? | "Piloto: 2 grupos (lista vs azar), medir conversión a 3 meses, monitorear PSI mensual y reentrenar trimestral." |
| ¿Qué no hicieron? | "No tenemos costo por contacto ni margen; usamos supuestos. No medimos canal." |

### 19.3 Limitaciones que debes decir tú primero
- Monto: R² en soles bajo porque la mayoría no convierte; ordena bien entre quienes convierten.
- Conteos acumulados sacados por PSI (sesgo por antigüedad en datos).
- Lead = sesgo de selección (lo eligió un ejecutivo).
- Supuestos de costo y margen.

---

## 20. Lenguaje de negocio

| En vez de… | Di… |
|---|---|
| "Gini 0.31" | "ordena bastante mejor que el azar y mejor que la regla simple" |
| "lift D1 1.93" | "el 10 % de arriba convierte casi el doble que el promedio" |
| "captura@10 % = 19 %" | "con 1 de cada 10 llamadas encontramos 1 de cada 5 conversiones" |
| "valor esperado" | "soles que esperamos ganar por cada llamada" |
| "odds ratio 1.6" | "60 % más chances" |
| "PSI > 0.25" | "la variable cambió con el tiempo; no es confiable" |
| "fuga" | "información que no existía el día de decidir" |
| "OOF" | "medido en empresas que el modelo no vio" |
| "fuera de tiempo" | "como si lo hubiéramos usado hace 6 meses y mirado qué pasó" |
| "HHI alto" | "depende de pocos compradores" |
| "contagio" | "sus socios comerciales ya hacen factoring" |
| "restricción en PuLP" | "regla comercial" |

**Estructura de la lámina "A quiénes priorizamos":** 1 número grande (2.2x) · 1 tabla por zona · 1 empresa ejemplo con sus 3 razones · 1 frase de acción.

**Estructura de la lámina "Impacto y plan":** conversiones extra · soles esperados · piloto A/B · monitoreo · siguiente versión.

---

## 21. Glosario

| Término | Significado |
|---|---|
| Aforo | % del valor de la factura que el banco adelanta |
| AUC | probabilidad de que un positivo tenga mayor score que un negativo |
| AUC-PR | área bajo precisión-recall; piso = tasa base |
| Brier | error cuadrático de la probabilidad |
| Calibración | que la probabilidad predicha coincida con la tasa real |
| Captura@k | % de positivos en el top k % |
| CAVALI | registro donde se anotan las facturas negociables en Perú |
| Cedente / proveedor | quien vende la factura |
| Confirming | factoring iniciado por el pagador para sus proveedores |
| Corte | "día de decidir": variables antes, target después |
| CPP | calificación SBS "con problemas potenciales" |
| Decil | 10 % de la lista ordenada |
| Duan | factor que corrige el sesgo al volver de log |
| EAD / LGD / PD | exposición / pérdida dado default / probabilidad de default |
| EL | pérdida esperada = PD × LGD × EAD |
| EPV | positivos por variable |
| Fuga (leakage) | usar información posterior al corte |
| Gini | 2·AUC − 1 |
| Grano | qué representa una fila |
| HHI | índice de concentración (Σ participación²) |
| IV / WoE | poder predictivo en lenguaje de riesgo |
| KS | máxima separación entre distribuciones de score |
| Lead | empresa marcada por comercial como oportunidad |
| Lift | tasa del grupo / tasa base |
| Logística | modelo lineal en log-odds |
| LightGBM | árboles de boosting rápidos |
| Odds / odds ratio | p/(1−p) / cociente de odds |
| OOF | predicción fuera de pliegue |
| Pagador / adquirente | quien debe pagar la factura |
| Parsimonia | preferir lo simple si rinde igual |
| Permutación | caída del Gini al desordenar una variable |
| PSI | índice de estabilidad de población |
| PuLP / HiGHS | librería / solver de programación entera |
| R² | % de variación explicada |
| Recurso (con/sin) | si el proveedor responde si el pagador no paga |
| SHAP | aporte de cada variable a una predicción |
| Share of wallet | % del negocio del cliente que tiene el banco |
| Spearman | correlación de orden |
| Target | lo que se predice (1 = tomó factoring en la ventana) |
| Tweedie | distribución para ceros + cola larga |
| Valor esperado | probabilidad × monto |
| Voraz (greedy) | ordenar y tomar mientras se cumplan reglas |
| Winsorizar | recortar extremos a p1/p99 |

---

## 22. Hoja de bolsillo

```
MI PREGUNTA:  ¿por qué predice y a quién llamamos?
RECIBO:       predicciones.csv (id, prob, valor_esperado, priorizado, monto_si_convierte, zona)
ENTREGO:      entregas/submission.csv  →  python -m datafest.validar  →  PR a main

COMANDOS
  python trabajo/exportar_submission.py --config trabajo/config_evento.py
  python trabajo/check_liz.py ~/datafest_trabajo/salidas K
  python trabajo/liz_prioriza.py --config trabajo/config_evento.py   (si hay reglas extra)

ORDEN DE DECISIÓN
  prob → valor esperado (P × monto) → cupos por zona (voraz) → reglas cruzadas (PuLP) → costo de cada regla

NÚMEROS QUE SIEMPRE LLEVO
  tasa base · conversión de la lista · lift · conversiones extra · IC 95 % · valor esperado total · costo de reglas

FÓRMULAS
  Gini = 2·AUC − 1        lift = tasa_lista / tasa_base        captura@k = lift@k × k
  odds = p/(1−p)          OR 1.5 sobre 20 % → 27 %             EE = √(p(1−p)/n), IC = p ± 1.96·EE
  EL = PD × LGD × EAD     valor esperado = P × E[monto | convierte]

ALARMAS
  Gini > 0.8 · variable > 0.5 · priorizadas ≠ K · ids con ".0" · permutación 0 (= --rapido)
  coeficiente __te solo · hallazgo con n < 100 · variable en REVISAR_FUGA en la historia

FRASE
  "No llamamos a los de mayor probabilidad: llamamos a los de mayor valor esperado, respetando
   los cupos por zona. Con las mismas llamadas, la lista convierte 2.2 veces más que la base."
```
