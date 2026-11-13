# EXTRA · SOPHIA: ¿y si piden (o queremos probar) MÁS modelos?
# Compara 7 candidatos con la MISMA validación (5 pliegues OOF) y la métrica que elijas.
# Requiere haber corrido 3_variables.py (usa salidas/entrena.parquet y predice.parquet).
#   python extra/mas_modelos.py                 -> métrica gini
#   python extra/mas_modelos.py auc_pr          -> cualquier nombre de extra/metricas.py
#   python extra/mas_modelos.py gini rapido     -> salta los lentos (random forest, catboost)
# Si una librería no está instalada, ese modelo se salta (no se cae todo).
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ajustes as A
from extra import metricas as MET

NOMBRE_METRICA = sys.argv[1] if len(sys.argv) > 1 else "gini"
RAPIDO = "rapido" in sys.argv
METRICA = getattr(MET, NOMBRE_METRICA)
MENOR_ES_MEJOR = NOMBRE_METRICA in ("brier", "logloss")

S = Path(__file__).resolve().parents[1] / A.CARPETA_SALIDAS
tr, te = pd.read_parquet(S / "entrena.parquet"), pd.read_parquet(S / "predice.parquet")
tr, te = tr.sort_values("id").reset_index(drop=True), te.sort_values("id").reset_index(drop=True)
y = tr.target.values
X_cols = [c for c in tr.columns if c not in ("id", "target", "target_monto")]
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(tr[c])]
NUM = [c for c in X_cols if c not in CAT]
for df in (tr, te):
    df[CAT] = df[CAT].fillna("NA").astype(str)

# ---------- preparaciones: cada familia de modelo quiere los datos distinto ----------
log_signo = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)), feature_names_out="one-to-one")
prep_lineal = make_column_transformer(       # lineales: imputar, comprimir colas, escalar, one-hot
    (make_pipeline(SimpleImputer(strategy="median"), log_signo, StandardScaler()), NUM),
    (OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), CAT))
prep_arbol = make_column_transformer(        # árboles: NO necesitan escalar; categorías como números
    (SimpleImputer(strategy="median"), NUM),
    (OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CAT))
prep_nativo = make_column_transformer(       # boosting moderno acepta NaN: no imputamos
    ("passthrough", NUM),
    (OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-1), CAT))

CANDIDATOS = {
    "logistica": make_pipeline(prep_lineal, LogisticRegression(C=0.1, max_iter=3000)),
    "arbol": make_pipeline(prep_arbol, DecisionTreeClassifier(max_depth=5, min_samples_leaf=100, random_state=42)),
    "random_forest": make_pipeline(prep_arbol, RandomForestClassifier(
        n_estimators=300, min_samples_leaf=30, max_features=0.5, n_jobs=-1, random_state=42)),
    "hist_gb (sklearn)": make_pipeline(prep_nativo, HistGradientBoostingClassifier(
        learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=50, l2_regularization=1.0, random_state=42)),
}
try:
    import lightgbm as lgb
    CANDIDATOS["lightgbm"] = make_pipeline(prep_nativo, lgb.LGBMClassifier(
        n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=42))
except ImportError:
    print("lightgbm no instalado: se salta")
try:
    import xgboost as xgb
    CANDIDATOS["xgboost"] = make_pipeline(prep_nativo, xgb.XGBClassifier(
        n_estimators=300, learning_rate=0.03, max_depth=4, min_child_weight=20,
        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, n_jobs=-1, random_state=42))
except ImportError:
    print("xgboost no instalado: se salta")
try:
    from catboost import CatBoostClassifier   # usa las categorías tal cual (no necesita OrdinalEncoder)
    CANDIDATOS["catboost"] = CatBoostClassifier(iterations=400, learning_rate=0.05, depth=5,
                                                cat_features=CAT, verbose=0, random_seed=42,
                                                allow_writing_files=False)   # no crea la carpeta catboost_info
except ImportError:
    print("catboost no instalado: se salta")
