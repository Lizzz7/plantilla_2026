# Léeme primero · cómo usar este kit en 3 horas

## Qué hay

```
kit_datafest/
├── scripts/                 5 scripts cortos (≈430 líneas en total) + ajustes.py
│   ├── ajustes.py           lo único que se cambia con los datos del reto (Nat)
│   ├── 1_leer_limpiar.py    Hellen  · leer todo como texto, decidir tipos, limpiar
│   ├── 2_revisar.py         Nat     · ¿los nombres existen? tasa base, línea de tiempo
│   ├── 3_variables.py       Kath    · 1 fila por empresa, solo pasado, prueba de fuga
│   ├── 4_modelo.py          Sophia  · regla vs logística vs LightGBM, misma validación
│   ├── 5_entregar.py        Liz     · valor esperado, cupos por zona, CSV + controles
│   ├── extra/               PLAN B y ampliaciones (no hacen falta para el flujo básico)
│   │   ├── metricas.py           todas las métricas (AUC-PR, KS, F1, Brier, MAE, WAPE...)
│   │   ├── mas_modelos.py        7 modelos + ensamble, misma validación, métrica a elección
│   │   ├── uno_o_varios.py       ¿un modelo global o uno por zona/segmento? (lo mide)
│   │   └── limpieza_pandas.py    limpieza alternativa si DuckDB falla + diagnóstico por columna
│   ├── temporal/            si el reto es en el tiempo
│   │   ├── datos_temporales.py   datos de práctica (retiros diarios por agencia)
│   │   ├── pronostico.py         naive, Holt-Winters, SARIMA, LightGBM con rezagos + backtest
│   │   ├── arima_paso_a_paso.py  ARIMA explicado (ADF, ACF/PACF, AIC, residuos, intervalos)
│   │   └── varios_cortes.py      clasificación apilando varios cortes, sin fugas
│   └── optimizacion/
│       └── priorizar_restricciones.py  "el 10%" con cupos, mínimos, presupuesto, ejecutivos
├── apuntes/                 estos .md
└── papers/                  referencias con enlace y resumen (factoring, modelos, fugas, series)
```

Correrlos (desde `scripts/`, con los datos en `scripts/datos/`):

```bash
python 1_leer_limpiar.py && python 2_revisar.py && python 3_variables.py && python 4_modelo.py && python 5_entregar.py
```

Resultado con los datos de práctica (5 000 empresas): Gini **0.292** en el periodo que el modelo no vio
(una regla simple da 0.260), y las 125 empresas priorizadas convierten **52%** contra 19.9% de la base (2.6×).
Son menos variables que en las plantillas grandes y, aun así, mide más: menos ruido.

## Plan de 3 horas

| Tiempo | Todas | Detalle |
| --- | --- | --- |
| 0:00–0:20 | Correr los 5 scripts y abrir los 7 gráficos de `salidas/` | ver el flujo completo funcionando |
| 0:20–0:35 | Leer `02_flujo_y_conceptos.md` | corte, horizonte, target, fuga, Gini: el idioma común |
| 0:35–1:35 | Cada una: SU script + `13_scripts_explicados.md` (su sección) + su apunte | ver tabla de abajo |
| 1:35–2:15 | Cada una **reescribe su script con sus palabras** y lo corre | si funciona igual, ya es suyo |
| 2:15–2:45 | Ronda: cada una explica su paso en 5 min sin mirar el código | las demás preguntan con `12_jurado.md` |
| 2:45–3:00 | Corrida completa cronometrada + `11_que_hacer_si.md` | el plan B si algo sale distinto |

| Persona | Script | Apuntes clave |
| --- | --- | --- |
| Nat | `ajustes.py`, `2_revisar.py` | 01 factoring · 02 flujo · 11 qué hacer si · 12 jurado |
| Hellen | `1_leer_limpiar.py` | 06 limpieza · 10 eficiencia · 09 funciones |
| Kath | `3_variables.py` | 07 variables · 05 fugas · 09 funciones |
| Sophia | `4_modelo.py` | **03 métricas · 04 modelos · 05 fugas y validación** |
| Liz | `5_entregar.py` | 08 priorización · 01 factoring · 12 jurado |

**Después de las 3 horas (o el viernes antes de las 14:00), según rol:**

| Persona | Plan B / ampliación | Apunte |
| --- | --- | --- |
| Hellen | `extra/limpieza_pandas.py` | 16 si la limpieza falla |
| Kath | `temporal/varios_cortes.py`, `temporal/pronostico.py` | 17 series de tiempo |
| Sophia | `extra/metricas.py`, `extra/mas_modelos.py`, `temporal/arima_paso_a_paso.py` | 14 otras métricas · 15 más modelos · 17 |
| Liz | `optimizacion/priorizar_restricciones.py` | 18 optimización con restricciones |
| Nat | `papers/` (elige 1 cita por decisión para la exposición) | `papers/00_INDICE.md` |

Instalar lo extra: `pip install statsmodels xgboost catboost "pulp<3"` (si algo no se instala, esos modelos se saltan solos).

## Índice de apuntes

| Archivo | De qué trata |
| --- | --- |
| `01_factoring.md` | el negocio: qué es, por qué una empresa lo usa, qué variables lo predicen |
| `02_flujo_y_conceptos.md` | del archivo al CSV, y los 10 conceptos que todas deben saber |
| `03_metricas.md` | Gini, AUC, AUC-PR, KS, lift, captura, Brier, R², MAE: qué miden, cómo leerlas, cuál usar |
| `04_modelos.md` | regla, logística, árbol, Random Forest, LightGBM, XGBoost, CatBoost: cuándo y por qué |
| `05_fugas_y_validacion.md` | cómo nace una fuga, cómo detectarla, consultas, cómo corregir |
| `06_limpieza_casos.md` | cada tipo de dato sucio y su arreglo |
| `07_variables.md` | recetas de variables (RFM, ventanas, tendencia, ratios, concentración) |
| `08_priorizacion_y_entrega.md` | valor esperado, cupos, capacidad, controles del CSV |
| `09_funciones_clave.md` | chuleta de pandas, DuckDB SQL y scikit-learn que usamos |
| `10_eficiencia_y_tiempo.md` | datos grandes, memoria, qué hacer primero si falta tiempo |
| `11_que_hacer_si.md` | casos inesperados: train/test, monto, sin fechas, pronóstico, desbalance |
| `12_jurado.md` | preguntas probables y respuestas |
| `13_scripts_explicados.md` | los 5 scripts, bloque por bloque |
| `14_otras_metricas.md` | si la métrica no es Gini: cuál usar, cómo cambiarla, trampas |
| `15_mas_modelos.md` | 7 modelos comparados, cuándo usar cada uno, parámetros seguros |
| `16_si_la_limpieza_falla.md` | escalera de soluciones y plan B en pandas |
| `17_series_de_tiempo.md` | backtest, naive, Holt-Winters, ARIMA/SARIMA, LightGBM con rezagos, varios cortes |
| `18_optimizacion_restricciones.md` | priorizar con capacidad, cupos, mínimos, presupuesto y ejecutivos |
| `19_modelos_casos.md` | 11 casos (propensión, monto, fuga, riesgo, pronóstico, segmentación...): modelo, métrica y script |
| `20_uno_o_varios_modelos.md` | varios modelos en paralelo, ensamble, uno por zona vs global, dos etapas |

Mapa del equipo (rol, script, contratos entre pasos, horario del evento): **`../GLOBAL_EQUIPO.md`**.
