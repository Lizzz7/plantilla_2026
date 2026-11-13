# EXTRA · SOPHIA: ¿y si la métrica que piden NO es Gini?
# Este archivo tiene TODAS las métricas probables en funciones cortas.
# Uso 1 (ver todas sobre tu modelo):   python extra/metricas.py
# Uso 2 (cambiar la métrica del paso 4): en 4_modelo.py reemplaza gini(...) por la función que pidan:
#        from extra.metricas import auc_pr     ->  res = ... {k: auc_pr(y, v) ...}
# Regla: el modelo se ELIGE con la métrica que te van a calificar. Las demás son para el informe.
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn import metrics as M

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # para poder importar ajustes.py


# ---------- clasificación: el modelo da una PROBABILIDAD (o score) ----------
def gini(y, p):            # orden global. 0 = azar, 1 = perfecto. Gini = 2*AUC - 1
    return 2 * M.roc_auc_score(y, p) - 1


def auc(y, p):             # lo mismo que Gini en otra escala (0.5 = azar)
    return M.roc_auc_score(y, p)


def auc_pr(y, p):          # área bajo precisión-recall. Mejor que AUC si el positivo es MUY raro (<5%)
    return M.average_precision_score(y, p)    # el azar vale la tasa base, no 0.5


def ks(y, p):              # máxima distancia entre acumuladas de buenos y malos (clásico en riesgo)
    fpr, tpr, _ = M.roc_curve(y, p)
    return float(np.max(tpr - fpr))


def captura_top(y, p, k=0.10):   # % de todos los positivos que caen en el k% de arriba
    y, p = np.asarray(y), np.asarray(p)
    n = int(np.ceil(len(p) * k))
    top = np.argsort(-p)[:n]
    return y[top].sum() / y.sum()


def lift_top(y, p, k=0.10):      # cuántas veces mejor que al azar es el k% de arriba
    y, p = np.asarray(y), np.asarray(p)
    n = int(np.ceil(len(p) * k))
    return y[np.argsort(-p)[:n]].mean() / y.mean()


def precision_top(y, p, k=0.10):  # de los que llamamos (k% de arriba), qué % convierte
    y, p = np.asarray(y), np.asarray(p)
    n = int(np.ceil(len(p) * k))
    return y[np.argsort(-p)[:n]].mean()


def brier(y, p):           # error de la probabilidad (más bajo = mejor). Exige p entre 0 y 1
    return M.brier_score_loss(y, p)


def logloss(y, p):         # castiga mucho estar seguro y equivocado. Exige p entre 0 y 1
    return M.log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))


# --- métricas que necesitan un UMBRAL (sí/no). El umbral se elige en ENTRENAMIENTO (OOF), nunca en el examen ---
def umbral_f1(y_oof, p_oof):     # umbral que maximiza F1 en las predicciones fuera de pliegue
    prec, rec, thr = M.precision_recall_curve(y_oof, p_oof)
    f1 = 2 * prec * rec / np.clip(prec + rec, 1e-12, None)
    return float(thr[np.argmax(f1[:-1])])


def umbral_por_capacidad(p, k=0.10):  # si te dicen "solo podemos llamar al 10%", el umbral sale solo
    return float(np.quantile(p, 1 - k))


def f1(y, p, umbral):
    return M.f1_score(y, (np.asarray(p) >= umbral).astype(int))


def matriz(y, p, umbral):        # [[VN, FP], [FN, VP]]
    return M.confusion_matrix(y, (np.asarray(p) >= umbral).astype(int))


# ---------- regresión: el modelo da un NÚMERO (monto, días, unidades) ----------
def mae(y, yhat):          # error promedio en las unidades del problema (S/). Fácil de explicar
    return M.mean_absolute_error(y, yhat)


def rmse(y, yhat):         # como MAE pero castiga más los errores grandes
    return float(np.sqrt(M.mean_squared_error(y, yhat)))


def r2(y, yhat):           # % de la variación explicada. 0 = predecir el promedio; negativo = peor que eso
    return M.r2_score(y, yhat)


def mape(y, yhat):         # error % promedio. ¡Explota si hay y = 0! Por eso se ignoran los ceros
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    m = y != 0
    return float(np.mean(np.abs((y[m] - yhat[m]) / y[m])))


def wape(y, yhat):         # error % total = suma|error| / suma|y|. La versión segura de MAPE (series de tiempo)
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return float(np.abs(y - yhat).sum() / np.abs(y).sum())


# ---------- "ganancia": cuando el jurado mide plata, no orden ----------
def valor_capturado(y, p, monto, k=0.10):  # suma de monto de los positivos en el k% de arriba
    y, p, monto = np.asarray(y), np.asarray(p), np.asarray(monto)
    n = int(np.ceil(len(p) * k))
    top = np.argsort(-p)[:n]
    return float((y[top] * monto[top]).sum())


def tabla_calibracion(y, p, n=10):  # ¿la prob 0.30 convierte de verdad ~30%? Columna "real" vs "predicho"
    d = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    d["grupo"] = pd.qcut(d.p.rank(method="first"), n, labels=False)
    return d.groupby("grupo").agg(predicho=("p", "mean"), real=("y", "mean"), n=("y", "size")).round(3)


CLASIFICACION = {"gini": gini, "auc": auc, "auc_pr": auc_pr, "ks": ks,
                 "captura_10%": captura_top, "lift_10%": lift_top, "precision_10%": precision_top,
                 "brier (bajo=mejor)": brier, "logloss (bajo=mejor)": logloss}


if __name__ == "__main__":
    import ajustes as A
    S = Path(__file__).resolve().parents[1] / A.CARPETA_SALIDAS
    te = pd.read_parquet(S / "predice.parquet")
    prob = pd.read_parquet(S / "prob.parquet")
    d = te[["id", "target", "target_monto"]].merge(prob, on="id")
    if d.target.nunique() < 2:
        sys.exit("predice.parquet no tiene target conocido: corre esto con el corte anterior como examen")
    y, p = d.target, d.prob
    print("== Clasificación (sobre el examen) ==")
    for nombre, f in CLASIFICACION.items():
        print(f"  {nombre:22s} {f(y, p):.4f}")
    print(f"  tasa base (azar de auc_pr) {y.mean():.4f}")
    u = umbral_por_capacidad(p, 0.10)
    print(f"\nUmbral si llamamos al 10%: {u:.3f}  ->  F1 {f1(y, p, u):.3f}")
    print("Matriz [[VN FP] [FN VP]]:\n", matriz(y, p, u))
    print("\n== Calibración (predicho vs real por decil) ==")
    print(tabla_calibracion(y, p))
    print(f"\nValor capturado en el 10% de arriba: S/ {valor_capturado(y, p, d.target_monto):,.0f}"
          f"  de S/ {d.target_monto.sum():,.0f} totales")
    # demo de regresión: predecir el monto con un modelo tonto (promedio) para ver las escalas
    pos = d[d.target == 1]
    ingenuo = np.full(len(pos), pos.target_monto.median())
    print("\n== Regresión (demo: predecir monto con la mediana) ==")
    for nombre, f in {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape, "wape": wape}.items():
        print(f"  {nombre:6s} {f(pos.target_monto, ingenuo):,.3f}")
