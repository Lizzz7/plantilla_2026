"""
CANDIDATOS: desde "sin modelo" hasta LightGBM. Siempre se empieza por lo simple.

  regla_1var      sin modelo: ordenar por la variable con más Gini. Es la LÍNEA BASE que hay que
                  superar ("¿cuánto mejora el modelo frente a lo que haría un ejecutivo?").
  regla_top3      sin modelo: promedio de rankings de las 3 mejores (tipo scorecard manual).
  logistica       lineal, explicable con coeficientes. Gana cuando hay pocos datos o señal lineal.
  lgbm            árboles con boosting: no linealidades e interacciones, nulos y categorías nativas.
                  Suele ganar en datos tabulares con >5k filas.
  lgbm_pesos      mismo lgbm con class weights (desbalance). Mismo Gini, probabilidades infladas.
  lgbm_submuestra entrena con 1 negativo cada k y CORRIGE la probabilidad después (prior correction).
  ensamble        promedio de rankings de logística + lgbm: gana si se equivocan en cosas distintas.

Todo se evalúa con predicciones OOF (fuera de pliegue): la comparación es justa.
"""
import warnings

import numpy as np
import pandas as pd

from pipeline.modelado import metricas as M
from pipeline.modelado.datos import pliegues
from pipeline.regularizar import Regularizador

warnings.filterwarnings("ignore")

LGBM_BASE = dict(n_estimators=600, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                 subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=-1)


def _rank(x):
    return pd.Series(x).rank(pct=True).values


# ------------------------------------------------------------------ ajustadores (fit -> predict)
def fit_lgbm(Xtr, ytr, Xva, params=None, peso=None, submuestra=None, semilla=42, monto=False, devolver=False):
    import lightgbm as lgb
    p = {**LGBM_BASE, **(params or {}), "random_state": semilla}
    Xt, yt = Xtr, ytr
    factor = 1.0
    if submuestra:  # 1 de cada `submuestra` negativos
        rng = np.random.default_rng(semilla)
        keep = (ytr.values == 1) | (rng.random(len(ytr)) < 1 / submuestra)
        Xt, yt = Xtr[keep], ytr[keep]
        factor = submuestra
    if monto:
        m = lgb.LGBMRegressor(**p)
    else:
        m = lgb.LGBMClassifier(**p, **({"is_unbalance": True} if peso else {}))
    # early stopping con un 10% interno del train (no toca la validación)
    rng = np.random.default_rng(semilla + 1)
    es = rng.random(len(yt)) < 0.1
    m.fit(Xt[~es], yt[~es], eval_set=[(Xt[es], yt[es])],
          callbacks=[lgb.early_stopping(50, verbose=False)])
    pred = m.predict(Xva) if monto else m.predict_proba(Xva)[:, 1]
    if submuestra and not monto:  # corrección de prior: devuelve la probabilidad a la escala real
        pred = pred / (pred + (1 - pred) * factor)
    return (pred, m) if devolver else pred


def fit_logistica(Xtr, ytr, Xva, C_=1.0, peso=None):
    from sklearn.linear_model import LogisticRegression
    R = Regularizador("lineal")
    A = R.fit_transform(Xtr, ytr)
    B = R.transform(Xva)[A.columns]
    A = A.select_dtypes("number"); B = B[A.columns]
    m = LogisticRegression(C=C_, max_iter=3000, class_weight="balanced" if peso else None)
    m.fit(A, ytr)
    return m.predict_proba(B)[:, 1]


def regla(Xtr, ytr, Xva, k=1):
    """Sin modelo: elige (con train) las k variables numéricas de mayor Gini y su dirección."""
    g = {}
    for v in Xtr.columns:
        if pd.api.types.is_numeric_dtype(Xtr[v]) and Xtr[v].notna().mean() > 0.5:
            x = Xtr[v].fillna(Xtr[v].median())
            if x.nunique() > 1:
                g[v] = M.gini(ytr, x)
    top = sorted(g, key=lambda v: -abs(g[v]))[:k]
    s = np.zeros(len(Xva))
    for v in top:
        x = Xva[v].fillna(Xtr[v].median())
        s += _rank(x if g[v] > 0 else -x)
    return s / max(len(top), 1)


# ------------------------------------------------------------------ OOF
def oof(fn, X, y, folds, **kw):
    p = np.zeros(len(y))
    for tr, va in folds:
        p[va] = fn(X.iloc[tr], y.iloc[tr], X.iloc[va], **kw)
    return p


CANDIDATOS = {
    "regla_1var": (regla, dict(k=1)),
    "regla_top3": (regla, dict(k=3)),
    "logistica": (fit_logistica, {}),
    "lgbm": (fit_lgbm, {}),
    "lgbm_pesos": (fit_lgbm, dict(peso=True)),
    "lgbm_submuestra": (fit_lgbm, dict(submuestra=4)),
}


def comparar(D, params_lgbm=None):
    tr, vs = D["train"], D["vars"]
    X, y = tr[vs], tr["target"].astype(int)
    folds = pliegues(y)
    preds, filas = {}, []
    for nombre, (fn, kw) in CANDIDATOS.items():
        kw = dict(kw)
        if nombre.startswith("lgbm") and params_lgbm:
            kw["params"] = params_lgbm
        preds[nombre] = oof(fn, X, y, folds, **kw)
        filas.append(dict(modelo=nombre, **M.resumen_clasif(y, preds[nombre])))
        print(f"  {nombre:<16} Gini OOF {filas[-1]['gini']:.4f}  AUC-PR {filas[-1]['auc_pr']:.4f}  "
              f"prob media {filas[-1]['prob_media']:.3f} (real {filas[-1]['tasa_real']:.3f})")
    preds["ensamble"] = (_rank(preds["lgbm"]) + _rank(preds["logistica"])) / 2
    filas.append(dict(modelo="ensamble", **M.resumen_clasif(y, preds["ensamble"])))
    print(f"  {'ensamble':<16} Gini OOF {filas[-1]['gini']:.4f}")
    tabla = pd.DataFrame(filas)
    # las reglas y el ensamble de rankings no son probabilidades: su brier no aplica
    tabla.loc[tabla.modelo.str.startswith(("regla", "ensamble")), ["brier", "prob_media"]] = np.nan
    return tabla, preds, folds
