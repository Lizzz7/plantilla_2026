# PASO 4 · SOPHIA (versión simple): ¿qué modelo usamos y cuánto mide?
# Entrada : entrena.parquet (corte anterior, con target) y predice.parquet (corte actual)
# Salida  : prob.parquet (id, prob [, monto_si_convierte, valor_esperado]) + 3 gráficos + notas en pantalla
# Bloques:  0 cargar · 1 alarma de fugas · 2 los 3 modelos · 3 medirlos igual · 4 elegir  5 ¿probabilidades creíbles? · 6 predecir · 7 monto (si hay) · 8 qué variables pesan · 9 gráficos
from pathlib import Path

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")                      # guarda gráficos sin abrir ventanas
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


def gini(y, p):
    """0 = azar, 1 = perfecto. Mide si el modelo pone arriba a los que sí convierten."""
    return 2 * roc_auc_score(y, p) - 1

# 0) CARGAR

S = Path(A.CARPETA_SALIDAS)
tr = pd.read_parquet(S / "entrena.parquet")          # pasado: aquí aprendemos (ya sabemos quién convirtió)
te = pd.read_parquet(S / "predice.parquet")          # presente: aquí predecimos
y = tr["target"]                                     # 1 = convirtió, 0 = no
X_cols = [c for c in tr.columns if c not in ("id", "target", "target_monto")]   # nunca: id, ni el futuro
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(tr[c])]           # texto (rubro, zona...)
NUM = [c for c in X_cols if c not in CAT]                                       # números
for df in (tr, te):
    df[CAT] = df[CAT].fillna("NA").astype(str)        # nulo en texto -> categoría "NA"

hay_examen = "target" in te and te["target"].nunique() == 2   # ¿el presente ya trae la respuesta? (simulacro sí)
print(f"Entrena: {len(tr):,} empresas, {len(X_cols)} variables, convierte {y.mean():.1%}")
print(f"Predice: {len(te):,} empresas · examen fuera de tiempo: {'SÍ' if hay_examen else 'NO'}\n")


# 1) ALARMA DE FUGAS: una variable SOLA no debería adivinar demasiado

sospechosas = []
for c in NUM:
    x = tr[c].fillna(tr[c].median())
    if x.nunique() > 1 and abs(gini(y, x)) > 0.5:     # > 0.5 sola = "sabe el futuro"
        sospechosas.append((c, round(abs(gini(y, x)), 2)))
if sospechosas:
    print("[!!] POSIBLE FUGA (¿existía este dato el día de decidir?):", sospechosas, "\n")


# 2) LOS 3 CANDIDATOS, de simple a complejo

# 2a) REGLA: ordenar por la mejor variable sola = lo que haría un ejecutivo sin modelo
mejor = max(NUM, key=lambda c: abs(gini(y, tr[c].fillna(tr[c].median()))))
signo = np.sign(gini(y, tr[mejor].fillna(tr[mejor].median())))   # +1 "más es mejor", -1 "más es peor"

# 2b) LOGÍSTICA = una balanza: cada variable suma o resta. Necesita números limpios y en la misma escala.
log_signo = FunctionTransformer(lambda x: np.sign(x) * np.log1p(np.abs(x)), feature_names_out="one-to-one")
logistica = make_pipeline(
    make_column_transformer(
        (make_pipeline(SimpleImputer(strategy="median"),   # vacío -> mediana
                       log_signo,                          # montos gigantes -> escala log
                       StandardScaler()), NUM),            # todas con media 0 y desviación 1
        (OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), CAT)),   # rubro -> columnas 0/1
    LogisticRegression(C=0.1, max_iter=3000))             # C chico = coeficientes prudentes

# 2c) LIGHTGBM = muchos árboles pequeños; cada uno corrige al anterior. Acepta vacíos y categorías.
arboles = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50,
                             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=42)
Xtr_lgb = tr[X_cols].astype({c: "category" for c in CAT})
Xte_lgb = te[X_cols].astype({c: pd.CategoricalDtype(Xtr_lgb[c].cat.categories) for c in CAT})  # mismas categorías


# 3) MEDIRLOS IGUAL: 5 pliegues; cada empresa la predice un modelo que NO la vio (OOF)

cv = StratifiedKFold(5, shuffle=True, random_state=42)
oof = {"regla": signo * tr[mejor].fillna(tr[mejor].median()),
       "logistica": cross_val_predict(logistica, tr[X_cols], y, cv=cv, method="predict_proba")[:, 1],
       "lightgbm": cross_val_predict(arboles, Xtr_lgb, y, cv=cv, method="predict_proba")[:, 1]}

logistica.fit(tr[X_cols], y)                          # modelos finales: con TODO el pasado
arboles.fit(Xtr_lgb, y)
pred = {"regla": signo * te[mejor].fillna(tr[mejor].median()),
        "logistica": logistica.predict_proba(te[X_cols])[:, 1],
        "lightgbm": arboles.predict_proba(Xte_lgb)[:, 1]}

res = pd.DataFrame({"gini_oof": {k: gini(y, v) for k, v in oof.items()}})
if hay_examen:
    res["gini_examen"] = {k: gini(te["target"], v) for k, v in pred.items()}
print(res.round(3), "\n")


# 4) ELEGIR: el mejor; si el más simple está a ≤ 0.005, gana el simple. La regla es solo la vara.