if RAPIDO:
    CANDIDATOS.pop("random_forest", None)
    CANDIDATOS.pop("catboost", None)

# ---------- misma validación para todos ----------
cv = StratifiedKFold(5, shuffle=True, random_state=42)
oof, pred, tiempos = {}, {}, {}
for nombre, modelo in CANDIDATOS.items():
    t0 = time.time()
    o = np.zeros(len(tr))
    for i_tr, i_va in cv.split(tr, y):
        modelo.fit(tr.loc[i_tr, X_cols], y[i_tr])
        o[i_va] = modelo.predict_proba(tr.loc[i_va, X_cols])[:, 1]
    modelo.fit(tr[X_cols], y)
    oof[nombre], pred[nombre] = o, modelo.predict_proba(te[X_cols])[:, 1]
    tiempos[nombre] = time.time() - t0
    print(f"  {nombre:18s} {NOMBRE_METRICA} OOF = {METRICA(y, o):.4f}   ({tiempos[nombre]:.0f}s)")

# ---------- ensamble por RANGO: promediar posiciones, no probabilidades ----------
# (cada modelo tiene su propia escala de prob; el rango las pone en la misma escala)
def rango(v):
    return pd.Series(v).rank(pct=True).values

TOP = sorted(oof, key=lambda k: METRICA(y, oof[k]), reverse=not MENOR_ES_MEJOR)[:3]
if not MENOR_ES_MEJOR:          # brier/logloss necesitan probabilidades reales: ahí no se ensambla por rango
    oof["ensamble_top3"] = np.mean([rango(oof[k]) for k in TOP], axis=0)
    pred["ensamble_top3"] = np.mean([rango(pred[k]) for k in TOP], axis=0)
    tiempos["ensamble_top3"] = sum(tiempos[k] for k in TOP)
    print(f"  ensamble de {TOP}")

res = pd.DataFrame({f"{NOMBRE_METRICA}_oof": {k: METRICA(y, v) for k, v in oof.items()},
                    "segundos": tiempos})
if te.target.nunique() == 2:
    res[f"{NOMBRE_METRICA}_examen"] = {k: METRICA(te.target, v) for k, v in pred.items()}
res = res.sort_values(f"{NOMBRE_METRICA}_oof", ascending=MENOR_ES_MEJOR)
print("\n", res.round(4))

# regla de elección: el mejor OOF; si uno más SIMPLE está a menos de 0.005, gana el simple
ORDEN_SIMPLE = ["logistica", "arbol", "hist_gb (sklearn)", "lightgbm", "xgboost", "random_forest",
                "catboost", "ensamble_top3"]
col = res[f"{NOMBRE_METRICA}_oof"]
mejor = col.min() if MENOR_ES_MEJOR else col.max()
cerca = [m for m in ORDEN_SIMPLE if m in col and abs(col[m] - mejor) <= 0.005]
print(f"\nelegido: {cerca[0]}  (mejor OOF {mejor:.4f}; se prefiere el más simple a <0.005)")

pd.DataFrame({"id": te.id, "prob": pred[cerca[0]]}).to_parquet(S / "prob_mas_modelos.parquet", index=False)
print("Guardado salidas/prob_mas_modelos.parquet  (para usarlo, renómbralo a prob.parquet y corre 5_entregar.py)")
print("  ojo: el ensamble devuelve RANGOS 0-1, no probabilidades; si el entregable pide prob, usa un modelo solo")

fig, ax = plt.subplots(figsize=(8, 4))
cols = [c for c in res.columns if c != "segundos"]
res[cols].plot.barh(ax=ax, color=["#2a78d6", "#9a9993"][: len(cols)])
ax.invert_yaxis()
ax.set_title(f"{NOMBRE_METRICA} por modelo (misma validación)", loc="left")
plt.tight_layout()
plt.savefig(S / "extra_mas_modelos.png", dpi=120)
print("Gráfico: salidas/extra_mas_modelos.png")
