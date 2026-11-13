# Modelos · cuándo usar cada uno y cómo explicarlo

Regla de oro: **empiecen simple, comparen con la misma validación, y quédense con el más simple que empate.**
Un modelo que pueden explicar en 30 segundos vale más ante el jurado que uno 0.005 mejor que nadie entiende.

## 1. Tabla de decisión

| Modelo | Cuándo | Fortaleza | Debilidad | Cómo se explica |
| --- | --- | --- | --- | --- |
| **Regla de 1 variable** | Siempre, como línea base | Cero riesgo, 1 segundo | No combina información | "Lo que haría un ejecutivo: ordenar por ventas" |
| **Regresión logística** | Primera opción seria; pocos datos; jurado de negocio | Explicable (pesos y signos), estable en el tiempo | No ve interacciones ni curvas sin trabajo previo | "Suma de efectos: más ventas → más probabilidad" |
| **Árbol de decisión** | Para explicar reglas, no para competir | Se dibuja | Inestable, poco preciso | "Si ventas > X y ya hizo factoring → alta" |
| **Random Forest** | Comparación robusta | Pocos parámetros, aguanta ruido | Lento con muchos datos, probabilidades poco calibradas | "Muchos árboles votan" |
| **LightGBM** | Datos tabulares grandes, relaciones no lineales | El que más gana en competencias tabulares; rápido | Sobreajusta con pocos datos; menos explicable | "Cada árbol corrige los errores del anterior" |
| **XGBoost** | Alternativa a LightGBM | Muy probado | Algo más lento | igual que LightGBM |
| **CatBoost** | Muchas categorías con muchos valores (distrito, CIIU) | Maneja categorías solo | Más lento de entrenar | igual, "con categorías nativas" |

Nuestro resultado (práctica, examen): regla 0.260 · **logística 0.292** · LightGBM 0.246. Ganó la logística
porque la señal es casi lineal (más ventas, más historia de factoring → más probabilidad) y hay 5 000 filas.
Con 200 000 filas y relaciones raras, LightGBM suele ganar. Por eso se compara, no se asume.

## 2. Regresión logística por dentro

`prob = 1 / (1 + e^-(b0 + b1·x1 + b2·x2 + ...))`

- Cada `b` es el peso de una variable. Signo + → la variable sube la probabilidad.
- Con variables estandarizadas, **odds ratio = e^b**: "una desviación estándar más de ventas multiplica las
  chances por 1.5".
- Preparación obligatoria (ya está en `4_modelo.py`):
  1. vacíos → mediana (`SimpleImputer`);
  2. log con signo en montos (si no, una empresa de S/ 3 millones domina los pesos);
  3. misma escala (`StandardScaler`);
  4. categorías → columnas 0/1 (`OneHotEncoder`).
- `C=0.1`: regularización. Más pequeño = pesos más prudentes = menos sobreajuste.
- Ver los pesos:
  ```python
  nombres = logistica[0].get_feature_names_out()
  pesos = pd.Series(logistica[-1].coef_[0], index=nombres).sort_values()
  ```

## 3. LightGBM por dentro

- Construye árboles pequeños uno tras otro; cada uno aprende lo que el anterior falló.
- Hiperparámetros que importan (en orden):

| Parámetro | Qué hace | Valor seguro | Si sobreajusta |
| --- | --- | --- | --- |
| `num_leaves` | complejidad de cada árbol | 15–31 | bajar a 7 |
| `min_child_samples` | mínimo de filas por hoja | 50 | subir a 100–200 |
| `learning_rate` + `n_estimators` | paso y número de árboles | 0.03 y 300 | menos árboles |
| `subsample`, `colsample_bytree` | usar parte de filas/columnas | 0.8 | 0.7 |

- Acepta vacíos y categorías (tipo `category`) sin preparación.
- Señal de sobreajuste: OOF bien pero examen mucho peor, o peor que la logística.
- Ajuste fino (Optuna): **al final y solo si sobra tiempo**. Mueve poco frente a buenas variables.

## 4. Validación (lo que hace honesto cualquier modelo)

- **5 pliegues estratificados**: la tabla se parte en 5 con la misma tasa de positivos; cada parte se predice con un
  modelo entrenado en las otras 4 (OOF).
- **Fuera de tiempo**: entrenar con el corte anterior, examinar con el actual. Imita lo que hará el banco.
- **Nunca** elegir el modelo mirando el examen muchas veces: se termina "ajustando al examen".

## 5. Lo que NO hacer (y por qué)

| Tentación | Por qué no |
| --- | --- |
| Reponderar clases / SMOTE por "desbalance" | El Gini mide orden: no mejora y descalibra las probabilidades |
| Redes neuronales | En datos tabulares pequeños rinden menos que boosting y no se explican |
| PCA | Pierde la interpretación de las variables; no mejora árboles |
| 50 modelos en un ensamble | Ganancia mínima, imposible de explicar en 30 segundos |
| Optuna antes de tener buenas variables | Optimiza ruido |

## 6. Otros problemas, otros modelos

| Problema | Modelo |
| --- | --- |
| Monto (regresión) | `LGBMRegressor` (o `objective="tweedie"` con muchos ceros); `Ridge` como base lineal |
| Probabilidad × monto | Dos partes: clasificador × regresor entrenado solo en los que convirtieron |
| Grupos sin target (segmentación) | K-means sobre variables escaladas; describir cada grupo por sus promedios |
| Pronóstico (serie de tiempo) | LightGBM con rezagos (valor de ayer, hace 7 días) y validación por bloques de tiempo |
| Red pagador–proveedor | Mismo modelo + variables de contagio (% de pagadores que ya hicieron factoring) |

## 7. Guion de 30 segundos

"Comparamos tres modelos con la misma validación: una regla simple, una regresión logística y LightGBM.
Ganó la logística con Gini 0.29 en un periodo que el modelo no vio, contra 0.26 de la regla. La elegimos también
porque se explica: más ventas y más historia de factoring suben la probabilidad."
