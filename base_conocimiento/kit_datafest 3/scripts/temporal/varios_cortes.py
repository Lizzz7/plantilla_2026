# TEMPORAL · KATH + SOPHIA: el mismo problema de clasificación, pero usando VARIOS cortes.
# ¿Cuándo? Cuando hay pocos positivos o el jurado pregunta "¿su modelo aguanta en el tiempo?".
# Idea: armar la tabla en varios cortes pasados, apilarlas (más filas para entrenar)
#       y validar SIEMPRE hacia adelante: entrenar con el pasado, medir en el futuro.
#   python temporal/varios_cortes.py
# Dos reglas que evitan fugas temporales:
#   1) un corte de entrenamiento c solo vale si c + HORIZONTE <= corte de examen (su target ya pasó)
#   2) la misma empresa aparece en varios cortes -> la validación cruzada agrupa por id
import importlib.util
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import ajustes as A

warnings.filterwarnings("ignore", message="Skipping features without any observed values")

# armar_tabla viene de 3_variables.py (el nombre empieza con número, por eso se importa así)
spec = importlib.util.spec_from_file_location("variables", BASE / "3_variables.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

# ---------------- AJUSTES DE ESTE SCRIPT ----------------
PASO_MESES = 3      # cada cuánto un corte de entrenamiento
N_CORTES = 3        # cuántos cortes apilar (máximo; se descartan los que no tienen historia completa)
HISTORIA = 6        # meses de historia IGUAL en todos los cortes (si no, el modelo aprende "cuánta historia hay")
# --------------------------------------------------------
A.HISTORIA = HISTORIA                                   # armar_tabla lee A.HISTORIA al momento de llamar
V.L = BASE / A.CARPETA_SALIDAS / "limpio"

# ¿desde cuándo hay datos? un corte necesita HISTORIA meses completos antes
inicio = min(pd.read_parquet(V.L / f"{t}.parquet", columns=[f])[f].dropna().min() for _, t, _, f, _ in A.EVENTOS)
inicio = pd.Timestamp(inicio)
print(f"datos desde {inicio.date()}: el primer corte válido es {(inicio + pd.DateOffset(months=HISTORIA)).date()}")


def cortes_para(examen):
    """cortes de entrenamiento válidos para un corte de examen dado"""
    examen = pd.Timestamp(examen)
    out = []
    for k in range(N_CORTES):
        c = examen - pd.DateOffset(months=A.HORIZONTE + PASO_MESES * k)
        assert c + pd.DateOffset(months=A.HORIZONTE) <= examen          # regla 1: su target ya pasó
        if c - pd.DateOffset(months=HISTORIA) >= inicio:                # historia completa, o no entra
            out.append(str(c.date()))
        else:
            print(f"  corte {c.date()} descartado: no tiene {HISTORIA} meses de historia")
    return out[::-1]


# examen = el corte más nuevo con target CONOCIDO. En la práctica A.CORTE ya lo tiene; en el reto real no,
# así que se usa A.CORTE_ANTERIOR automáticamente.
actual = V.armar_tabla(A.CORTE)
CORTE_EXAMEN = A.CORTE if actual.target.nunique() == 2 else A.CORTE_ANTERIOR
cortes = cortes_para(CORTE_EXAMEN)
print("cortes para entrenar:", cortes, "| examen:", CORTE_EXAMEN, f"| historia {HISTORIA} meses")
if len(cortes) < 2:
    sys.exit("Hay menos de 2 cortes con historia completa: bajen HISTORIA o PASO_MESES, o usen el flujo normal.")

tablas = []
for c in cortes:
    t = V.armar_tabla(c)
    t["corte"] = c
    tablas.append(t)
    print(f"  corte {c}: {len(t):,} filas, tasa {t.target.mean():.1%}")
apilada = pd.concat(tablas, ignore_index=True)
te = actual if CORTE_EXAMEN == A.CORTE else V.armar_tabla(CORTE_EXAMEN)
print(f"  examen {CORTE_EXAMEN}: {len(te):,} filas, tasa {te.target.mean():.1%}")

X_cols = [c for c in apilada.columns if c not in ("id", "target", "target_monto", "corte")]
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(apilada[c])]
NUM = [c for c in X_cols if c not in CAT]
for df in (apilada, te, actual):
    df[CAT] = df[CAT].fillna("NA").astype(str)


