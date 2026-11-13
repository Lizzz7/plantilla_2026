# PASO 4 · SOPHIA: comparar 3 modelos con la MISMA validación y elegir.
# Entrena con el corte anterior; examina con el actual (si su target ya se conoce).
from pathlib import Path

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import make_column_transformer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

import ajustes as A

S = Path(A.CARPETA_SALIDAS)
tr, te = pd.read_parquet(S / "entrena.parquet"), pd.read_parquet(S / "predice.parquet")
y = tr.target
X_cols = [c for c in tr.columns if c not in ("id", "target", "target_monto")]
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(tr[c])]   # texto = categoría
NUM = [c for c in X_cols if c not in CAT]
for df in (tr, te):                                   # categorías como texto; las raras quedan "NA"
    df[CAT] = df[CAT].fillna("NA").astype(str)


def gini(y, p):
    return 2 * roc_auc_score(y, p) - 1


# 1) los candidatos, de simple a complejo
log_signo = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)), feature_names_out="one-to-one")  # colas largas
logistica = make_pipeline(
    make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median"), log_signo, StandardScaler()), NUM),
        (OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), CAT)),
    LogisticRegression(C=0.1, max_iter=3000))
arboles = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50,
                             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=42)
Xtr_lgb = tr[X_cols].astype({c: "category" for c in CAT})
Xte_lgb = te[X_cols].astype({c: pd.CategoricalDtype(Xtr_lgb[c].cat.categories) for c in CAT})

# regla simple: ordenar por la mejor variable sola (lo que haría alguien sin modelo)
mejor = max(NUM, key=lambda c: abs(gini(y, tr[c].fillna(tr[c].median()))))
signo = np.sign(gini(y, tr[mejor].fillna(tr[mejor].median())))

# 2) misma validación para todos: 5 pliegues, cada fila se predice con un modelo que no la vio (OOF)
cv = StratifiedKFold(5, shuffle=True, random_state=42)
oof = {"regla": signo * tr[mejor].fillna(tr[mejor].median()),
       "logistica": cross_val_predict(logistica, tr[X_cols], y, cv=cv, method="predict_proba")[:, 1],
       "lightgbm": cross_val_predict(arboles, Xtr_lgb, y, cv=cv, method="predict_proba")[:, 1]}
logistica.fit(tr[X_cols], y)
arboles.fit(Xtr_lgb, y)
pred = {"regla": signo * te[mejor].fillna(tr[mejor].median()),
        "logistica": logistica.predict_proba(te[X_cols])[:, 1],
        "lightgbm": arboles.predict_proba(Xte_lgb)[:, 1]}

hay_examen = te.target.nunique() == 2
res = pd.DataFrame({"gini_oof": {k: gini(y, v) for k, v in oof.items()}})
if hay_examen:
    res["gini_examen"] = {k: gini(te.target, v) for k, v in pred.items()}
print(res.round(3))

# 3) elegir: el mejor OOF; si el más simple está a menos de 0.005, gana el simple
elegido = next(m for m in ["regla", "logistica", "lightgbm"] if res.gini_oof[m] >= res.gini_oof.max() - 0.005)
if elegido == "regla":
    elegido = "logistica"                               # la regla no da probabilidades
print(f"elegido: {elegido}   (regla simple = ordenar por {mejor})")
if res.gini_oof.max() > 0.8:
    print("[!!] Gini > 0.8: sospechen una fuga antes de celebrar")
pd.DataFrame({"id": te.id, "prob": pred[elegido]}).to_parquet(S / "prob.parquet", index=False)

# 4) gráficos: comparación, deciles e importancia
ax = res.plot.bar(rot=0, color=["#9a9993", "#2a78d6"][: res.shape[1]], figsize=(7, 4))
ax.set_title("Gini por modelo con la misma validación", loc="left")
plt.tight_layout()
plt.savefig(S / "4_modelos.png", dpi=120)

yv, pv = (te.target, pred[elegido]) if hay_examen else (y, oof[elegido])
dec = pd.qcut(pd.Series(pv).rank(method="first", ascending=False), 10, labels=range(1, 11))
tasa = pd.Series(np.asarray(yv)).groupby(np.asarray(dec)).mean()
plt.figure(figsize=(7, 4))
plt.bar(tasa.index, tasa * 100, color=["#2a78d6"] + ["#9a9993"] * 9)
plt.axhline(np.mean(yv) * 100, color="#eb6834", linestyle="--")
plt.title(f"% que convierte por decil (D1 = 10% de arriba): lift {tasa.iloc[0] / np.mean(yv):.1f}x", loc="left")
plt.tight_layout()
plt.savefig(S / "4_deciles.png", dpi=120)

modelo, Xi = (logistica, tr[X_cols]) if elegido == "logistica" else (arboles, Xtr_lgb)
pi = permutation_importance(modelo, Xi.sample(3000, random_state=1), y.loc[Xi.sample(3000, random_state=1).index],
                            scoring="roc_auc", n_repeats=3, random_state=1)
imp = pd.Series(2 * pi.importances_mean, index=X_cols).sort_values().tail(10)
print("variables que más pesan:\n", imp.sort_values(ascending=False).round(4))
fig, ax = plt.subplots(figsize=(7, 4))                 # figura nueva (si no, se dibuja encima de la anterior)
imp.plot.barh(ax=ax, color="#2a78d6", title="Cuánto cae el Gini si desordeno cada variable")
plt.tight_layout()
plt.savefig(S / "4_importancia.png", dpi=120)
print("Gráficos: 4_modelos.png, 4_deciles.png, 4_importancia.png")
