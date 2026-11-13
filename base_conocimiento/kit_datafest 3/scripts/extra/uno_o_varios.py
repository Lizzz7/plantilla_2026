# EXTRA · SOPHIA: ¿un solo modelo para todas, o un modelo por grupo (zona, segmento)?
# Se decide MIDIENDO, con la misma validación. Compara:
#   A) un modelo global                     (todas las empresas juntas)
#   B) un modelo por grupo                  (ej. uno por zona: LIMA, NORTE...)
#   C) global + el grupo como variable      (ya lo hace A si la columna entra como categoría)
# Mide el Gini global y el Gini DENTRO de cada grupo, que es el que importa cuando hay cupos por zona
# (con cupos, solo se compara a una empresa de LIMA contra otras de LIMA).
#   python extra/uno_o_varios.py                -> agrupa por la zona de ajustes.py
#   python extra/uno_o_varios.py segmento       -> agrupa por otra columna
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ajustes as A

S = Path(__file__).resolve().parents[1] / A.CARPETA_SALIDAS
GRUPO = sys.argv[1] if len(sys.argv) > 1 else A.ZONA
MIN_POSITIVOS = 100          # un grupo con menos positivos que esto NO tiene modelo propio (usa el global)

tr = pd.read_parquet(S / "entrena.parquet").sort_values("id").reset_index(drop=True)
te = pd.read_parquet(S / "predice.parquet").sort_values("id").reset_index(drop=True)
X_cols = [c for c in tr.columns if c not in ("id", "target", "target_monto")]
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(tr[c])]
NUM = [c for c in X_cols if c not in CAT]
for df in (tr, te):
    df[CAT] = df[CAT].fillna("NA").astype(str)


def modelo():
    log_signo = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)), feature_names_out="one-to-one")
    return make_pipeline(make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median"), log_signo, StandardScaler()), NUM),
        (OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), CAT)),
        LogisticRegression(C=0.1, max_iter=3000))


def gini(y, p):
    return 2 * roc_auc_score(y, p) - 1 if len(set(y)) == 2 else np.nan


def gini_dentro(df, p):      # promedio ponderado del Gini dentro de cada grupo
    g = [(len(d), gini(d.target, p[d.index])) for _, d in df.groupby(GRUPO)]
    g = [(n, v) for n, v in g if not np.isnan(v)]
    return sum(n * v for n, v in g) / sum(n for n, _ in g)


cv = StratifiedKFold(5, shuffle=True, random_state=42)
print(f"Agrupando por '{GRUPO}':")
print(tr.groupby(GRUPO).target.agg(empresas="size", positivos="sum", tasa="mean").round(3).to_string(), "\n")

# A) global
oofA = np.zeros(len(tr))
for a, b in cv.split(tr, tr.target):
    oofA[b] = modelo().fit(tr.loc[a, X_cols], tr.target[a]).predict_proba(tr.loc[b, X_cols])[:, 1]
predA = modelo().fit(tr[X_cols], tr.target).predict_proba(te[X_cols])[:, 1]

# B) uno por grupo (los grupos chicos usan el global)
oofB, predB = oofA.copy(), predA.copy()
propios = []
for g, d in tr.groupby(GRUPO):
    if d.target.sum() < MIN_POSITIVOS:
        print(f"  {g}: {int(d.target.sum())} positivos < {MIN_POSITIVOS} -> usa el modelo global")
        continue
    propios.append(g)
    idx = d.index.values
    for a, b in cv.split(d, d.target):
        m = modelo().fit(d.iloc[a][X_cols], d.target.iloc[a])
        oofB[idx[b]] = m.predict_proba(d.iloc[b][X_cols])[:, 1]
    mt = te[GRUPO] == g
    if mt.any():
        predB[mt.values] = modelo().fit(d[X_cols], d.target).predict_proba(te.loc[mt, X_cols])[:, 1]

hay_examen = te.target.nunique() == 2
filas = []
for nombre, o, p in [("A) un modelo global", oofA, predA), (f"B) uno por {GRUPO}", oofB, predB)]:
    f = {"modelo": nombre, "gini_oof": gini(tr.target, o), f"gini_dentro_{GRUPO}_oof": gini_dentro(tr, pd.Series(o))}
    if hay_examen:
        f["gini_examen"] = gini(te.target, p)
        f[f"gini_dentro_{GRUPO}_examen"] = gini_dentro(te, pd.Series(p))
    filas.append(f)
r = pd.DataFrame(filas).set_index("modelo").round(3)
print("\n", r.to_string())
print(f"\nGrupos con modelo propio: {propios}")
mejor = r[f"gini_dentro_{GRUPO}_oof"].idxmax()
print(f"Decisión por OOF (dentro de {GRUPO}): {mejor}")
print("Regla: modelo por grupo SOLO si gana por > 0.01 y cada grupo tiene suficientes positivos;"
      "\nsi empatan, uno global (más datos por modelo, uno solo que explicar y mantener).")
