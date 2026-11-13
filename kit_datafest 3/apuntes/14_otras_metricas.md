# 14 · ¿Y si la métrica NO es Gini?

**Quién:** Sophia (elige el modelo con la métrica que califican) + Liz (explica la métrica al jurado).
**Código:** `scripts/extra/metricas.py` (todas las funciones) — `python extra/metricas.py` las calcula todas sobre su modelo.

## La regla de oro

> El modelo se **elige** con la métrica que te van a **calificar**. Las demás métricas son para el informe y la exposición.

Si el enunciado dice "AUC-PR" y ustedes eligen el modelo por Gini, pueden quedar segundos con el mejor modelo en Gini.

## Paso 1: ¿qué tipo de salida me piden?

| Me piden… | Tipo | Métricas probables |
|---|---|---|
| una **probabilidad** / score por cliente | clasificación (orden) | Gini, AUC, AUC-PR, KS, lift, captura |
| un **sí / no** por cliente | clasificación (umbral) | F1, precisión, recall, matriz de confusión |
| una **lista de los N mejores** | ranking con capacidad | precisión@N, captura@N, valor capturado |
| un **número** por cliente (monto, días) | regresión | MAE, RMSE, R², MAPE |
| un **número por fecha** (demanda, saldo) | serie de tiempo | WAPE, MAE, RMSE, MASE (ver apunte 17) |
| que la probabilidad sea **creíble** | calibración | Brier, log loss, tabla de calibración |

## Paso 2: cada métrica en una línea (para decirla al jurado)

| Métrica | Qué mide | Rango / "azar" | Cuándo es la buena |
|---|---|---|---|
| **Gini** = 2·AUC − 1 | qué tan bien ordena a todos | 0 azar · 1 perfecto | estándar en banca/riesgo; ordenar toda la cartera |
| **AUC** | probabilidad de que un positivo tenga score mayor que un negativo | 0.5 azar · 1 perfecto | lo mismo que Gini en otra escala |
| **AUC-PR** (average precision) | precisión promedio a lo largo de todos los recall | **azar = tasa base** (ej. 0.20) | positivo raro (<5%): fraude, fuga, default |
| **KS** | máxima separación entre acumuladas de positivos y negativos | 0 – 1 | clásico en scoring de crédito en Perú |
| **Captura@10%** | % de todos los positivos que caen en el 10% de arriba | azar = 10% | "solo podemos llamar al 10%" |
| **Lift@10%** | cuántas veces mejor que el azar es ese 10% | azar = 1x | explicarlo a negocio ("2x más conversión") |
| **Precisión@10%** | de los que llamamos, qué % convierte | azar = tasa base | costo por llamada importa |
| **F1** | equilibrio precisión/recall con un umbral | 0 – 1 | piden sí/no y no dicen capacidad |
| **Brier** | error cuadrático de la probabilidad | menor = mejor | piden probabilidades "bien calibradas" |
| **Log loss** | castiga mucho estar seguro y equivocado | menor = mejor | competencias tipo Kaggle con probabilidades |
| **MAE** | error promedio en soles | menor = mejor | montos; fácil de explicar |
| **RMSE** | como MAE pero castiga más errores grandes | menor = mejor | errores grandes son caros |
| **R²** | % de la variación explicada | 0 = predecir el promedio; **<0 = peor que el promedio** | regresión "académica" |
| **MAPE** | error % promedio | explota si y = 0 | solo si no hay ceros |
| **WAPE** | error total / total real | menor = mejor | series de tiempo; la versión segura de MAPE |

## Paso 3: cómo cambiar la métrica en el flujo (2 líneas)

En `4_modelo.py`:

```python
from extra.metricas import auc_pr          # o ks, captura_top, brier...
res = pd.DataFrame({"auc_pr_oof": {k: auc_pr(y, v) for k, v in oof.items()}})
```

Y en la regla de elección, si la métrica es "menor es mejor" (Brier, log loss, MAE), se toma el **mínimo**, no el máximo.
O directamente: `python extra/mas_modelos.py auc_pr` compara 7 modelos con esa métrica.

## Trampas que el jurado detecta

1. **Elegir el umbral en el examen.** El umbral de F1 se elige con las predicciones OOF del entrenamiento (`umbral_f1(y_oof, p_oof)`), nunca mirando el examen. Si te dan capacidad ("10%"), el umbral sale solo: `umbral_por_capacidad(p, 0.10)`.
2. **AUC-PR comparado con 0.5.** El azar de AUC-PR es la tasa base. Un 0.33 con tasa 0.20 es bueno (1.6x); un 0.33 con tasa 0.40 es peor que tirar una moneda.
3. **Brier / log loss con un ensamble por rango.** Los rangos no son probabilidades: para estas métricas usen un modelo solo (logística suele estar bien calibrada).
4. **R² negativo.** No es un bug: el modelo es peor que predecir el promedio. Prueben el target sin log, o predecir la mediana por grupo como baseline.
5. **MAPE con ceros.** Divide por cero. Usen WAPE y díganlo.

## Resultado en los datos de práctica (para tener la escala en la cabeza)

| Métrica | Valor | Lectura |
|---|---|---|
| Gini | 0.29 | ordena moderadamente (normal en propensión comercial: 0.2–0.4) |
| AUC-PR | 0.33 | tasa base 0.20 → 1.6x el azar |
| KS | 0.22 | — |
| Captura@10% | 20% | el 10% de arriba trae el doble de lo que traería el azar |
| Lift@10% | 2.0x | "llamando al 10% que dice el modelo convierten el doble" |
| Brier | 0.152 | — |
| Calibración | decil 10: predice 0.39, real 0.39 | la probabilidad es creíble |

Frase para el jurado: *"Elegimos el modelo con [métrica oficial] porque es con la que nos evalúan; reportamos además lift y captura en el 10% porque son las que entiende el negocio."*
