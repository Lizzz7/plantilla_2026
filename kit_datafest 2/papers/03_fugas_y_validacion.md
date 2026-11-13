# 03 · Fugas de información y validación

## Kaufman, S., Rosset, S. y Perlich, C. (2011) — "Leakage in Data Mining: Formulation, Detection, and Avoidance"

- **Dónde:** KDD 2011, pp. 556–563 (DOI 10.1145/2020408.2020496). Versión extendida en *ACM Transactions on Knowledge Discovery from Data* 6(4), 2012, con Ori Stitelman como coautor.
- **Enlaces:** ficha DBLP https://dblp.org/rec/conf/kdd/KaufmanRP11.html · versión de revista https://cris.iucc.ac.il/en/publications/leakage-in-data-mining-formulation-detection-and-avoidance-2/
- **En nuestras palabras:** definen la fuga como meter en el modelo información sobre el target que **no estaría disponible legítimamente al momento de predecir**. Muestran que varias competencias famosas fueron ganadas aprovechando fugas. Su propuesta para evitarlas: etiquetar cada dato con el momento en que se conoce y separar estrictamente "lo que sé para aprender" de "lo que sé para predecir" (*learn-predict separation*). Para detectarlas cuando no controlas cómo se juntaron los datos: buscar variables sospechosamente predictivas y revisar su origen.

**Cómo se traduce a nuestro kit:**

| Idea del paper | Dónde está en el kit |
|---|---|
| separar aprender / predecir por tiempo | `CORTE`, `CORTE_ANTERIOR` y el `WHERE fecha < corte` de `3_variables.py` |
| variables "demasiado buenas" = sospecha | la prueba de Gini > 0.5 por variable en `3_variables.py` |
| conocer el origen de cada columna | la lista `FUERA` en `ajustes.py` (fecha de cancelación, copias de ventas) |
| fuga temporal en series | rezagos ≥ horizonte en `temporal/pronostico.py` |
| filas del mismo cliente en train y validación | `StratifiedGroupKFold` en `temporal/varios_cortes.py` |

**Frase para el jurado:** *"Nuestra primera validación fue de fugas, no de modelos: cada variable se calcula solo con información anterior al corte y probamos fuera de tiempo, como recomiendan Kaufman, Rosset y Perlich."*

## Perlich y la validación cruzada con pocos datos

Claudia Perlich (coautora del paper anterior) tiene otro trabajo sobre cómo la validación cruzada y el *stacking* pueden fabricar modelos que parecen predictivos con datos **aleatorios** cuando hay pocas filas. Lo comenta en esta entrevista: https://dataskeptic.com/blog/episodes/2016/predictive-models-on-random-data
**Para qué:** justificar que (1) siempre comparamos contra un **baseline tonto**, y (2) desconfiamos de mejoras de 0.005 en el OOF.

## Resumen operativo (para tener en la cabeza)

1. Si una variable sola da Gini > 0.5 → preguntar **cuándo** se conoce ese dato.
2. Si OOF ≫ examen fuera de tiempo → hay fuga o el comportamiento cambió.
3. Si el examen ≫ OOF → sospechar del examen (¿se usó para elegir algo?).
4. En el tiempo: nunca KFold aleatorio.
5. Mismo cliente en varias filas → agrupar por cliente en la validación.
