# 02 · Modelos: de dónde salen y qué dice la evidencia

## Chen, T. y Guestrin, C. (2016) — "XGBoost: A Scalable Tree Boosting System"

- **Dónde:** KDD 2016. **Enlace:** https://arxiv.org/abs/1603.02754 (DOI 10.1145/2939672.2939785)
- **En nuestras palabras:** presenta XGBoost, una implementación de *gradient boosting* con árboles que agrega regularización, manejo nativo de valores faltantes (aprende hacia qué rama mandar los nulos) y optimizaciones de sistema para escalar. Se volvió la herramienta por defecto en competencias de datos tabulares.
- **Para qué lo citamos:** por qué probamos boosting; por qué no imputamos nulos para los modelos de árboles.

## Ke, G. et al. (2017) — "LightGBM: A Highly Efficient Gradient Boosting Decision Tree"

- **Dónde:** NeurIPS 2017. **Enlace:** https://proceedings.neurips.cc/paper/2017/file/6449f44a102fde848669bdd9eb6b76fa-Paper.pdf
- **En nuestras palabras:** propone dos técnicas para acelerar el boosting en datos grandes: muestrear con prioridad las filas con gradiente grande (GOSS) y agrupar variables que casi nunca tienen valores a la vez (EFB). Reportan entrenamiento hasta ~20 veces más rápido con precisión similar.
- **Para qué lo citamos:** por qué LightGBM cuando hay muchas filas o poco tiempo.

## Prokhorenkova, L. et al. (2018) — "CatBoost: unbiased boosting with categorical features"

- **Dónde:** NeurIPS 2018. **Enlace:** https://arxiv.org/abs/1706.09516
- **En nuestras palabras:** identifica una **fuga sutil** dentro del boosting (el modelo usa el target de la misma fila al codificar categorías y al calcular gradientes) y la corrige con *ordered boosting* y un tratamiento especial de las categorías.
- **Para qué lo citamos:** por qué CatBoost cuando hay muchas categorías (rubro, CIIU, distrito). Y como ejemplo de que **hasta los algoritmos tienen fugas**: refuerza nuestra obsesión con el corte.

## Lessmann, S., Baesens, B., Seow, H.-V. y Thomas, L. (2015) — "Benchmarking state-of-the-art classification algorithms for credit scoring: An update of research"

- **Dónde:** *European Journal of Operational Research* 247(1), 124–136. DOI 10.1016/j.ejor.2015.05.030
- **Enlaces:** ficha https://econpapers.repec.org/RePEc:eee:ejores:v:247:y:2015:i:1:p:124-136 · versión de autor (PDF) https://crc.business-school.ed.ac.uk/sites/crc/files/2023-10/Benchmarking-State-of-the-Art-Classification-Algorithms-for-Credit-Scoring-Lessmann-Seow-Baesens-and-Thomas.pdf
- **En nuestras palabras:** compara 41 clasificadores en 8 bases reales de scoring de crédito, con varias métricas, y evalúa el impacto financiero de usar uno u otro. Actualiza un estudio clásico de 2003.
- **Para qué lo citamos:** que **comparar varios modelos con varias métricas** es la práctica estándar en banca; que la elección debe considerar también el impacto de negocio, no solo la métrica. Encaja con nuestro `mas_modelos.py` + priorización por valor.

## Idea de fondo para la exposición

En datos tabulares de banca, la combinación **regresión logística (explicable) + un boosting (potente)** cubre casi todo. Probamos ambos con la misma validación y elegimos con la métrica oficial. Cuando empatan, preferimos el simple: se explica, se implementa y se monitorea más fácil, y eso pesa en un banco regulado.