def modelo():
    log_signo = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)), feature_names_out="one-to-one")
    return make_pipeline(make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median"), log_signo, StandardScaler()), NUM),
        (OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), CAT)),
        LogisticRegression(C=0.1, max_iter=3000))


def gini(y, p):
    return 2 * roc_auc_score(y, p) - 1


# validación cruzada AGRUPADA por empresa (regla 2): la misma empresa nunca está en train y validación a la vez
cv = StratifiedGroupKFold(5, shuffle=True, random_state=42)
oof = np.zeros(len(apilada))
for i_tr, i_va in cv.split(apilada, apilada.target, groups=apilada.id):
    m = modelo().fit(apilada.loc[i_tr, X_cols], apilada.target.iloc[i_tr])
    oof[i_va] = m.predict_proba(apilada.loc[i_va, X_cols])[:, 1]
print(f"\nGini OOF apilado (agrupado por empresa): {gini(apilada.target, oof):.3f}")

# comparación justa en el examen: ¿apilar ayuda frente a usar solo el último corte?
res = {}
solo_ultimo = apilada[apilada.corte == cortes[-1]]
res["solo último corte"] = gini(te.target, modelo().fit(solo_ultimo[X_cols], solo_ultimo.target)
                                .predict_proba(te[X_cols])[:, 1])
res[f"{N_CORTES} cortes apilados"] = gini(te.target, modelo().fit(apilada[X_cols], apilada.target)
                                          .predict_proba(te[X_cols])[:, 1])
# estabilidad: entrenar con cada corte por separado, medir en el examen
for c in cortes:
    d = apilada[apilada.corte == c]
    res[f"solo corte {c}"] = gini(te.target, modelo().fit(d[X_cols], d.target).predict_proba(te[X_cols])[:, 1])
r = pd.Series(res).round(3)
print("\nGini en el examen (", CORTE_EXAMEN, ")\n", r.to_string())
print("\nLectura: si 'apilados' >= 'solo último', usen la apilada. Si cortes viejos dan Gini mucho menor,"
      "\nel comportamiento cambió (drift): pesen más los cortes recientes o usen menos cortes.")

fig, ax = plt.subplots(figsize=(7, 3.5))
r.plot.barh(ax=ax, color=["#2a78d6" if "apilados" in k else "#9a9993" for k in r.index])
ax.invert_yaxis()
ax.set_title("Gini en el examen: un corte vs varios cortes apilados", loc="left")
plt.tight_layout()
plt.savefig(BASE / A.CARPETA_SALIDAS / "temporal_varios_cortes.png", dpi=120)
print("Gráfico: salidas/temporal_varios_cortes.png")

# entrega: reentrenar con TODOS los cortes cuyo target ya pasó respecto de A.CORTE, y predecir A.CORTE
finales = cortes_para(A.CORTE)
todo = pd.concat([V.armar_tabla(c).assign(corte=c) for c in finales], ignore_index=True)
todo[CAT] = todo[CAT].fillna("NA").astype(str)
p = modelo().fit(todo[X_cols], todo.target).predict_proba(actual[X_cols])[:, 1]
pd.DataFrame({"id": actual.id, "prob": p}).to_parquet(BASE / A.CARPETA_SALIDAS / "prob_varios_cortes.parquet", index=False)
print(f"\nModelo final con cortes {finales} -> salidas/prob_varios_cortes.parquet"
      "\n(si gana a la versión de un corte, renómbrenlo a prob.parquet y corran 5_entregar.py)")
