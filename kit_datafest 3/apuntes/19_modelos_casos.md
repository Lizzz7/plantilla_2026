# 19 · Modelos por caso: cuándo, cómo, dónde y con qué métrica

**Quién:** todas (Sophia lo domina; Liz y Nat lo usan para explicar).
Complementa: `04_modelos.md` (cómo funciona cada modelo), `14_otras_metricas.md` (cada métrica), `15_mas_modelos.md` (comparación).

## La pregunta que decide todo

Antes de elegir modelo, contesten en voz alta estas 4 preguntas. Las respuestas salen del enunciado.

1. **¿Qué es una fila?** Una empresa, una empresa en un mes, una agencia en un día, una factura...
2. **¿Qué se predice?** Un sí/no, un monto, una categoría, un número en el tiempo, o nada (grupos).
3. **¿Cuándo se decide?** La fecha de corte: lo que pasa antes son variables; lo que pasa después, el target.
4. **¿Qué se hace con la predicción?** Llamar al 10%, asignar un monto, abastecer una agencia... Eso define la métrica.

## Tabla maestra de casos

| # | Caso (cómo lo dice el enunciado) | Tipo | Fila | Modelo (en orden de prueba) | Métrica para elegir | Métrica para explicar | Script |
|---|---|---|---|---|---|---|---|
| 1 | "¿Qué empresas tomarán factoring en los próximos 6 meses?" | clasificación binaria | empresa al corte | regla → logística → LightGBM/XGBoost | la oficial (Gini/AUC) | lift y captura @10% | flujo 1–5 |
| 2 | "...y prioricen el 10% con cupos por zona" | clasificación + priorización | empresa | igual que 1 | Gini **dentro de zona** | conversión de los priorizados vs base | `5_entregar.py`, `optimizacion/` |
| 3 | "¿Cuánto financiará cada empresa?" | regresión | empresa | mediana por rubro → Ridge → LGBMRegressor | MAE o RMSE | error promedio en soles | `4_modelo.py` con Regressor |
| 4 | "Maximicen el monto esperado de la campaña" | probabilidad × monto | empresa | clasificador × regresor (dos modelos) | valor capturado en el top-K | soles esperados de la lista | `5_entregar.py` |
| 5 | "¿Quién **dejará** de usar factoring / cerrará la cuenta?" (fuga) | clasificación binaria | cliente activo al corte | igual que 1 | Gini / AUC-PR si es raro | captura @10% | flujo 1–5 cambiando `TARGET_*` |
| 6 | "¿Qué pagador no pagará su factura a tiempo?" (riesgo) | clasificación binaria, positivo raro | factura o pagador | logística (explicable, regulado) → boosting | **AUC-PR** o KS | KS, tasa de mora por decil | flujo con fila = factura |
| 7 | "¿Qué producto ofrecerle?" (siguiente mejor producto) | multiclase o varios binarios | empresa | un binario por producto (más simple) | Gini por producto | tasa de acierto del top-1 | flujo 1 vez por producto |
| 8 | "¿Cuánto efectivo/demanda habrá cada día?" | serie de tiempo | agencia × día | naive estacional → Holt-Winters/SARIMA → LightGBM con rezagos | WAPE / MAE | error % y sesgo | `temporal/pronostico.py` |
| 9 | "¿Cuándo hará su próxima operación?" | tiempo hasta el evento | empresa | binarios a 1, 3 y 6 meses | Gini por horizonte | % que ocurre en cada horizonte | flujo con `HORIZONTE` 1, 3, 6 |
| 10 | "Agrupen a los clientes en perfiles" | sin target (segmentación) | empresa | K-means (4–6 grupos) | estabilidad de los grupos y si tienen sentido | nombre de negocio por grupo | `11_que_hacer_si.md` §4 |
| 11 | "¿A quién le **cambia** la decisión una llamada?" (uplift) | causal | empresa | dos modelos: contactados vs no contactados | ganancia incremental | solo si hay grupo de control | decir que se necesita grupo control |

## Cada caso explicado: cuándo, cómo, dónde

