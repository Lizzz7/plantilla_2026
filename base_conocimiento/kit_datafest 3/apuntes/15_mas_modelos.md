# 15 · Más modelos: qué es cada uno y cuándo usarlo

**Quién:** Sophia. **Código:** `scripts/extra/mas_modelos.py` (7 candidatos + ensamble, misma validación, métrica a elección).

```
python extra/mas_modelos.py                # Gini
python extra/mas_modelos.py auc_pr         # otra métrica
python extra/mas_modelos.py gini rapido    # sin los lentos (random forest, catboost)
```

## La idea que hay que poder explicar

Todos los modelos se comparan con **la misma validación** (5 pliegues, cada fila predicha por un modelo que no la vio = OOF). Si uno usa una validación distinta, la comparación no vale. Gana el mejor OOF, **pero si uno más simple está a menos de 0.005, gana el simple** (más fácil de explicar y menos riesgo de que se caiga en el examen).

## Mapa rápido

| Modelo | Familia | Qué hace (una frase) | Bueno cuando… | Malo cuando… | Velocidad |
|---|---|---|---|---|---|
| **Regla de 1 variable** | baseline | ordena por la mejor variable sola | siempre: es el piso que hay que superar | — | instantáneo |
| **Regresión logística** | lineal | suma ponderada de variables → probabilidad | pocos datos, mucho ruido, hay que explicar cada coeficiente; probabilidades bien calibradas | relaciones no lineales fuertes, interacciones | instantáneo |
| **Árbol de decisión** | árbol | preguntas sí/no en cascada | explicar con un dibujo; reglas de negocio | casi siempre pierde contra un ensamble | instantáneo |
| **Random Forest** | ensamble de árboles (en paralelo) | muchos árboles con muestras al azar, se promedian | robusto "de fábrica", poca calibración de parámetros | datos muy grandes (lento, pesado) | medio |
| **HistGradientBoosting** | boosting (sklearn) | árboles en serie, cada uno corrige al anterior | no quieren instalar nada extra | — | rápido |
| **LightGBM** | boosting | boosting optimizado para muchos datos | tablas grandes (>50k filas), muchas variables | pocos datos y mucho ruido → sobreajusta | muy rápido |
| **XGBoost** | boosting | boosting con regularización fuerte | el clásico de competencias; muy estable | — | rápido |
| **CatBoost** | boosting | boosting que trata categorías sin one-hot | muchas categorías (rubro, distrito, CIIU) | prisa (es el más lento) | lento |
| **Ensamble por rango** | combinación | promedia las *posiciones* de los mejores 3 | cuando los modelos se equivocan en cosas distintas | piden probabilidades calibradas | suma de todos |

## Resultado en los datos de práctica (5,000 empresas, 18% positivos)

| Modelo | Gini OOF | Gini examen | Seg. |
|---|---|---|---|
| **logística** | **0.295** | **0.292** | 0.3 |
| ensamble top 3 | 0.282 | 0.288 | 10 |
| random forest | 0.266 | 0.275 | 8 |
| xgboost | 0.252 | 0.262 | 1 |
| catboost | 0.245 | 0.265 | 9 |
| hist_gb | 0.241 | 0.260 | 1 |
| árbol | 0.225 | 0.242 | 0.2 |
| lightgbm | 0.220 | 0.248 | 1 |

**Por qué gana la logística aquí** (y por qué puede pasar en el reto): pocas filas (5k), señal débil y mucho ruido. Los boosting aprenden ruido; la logística con regularización (C=0.1) y log de las colas no. Con 100k+ filas y relaciones no lineales, normalmente gana el boosting. **Por eso se prueban todos y decide el OOF, no la fama del modelo.**

## Parámetros que importan (y los valores "seguros")

| Modelo | Parámetro | Qué controla | Valor seguro | Si sobreajusta… |
|---|---|---|---|---|
| Logística | `C` | regularización (menor = más simple) | 0.1 | bajar a 0.03 |
| Árboles/boosting | `num_leaves` / `max_depth` | complejidad de cada árbol | 15 hojas / prof. 4–5 | bajar |
| Boosting | `min_child_samples` / `min_child_weight` | mínimo de filas por hoja | 50 / 20 | subir |
| Boosting | `learning_rate` + `n_estimators` | paso y cantidad de árboles | 0.03 + 300 | menos árboles |
| Boosting | `subsample`, `colsample_bytree` | % de filas/columnas por árbol | 0.8 | bajar a 0.6 |
| Random Forest | `min_samples_leaf` | tamaño mínimo de hoja | 30 | subir |

No pierdan más de 20 minutos tuneando: en estos retos el salto grande viene de **variables y de evitar fugas**, no de parámetros.

## Cómo usar el ganador en la entrega

`mas_modelos.py` guarda `salidas/prob_mas_modelos.parquet`. Si gana a lo que tenían: renómbrenlo a `prob.parquet` y corran `5_entregar.py`. Ojo: el ensamble devuelve rangos (0–1), no probabilidades; si el entregable pide probabilidad, usen un modelo solo.

## Si piden regresión (predecir un monto)

Mismos modelos con su versión `Regressor` (`LinearRegression`/`Ridge`, `RandomForestRegressor`, `LGBMRegressor`, `XGBRegressor`, `CatBoostRegressor`) y métricas MAE/RMSE/R² de `extra/metricas.py`. Dos consejos:
- Entrenen con el target **en su escala**; si lo pasan a log, el modelo minimiza error en log y el R² en soles puede salir negativo.
- Si el monto solo existe para los que convierten: **dos pasos** = P(convierte) × monto esperado si convierte (lo que ya hace `5_entregar.py`).

## Frase para el jurado

*"Comparamos 7 modelos con la misma validación cruzada fuera de pliegue. Ganó la regresión logística por 0.03 de Gini sobre el mejor boosting; con 5 mil empresas y señal ruidosa, el modelo simple generaliza mejor, y además podemos explicar cada variable."*
