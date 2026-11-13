# Métricas · qué miden, cómo leerlas y cuál usar (apunte de Sophia, útil para todas)

Una métrica responde UNA pregunta. Elegir la métrica es elegir la pregunta. Antes de modelar: ¿qué pide el
enunciado? ¿Ordenar (a quién llamar primero), acertar sí/no con un umbral, o estimar un monto?

## 1. Mapa rápido

| Pregunta del negocio | Métrica principal | Complemento |
| --- | --- | --- |
| ¿Ordena bien a quién llamar primero? | **Gini** (= 2·AUC − 1) | lift del decil 1, captura |
| ¿Encuentra a los pocos positivos? (desbalance fuerte, < 5%) | **AUC-PR** | precisión en el top-k |
| ¿Acierta con un umbral (sí/no)? | **F1**, precisión, recall | matriz de confusión |
| ¿Las probabilidades son "reales"? | **Brier**, calibración por decil | — |
| ¿Estima bien un monto? | **R²**, MAE, RMSE | Gini del orden por monto |
| ¿Separa buenos de malos (riesgo)? | **KS** | Gini |

## 2. Gini y AUC (la del concurso casi siempre)

- **AUC**: si tomo al azar una empresa que convirtió y una que no, la probabilidad de que el modelo le dé más
  puntaje a la que convirtió. 0.5 = azar, 1 = perfecto.
- **Gini = 2·AUC − 1**: lo mismo en escala 0 (azar) a 1 (perfecto). Es el estándar en banca.
- **Solo mide ORDEN.** Si multiplicas todas las probabilidades por 2, el Gini no cambia. Por eso la regla
  "ordenar por ventas" tiene Gini aunque no dé probabilidades.
- **Valores típicos** en propensión comercial: 0.2–0.5 normal, 0.5–0.7 muy bueno, **más de 0.8 = buscar fuga**.
- En código: `2 * roc_auc_score(y, prob) - 1`.

Datos de práctica: regla 0.260 · logística 0.292 · LightGBM 0.246 (examen).

## 3. Lift y captura (la traducción al negocio)

- **Lift del decil 1**: tasa de conversión del 10% con mayor probabilidad ÷ tasa promedio.
  Práctica: 39% / 19.9% = **2.0×**. "Con las mismas llamadas, el doble de conversiones."
- **Captura al k%**: qué % de todas las conversiones está en el k% de arriba. Al azar, captura = k%.
- **Gráfico de deciles** (`4_deciles.png`): barras que bajan de izquierda a derecha = buen orden. Si suben y bajan
  sin patrón, el modelo no ordena.

## 4. AUC-PR (cuando los positivos son pocos)

- Área bajo la curva precisión–recall. Su "azar" es la tasa base (si convierte 2%, el azar da 0.02).
- Con 1–2% de positivos el AUC puede verse alto aunque el top de la lista esté lleno de errores; el AUC-PR lo
  delata.
- Código: `from sklearn.metrics import average_precision_score`.
- Reporten siempre "AUC-PR X vs base Y" (ej. 0.45 vs 0.058 = 7.8 veces el azar).

## 5. KS (Kolmogorov-Smirnov)

- Máxima distancia entre la distribución acumulada del puntaje de positivos y la de negativos (0 a 1).
- Muy usado en riesgo de crédito. Típico: 0.2–0.4 aceptable, más de 0.5 muy bueno.
- Código: `from scipy.stats import ks_2samp; ks_2samp(p[y == 1], p[y == 0]).statistic`.

## 6. Con umbral: precisión, recall, F1

Solo si el enunciado pide decir sí/no (ej. "marquen a quién contactar" sin capacidad fija).

| | Predigo 1 | Predigo 0 |
| --- | --- | --- |
| Real 1 | VP | FN |
| Real 0 | FP | VN |

- Precisión = VP / (VP + FP): de los que marqué, cuántos eran.
- Recall = VP / (VP + FN): de los que eran, cuántos encontré.
- F1 = 2·P·R / (P + R).
- **El umbral NO es 0.5 por defecto**: se elige el que maximiza la métrica en las predicciones OOF:
  ```python
  from sklearn.metrics import f1_score
  umbrales = np.linspace(0.05, 0.95, 91)
  mejor_u = max(umbrales, key=lambda u: f1_score(y, oof >= u))
  ```

## 7. Calibración y Brier

- **Brier** = promedio de (prob − real)²; menor es mejor. Importa cuando la probabilidad se multiplica por un monto
  (valor esperado).
- **Calibración por decil**: en cada decil, compara la probabilidad promedio con la tasa real. Si el decil 1 dice
  50% en promedio y en la realidad convierte 39%, las probabilidades están infladas.
- Reponderar clases (`class_weight`) **descalibra**: infla las probabilidades. En la plantilla grande bajó el Gini
  de LightGBM de 0.244 a 0.181. No lo usen salvo que la métrica sea F1/recall.

## 8. Regresión: R², MAE, RMSE

- **R²**: qué parte de la variación del monto explica el modelo (1 = todo, 0 = igual que predecir el promedio,
  negativo = peor que el promedio).
- **MAE**: error promedio en soles (fácil de explicar). **RMSE**: castiga más los errores grandes.
- Con muchos montos en cero, el R² es bajo aunque el orden sea útil: reporten también el Gini del orden.
- Lo vimos: entrenar en logaritmo y volver a soles dio **R² negativo**; entrenar en soles dio 0.12.

## 9. OOF, examen y qué número reportar

- **OOF**: validación cruzada en la tabla de entrenamiento. Sirve para COMPARAR modelos entre sí.
- **Examen** (corte actual, si su target se conoce): el número honesto para el jurado.
- Si OOF − examen > 0.05: sobreajuste o cambio entre periodos.
- En el evento normalmente no hay examen (el target es el futuro): reporten el OOF del corte anterior y digan
  que es fuera de tiempo.

## 10. Frases listas

- "Nuestro modelo ordena con Gini 0.29 en un periodo que no vio; una regla simple da 0.26."
- "El 10% de arriba convierte 2 veces el promedio."
- "Medimos AUC-PR porque los positivos son pocos: 0.45 contra 0.06 del azar."
- "No reponderamos clases: baja el Gini e infla las probabilidades que usamos para el valor esperado."