modelos = ["logistica", "lightgbm"]                   # de simple a complejo
tope = res.gini_oof[modelos].max()
elegido = next(m for m in modelos if res.gini_oof[m] >= tope - 0.005)
g_regla, g_mod = res.gini_oof["regla"], res.gini_oof[elegido]
print(f"ELEGIDO: {elegido}")
print(f"FRASE: 'Ordenar solo por {mejor} da Gini {g_regla:.3f}; el modelo da {g_mod:.3f} "
      f"({(g_mod / g_regla - 1):+.0%})'")
if g_regla >= g_mod - 0.005:
    print("[!] la regla simple empata con el modelo: decirlo con honestidad")
if hay_examen:
    caida = g_mod - res.gini_examen[elegido]
    print(f"Examen fuera de tiempo: {res.gini_examen[elegido]:.3f} "
          f"-> {'sano' if caida < 0.05 else '[!] cae mucho: sobreajuste, fuga o cambio de comportamiento'}")
if res.gini_oof.max() > 0.8:
    print("[!!] Gini > 0.8: sospechen una fuga antes de celebrar")


# 5) ¿PROBABILIDADES CREÍBLES? Por decil: lo que el modelo dice vs lo que pasó (OOF)

d = pd.DataFrame({"y": y.values, "p": oof[elegido]})
d["decil"] = pd.qcut(d.p.rank(method="first", ascending=False), 10, labels=range(1, 11))   # 1 = top 10%
tabla = d.groupby("decil", observed=True).agg(dice=("p", "mean"), real=("y", "mean"))
tabla["lift"] = tabla.real / y.mean()
print("\nPor decil (1 = 10% de arriba):\n", (tabla * [100, 100, 1]).round(1).rename(
      columns={"dice": "modelo dice %", "real": "convirtió %"}).to_string())
print(f"Lift D1 = {tabla.lift.iloc[0]:.1f}x  ->  'el 10% de arriba convierte {tabla.lift.iloc[0]:.1f} veces el promedio'")


# 6) PREDECIR el presente con el elegido

salida = pd.DataFrame({"id": te["id"].astype(str), "prob": pred[elegido]})


# 7) MONTO (solo si existe target_monto): valor esperado = prob × monto si convierte

if "target_monto" in tr:
    pos = tr["target_monto"] > 0                                   # solo quienes convirtieron
    log_monto = np.log1p(tr.loc[pos, "target_monto"])              # en log: los montos tienen cola larga
    reg = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=30,
                            verbose=-1, random_state=42)
    oof_log = cross_val_predict(reg, Xtr_lgb[pos], log_monto, cv=5)           # honesto: sin verse a sí misma
    duan = float(np.mean(np.exp(log_monto - oof_log)))             # corrige que volver de log subestima
    reg.fit(Xtr_lgb[pos], log_monto)
    salida["monto_si_convierte"] = np.expm1(reg.predict(Xte_lgb)) * duan
    salida["valor_esperado"] = salida.prob * salida.monto_si_convierte
    print(f"\nMonto: factor de Duan {duan:.2f} · valor esperado total S/ {salida.valor_esperado.sum():,.0f}")

salida.to_parquet(S / "prob.parquet", index=False)
print(f"\nGuardado prob.parquet ({len(salida):,} filas, columnas {list(salida.columns)})")


# 8) ¿QUÉ VARIABLES PESAN? Desordeno cada una y mido cuánto cae el Gini
#    (en el examen si existe: datos que el modelo no vio; si no, en el pasado y avisamos)

modelo = logistica if elegido == "logistica" else arboles
if hay_examen:
    Xi, yi = (te[X_cols] if elegido == "logistica" else Xte_lgb), te["target"]
else:
    Xi, yi = (tr[X_cols] if elegido == "logistica" else Xtr_lgb), y
    print("[!] sin examen: importancia medida en el pasado (puede exagerar)")
m = Xi.sample(min(3000, len(Xi)), random_state=1)
pi = permutation_importance(modelo, m, yi.loc[m.index], scoring="roc_auc", n_repeats=3, random_state=1)
imp = pd.Series(2 * pi.importances_mean, index=X_cols).sort_values(ascending=False).head(10)
print("\nVariables que más pesan (caída de Gini al desordenarlas):\n", imp.round(4).to_string())

# graf
ax = res.plot.bar(rot=0, color=["#9a9993", "#2a78d6"][: res.shape[1]], figsize=(7, 4))
ax.set_title("Gini por modelo con la misma validación", loc="left")
plt.tight_layout(); plt.savefig(S / "4_modelos.png", dpi=120); plt.close()

plt.figure(figsize=(7, 4))
plt.bar(tabla.index.astype(int), tabla.real * 100, color=["#2a78d6"] + ["#9a9993"] * 9)
plt.axhline(y.mean() * 100, color="#eb6834", linestyle="--")
plt.title(f"% que convierte por decil: lift D1 {tabla.lift.iloc[0]:.1f}x", loc="left")
plt.tight_layout(); plt.savefig(S / "4_deciles.png", dpi=120); plt.close()

fig, ax = plt.subplots(figsize=(7, 4))
imp.sort_values().plot.barh(ax=ax, color="#2a78d6", title="Cuánto cae el Gini si desordeno cada variable")
plt.tight_layout(); plt.savefig(S / "4_importancia.png", dpi=120); plt.close()
print("\nGráficos: 4_modelos.png, 4_deciles.png, 4_importancia.png")