### Caso 1–2 · Propensión a factoring (el más probable)
- **Cuándo:** el target es "pasó o no pasó algo" en una ventana después del corte.
- **Cómo:** una fila por empresa con variables del pasado (facturación, recencia, operaciones previas, rubro, zona). Target = factoring BCP no anulado en [corte, corte + 6m).
- **Dónde está:** `3_variables.py` arma la tabla; `4_modelo.py` compara regla, logística y LightGBM; `5_entregar.py` prioriza.
- **Métrica:** Gini porque solo importa **ordenar** bien. Con cupos por zona, lo que realmente importa es el orden **dentro** de cada zona (`extra/uno_o_varios.py` lo mide). En la práctica dio 0.292 global y 0.292 dentro de zona.
- **Qué ayuda la métrica a decidir:** qué modelo entregar (OOF), si hay fuga (Gini > 0.8 o una variable > 0.5) y cuánto mejor que el azar es la lista (lift).

### Caso 3–4 · Monto
- **Cuándo:** piden "cuánto", o "maximizar soles", no solo "quién".
- **Cómo:** el monto solo existe para quien convierte. Por eso hay **dos partes**: P(convierte) × monto si convierte. El monto se estima con la mediana del rubro (robusto) o con un regresor entrenado solo con quienes convirtieron.
- **Métrica:** MAE en soles para el regresor. Para la campaña, el **valor capturado** en el top-K (`extra/metricas.py: valor_capturado`).
- **Cuidado:** entrenar el regresor en soles, no en log, si los califican con R² en soles (en log salió R² negativo).

### Caso 5–6 · Fuga y riesgo (positivo raro)
- **Cuándo:** el evento ocurre en menos del 5% de los casos.
- **Cómo:** el mismo flujo; solo cambian `TARGET_TABLA` y `TARGET_FILTRO`.
- **Métrica:** AUC-PR (su azar es la tasa base, no 0.5) y KS, que es la clásica en riesgo en Perú. **No** usar accuracy: con 2% de positivos, decir "nadie" da 98%.
- **Modelo:** en riesgo, la logística se prefiere aunque pierda por poco, porque se explica a un regulador.

### Caso 8 · Pronóstico en el tiempo
- **Cuándo:** la fila es "lugar × fecha" y piden números futuros.
- **Cómo:** validación hacia adelante; nunca pliegues aleatorios. Rezagos ≥ horizonte.
- **Dónde:** `temporal/pronostico.py`; ARIMA explicado en `temporal/arima_paso_a_paso.py`.
- **Métrica:** WAPE (la versión segura de MAPE) y **sesgo**: quedarse corto de efectivo cuesta más que sobrar.

### Caso 10 · Segmentación
- **Cuándo:** no hay target; piden "perfiles" o "grupos".
- **Cómo:** escalar variables, K-means con 4 a 6 grupos y describir cada grupo por sus promedios ("pymes comerciales con facturación creciente y sin factoring").
- **Métrica:** no hay una correcta. Lo que importa es que los grupos sean **estables** (corran con otra semilla) y **accionables** (cada grupo pide una acción distinta).

## Las métricas: en qué ayudan, fase por fase

| Fase | Pregunta | Métrica que la responde |
|---|---|---|
| Revisar datos (Nat) | ¿qué tan raro es el positivo? | tasa base (define si usar AUC-PR) |
| Variables (Kath) | ¿alguna variable hace trampa? | Gini de cada variable sola (> 0.5 = sospecha) |
| Modelo (Sophia) | ¿cuál modelo entrego? | métrica oficial en OOF |
| Modelo (Sophia) | ¿generaliza al futuro? | métrica en el examen fuera de tiempo (≈ OOF = sano) |
| Modelo (Sophia) | ¿la probabilidad es creíble? | Brier y tabla de calibración |
| Entrega (Liz) | ¿la lista vale la pena? | lift, precisión y captura @K; valor capturado |
| Exposición (Nat/Liz) | ¿qué gana el banco? | "llamando al 10% convierten 2x; S/ X esperados" |

## Errores típicos al elegir modelo

| Error | Por qué está mal | Qué hacer |
|---|---|---|
| Elegir el modelo "de moda" sin comparar | en 5 000 filas ganó la logística a todos los boosting | comparar siempre contra la regla y la logística |
| Elegir con el examen | se termina ajustando al examen | elegir con OOF; el examen solo confirma |
| Usar accuracy | con positivos raros engaña | Gini, AUC-PR, KS |
| Un modelo por zona "porque las zonas son distintas" | menos datos por modelo; en la práctica perdió (0.279 vs 0.292) | medir con `uno_o_varios.py` |
| Tunear parámetros 2 horas | mueve 0.005; variables y fugas mueven 0.1 | 20 minutos máximo |
