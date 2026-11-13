# ¿Qué hacer si…? · casos inesperados y cómo adaptar los scripts

## 1. Los datos vienen distintos

| Si… | Cambio |
| --- | --- |
| CSV separado por `;` | paso 1: `read_csv('{archivo}', all_varchar=true, delim=';')` |
| Excel con título arriba | paso 1: `pd.read_excel(archivo, sheet_name=None, dtype=str, skiprows=2)` |
| Archivo `.txt` o `.json` | paso 1: agregar `elif archivo.suffix == ".txt": ... read_csv(...)`; JSON: `read_json_auto('{archivo}')` |
| Llave con otro nombre (`nro_doc`) | paso 1: agregarla a la condición `c.startswith((...))`; `ajustes.ID` |
| Fechas mes/día | paso 1: poner `'%m/%d/%Y'` primero en `fecha()` |
| Un archivo por mes (`ventas_ene.csv`, `ventas_feb.csv`) | unirlos: `read_csv('datos/ventas_*.csv', union_by_name=true, all_varchar=true)` |
| Una tabla de perfil más (1 fila por empresa) | paso 3, bloque a: `base = base.merge(perfil.rename(columns={"cod_cliente": "id"}), on="id", how="left")` |
| Una tabla ancha por meses (`saldo_202401...`) | usar solo meses anteriores al corte y renombrarlos "hace 1 mes", "hace 2"... |

## 2. El target es distinto

| Si el enunciado… | Cambio |
| --- | --- |
| Da el target hecho (columna `compro` SI/NO) | paso 3: `base["target"] = (base.compro == "SI").astype(int)` y no construirlo. Validación: solo los 5 pliegues del paso 4 |
| Da `train.csv` (con target) y `test.csv` (sin target) | `entrena` = train, `predice` = test; mismas variables para ambos; sin corte anterior |
| Pide predecir un MONTO | paso 4: `LGBMRegressor` y `Ridge`; métrica `r2_score`; entrenar en soles (en log dio R² negativo) |
| Pide probabilidad Y monto | dos modelos: clasificador (prob) × regresor entrenado solo con los que convirtieron |
| Otro producto (leasing, crédito) o fuga de clientes | cambiar `TARGET_TABLA` y `TARGET_FILTRO` |
| No dice el corte | último mes con datos completos en TODAS las tablas, menos el horizonte |
| El target es muy raro (< 2%) | reportar AUC-PR además del Gini; no reponderar |
| La métrica oficial no es Gini | `extra/metricas.py` + `python extra/mas_modelos.py <metrica>` · apunte 14 |
| Pocos positivos y hay varios meses de historia | `temporal/varios_cortes.py` (apila cortes sin fuga) · apunte 17 |

## 3. La entrega es distinta

| Si piden… | Cambio |
| --- | --- |
| Otros nombres de columnas | `ajustes.ENTREGA` |
| Solo probabilidad, sin lista | borrar los pasos 2–3 de `5_entregar.py` |
| Solo empresas con lead / sin lead | filtrar `d` antes de priorizar |
| Sin cupos por zona | `d.loc[d.nlargest(k, "valor").index, "priorizado"] = 1` |
| Un mínimo por rubro | primero llenar el mínimo de cada rubro con `nlargest`, luego el resto global |
| Varias reglas a la vez (presupuesto, ejecutivos, máximos) | `optimizacion/priorizar_restricciones.py` · apunte 18 |
| Un decil o un puntaje en vez de probabilidad | `pd.qcut(d.prob.rank(method="first"), 10, labels=range(10, 0, -1))` |

## 4. El reto es de otro tipo

**Pronóstico** (ej. efectivo por agencia y día, como el caso 2024):
- La fila es "agencia × día", no "empresa".
- Variables: rezagos y promedios que terminen **al menos un horizonte atrás** (si piden 28 días, el valor de
  "ayer" no existe dentro del horizonte: usar hace 28, 35, 42 días), día de la semana, quincena, fin de mes, feriado.
- Validación por bloques de tiempo (backtest en 3 ventanas). **Nunca** pliegues aleatorios.
- Métrica típica: WAPE o MAE (MAPE explota con ceros).
- Código listo: `scripts/temporal/pronostico.py` (6 métodos, incluido ARIMA) · apunte `17_series_de_tiempo.md`.

**Segmentación** (sin target):
- Variables escaladas → `KMeans(n_clusters=4..6)` → describir cada grupo con sus promedios y ponerle un nombre de
  negocio ("pymes comerciales en crecimiento").

**Red pagador–proveedor**:
- Variables de contagio: % de los pagadores de la empresa cuyos otros proveedores ya hicieron factoring antes del
  corte.

## 5. Algo sale mal

Si lo que falla es la **lectura o limpieza**: `extra/limpieza_pandas.py` · apunte 16.


| Síntoma | Causa probable | Qué hacer |
| --- | --- | --- |
| Gini > 0.8 | fuga | `05_fugas_y_validacion.md`, Q1–Q3 |
| El modelo no le gana a la regla | ruido o pocas filas | menos variables, quedarse con la logística |
| Gini cerca de 0 | llaves rotas o target mal construido | Q5–Q6 |
| Tasa base 0% o 100% | filtro del target mal escrito, o ventana sin datos | revisar `TARGET_FILTRO` y la línea de tiempo |
| Todas las variables de eventos en 0 | ids distintos entre tablas | Q5: ¿calzan las llaves? |
| El script tarda demasiado | archivo grande en pandas | `10_eficiencia_y_tiempo.md` |
