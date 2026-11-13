"""
PASO 4 · SOPHIA — qué modelo usamos y cuánto mide de verdad.

Pregunta: ¿qué modelo gana con una validación honesta, y por cuánto frente a no tener modelo?

  python 4_modelo.py        (después del paso 3)

Qué hace, en orden:
  1. Filtro simple de variables (medido SOLO con la tabla que entrena):
       - sin señal: si sola no ordena nada (fuerza < MIN_SENAL), solo agrega ruido
       - repetida: si se parece > MAX_PARECIDO a otra que ya entró, dice lo mismo
  2. Compara los CANDIDATOS con la MISMA validación (5 pliegues; predicción "fuera de pliegue" = OOF).
  3. Elige el de mejor métrica; si uno MÁS SIMPLE (más arriba en la lista) queda a menos de TOLERANCIA, gana el simple.
  4. EXAMEN: si la tabla que predice tiene target (forma A con datos del periodo), mide ahí.
  5. Importancia por permutación: cuánto empeora la métrica si desordeno cada variable.

Métricas: clasificación -> Gini (2·AUC−1: qué tan bien ORDENA) · regresión -> R² (y Gini del orden).

QUÉ EDITAR SEGÚN EL RETO:
  - Probar otro modelo (Random Forest, XGBoost...)      -> agregarlo a CANDIDATOS (abajo)
  - La métrica oficial es otra (AUC-PR, F1, MAE...)     -> función metrica() (abajo)
  - Menos variables / más variables                     -> MIN_SENAL, MAX_PARECIDO
  - Muy pocos datos (< 2 000 filas)                      -> PLIEGUES = 3 y quedarse con regla/lineal
  - Montos con muchos ceros (regresión)                  -> probar lightgbm con objective="tweedie" o el monto
                                                           en dos partes (ver README, recetas)

Salidas: salidas/predicciones_modelo.parquet (id, prob o pred) · salidas/importancia.csv · gráficos 4_*
"""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor  # noqa: F401  (para CANDIDATOS)
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import make_scorer, r2_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from comun import AZUL, C, GRIS, NARANJA, REGRESION, SAL, alerta, es_binario, fuerza, gini, grafico, \
    guardar_grafico, guardar_resumen, pct, titulo

# >>> EDITABLE ---------------------------------------------------------------------------------
MIN_SENAL = 0.02       # fuerza mínima de una variable sola (Gini o Spearman) para entrar
MAX_PARECIDO = 0.90    # si dos variables se parecen más que esto (Spearman), se queda la más fuerte
TOLERANCIA = 0.005     # diferencia de métrica que aceptamos para preferir el modelo más simple
PLIEGUES = 5


def metrica(y, pred):
    """La métrica con la que se ELIGE el modelo. Cambien aquí si el enunciado pide otra."""
    if REGRESION:
        return r2_score(y, pred)
    return gini(y, pred)
    # Ejemplos: from sklearn.metrics import average_precision_score -> return average_precision_score(y, pred)


def log_con_signo(x):
    """1 000 000 -> 13.8 · 1 000 -> 6.9 · -50 -> -3.9: comprime las colas largas sin perder el orden."""
    return np.sign(x) * np.log1p(np.abs(x))


def preprocesar(num, cat):
    """Para modelos lineales: vacíos -> mediana, log a montos, misma escala; categorías -> columnas 0/1."""
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), FunctionTransformer(log_con_signo),
                              StandardScaler()), num),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=0.01), cat)])


# Candidatos de MÁS SIMPLE a MÁS COMPLEJO (el orden importa: ante empate gana el de arriba).
# Cada uno: nombre -> función(num, cat) que devuelve un modelo sin entrenar. "regla_1var" es especial.
CANDIDATOS = {
    "regla_1var": None,                                           # ordenar por la mejor variable sola
    "lineal": lambda num, cat: make_pipeline(preprocesar(num, cat),
                                             Ridge(alpha=10) if REGRESION else LogisticRegression(C=0.1, max_iter=3000)),
    "lightgbm": lambda num, cat: (lgb.LGBMRegressor if REGRESION else lgb.LGBMClassifier)(
        n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50, subsample=0.8,
        subsample_freq=1, colsample_bytree=0.8, random_state=C.SEMILLA, verbose=-1),
    # "random_forest": lambda num, cat: make_pipeline(preprocesar(num, cat), RandomForestClassifier(
    #     n_estimators=300, min_samples_leaf=20, n_jobs=-1, random_state=C.SEMILLA)),
}
# <<< FIN EDITABLE -----------------------------------------------------------------------------

titulo(f"PASO 4 · SOPHIA — qué modelo y cuánto mide ({C.TIPO_PROBLEMA})")
alertas = []
tr = pd.read_parquet(SAL / "tabla_entrena.parquet")
te = pd.read_parquet(SAL / "tabla_predice.parquet")
dic = pd.read_csv(SAL / "diccionario.csv").set_index("variable").significado.to_dict()
NOMBRE_METRICA = "R²" if REGRESION else "Gini"

if not REGRESION and not es_binario(tr.target):
    raise SystemExit(f"  El target tiene {tr.target.nunique()} valores: con TIPO_PROBLEMA='clasificacion' debe ser 0/1.")
FUERA = {"id", "target", "target_monto", "fecha_corte"}
X_cols = [c for c in tr.columns if c not in FUERA]
CAT = [c for c in X_cols if not pd.api.types.is_numeric_dtype(tr[c])]
NUM = [c for c in X_cols if c not in CAT]
y = tr.target.astype(float).to_numpy() if REGRESION else tr.target.astype(int).to_numpy()
y_ajuste = y          # (probado: en regresión entrenar en log y volver a soles sesga la predicción y baja el R²)
hay_examen = te.target.notna().any()
print(f"\n  Entrena: {len(tr):,} filas · " + (f"promedio {y.mean():,.0f}" if REGRESION else f"tasa {pct(y.mean())}")
      + f" · {len(NUM)} numéricas + {len(CAT)} categóricas")
print("  Examen: " + ("sí (la tabla que predice trae target)" if hay_examen else "no (target futuro): solo OOF"))


def preparar(df):
    """Mismo formato para entrenar y predecir: infinitos -> vacío, categorías como texto."""
    X = df[X_cols].copy()
    X[NUM] = X[NUM].astype(float).replace([np.inf, -np.inf], np.nan)
    for c in CAT:
        X[c] = X[c].astype("string").fillna("NA").astype(str)
    return X


Xtr, Xte = preparar(tr), preparar(te)

# ------------------------------------------------------------------ 1. filtro de variables
tasa_cat = {c: pd.Series(y).groupby(Xtr[c].to_numpy()).mean() for c in CAT}   # promedio del target por categoría
f_num = {c: fuerza(y, Xtr[c]) for c in NUM}
f_cat = {c: fuerza(y, Xtr[c].map(tasa_cat[c])) for c in CAT}
sin_senal = [c for c, g in {**f_num, **f_cat}.items() if not g >= MIN_SENAL]
quedan, repetidas = [], []
rangos = Xtr[NUM].rank()
for c in sorted((c for c in NUM if c not in sin_senal), key=f_num.get, reverse=True):
    gemela = next((k for k in quedan if abs(rangos[c].corr(rangos[k])) > MAX_PARECIDO), None)
    (repetidas if gemela else quedan).append(c)
NUM, CAT = quedan, [c for c in CAT if c not in sin_senal]
X_cols = NUM + CAT
Xtr, Xte = Xtr[X_cols], Xte[X_cols]
print(f"  Filtro: {len(sin_senal)} sin señal + {len(repetidas)} repetidas fuera -> quedan {len(X_cols)} variables")
if not X_cols:
    raise SystemExit("  No quedó ninguna variable con señal. Revisen el target (paso 2) o bajen MIN_SENAL.")


def a_lgb(X):
    """LightGBM: categorías como 'category' con las MISMAS categorías del entrenamiento."""
    X = X.copy()
    for c in CAT:
        X[c] = pd.Categorical(X[c], categories=sorted(Xtr[c].unique()))
    return X


mejor = max(NUM or X_cols, key=lambda c: f_num.get(c, 0))
signo = 1 if (gini(y, Xtr[mejor].fillna(Xtr[mejor].median())) if not REGRESION else
              Xtr[mejor].rank().corr(pd.Series(y).rank())) >= 0 else -1


def entrenar(nombre, X, yy):
    if CANDIDATOS[nombre] is None:                                # regla: no "aprende" pesos
        if REGRESION:                                             # ... salvo el promedio del target por decil
            cortes = np.unique(np.nanquantile(X[mejor].astype(float), np.linspace(0, 1, 11)))
            grupo = np.digitize(X[mejor].astype(float).fillna(Xtr[mejor].median()), cortes[1:-1])
            return dict(cortes=cortes, promedio=pd.Series(yy).groupby(grupo).mean(), general=float(np.mean(yy)))
        return None
    m = CANDIDATOS[nombre](NUM, CAT)
    m.fit(a_lgb(X) if nombre == "lightgbm" else X, yy)
    return m


def predecir(nombre, m, X):
    """Probabilidad (clasificación) o valor predicho (regresión)."""
    if CANDIDATOS[nombre] is None:                                # regla: ordenar por la mejor variable
        x = X[mejor].astype(float).fillna(Xtr[mejor].median())
        if REGRESION:                                             # promedio del target en su decil
            grupo = np.digitize(x, m["cortes"][1:-1])
            return pd.Series(grupo).map(m["promedio"]).fillna(m["general"]).to_numpy()
        return signo * x.to_numpy()
    X = a_lgb(X) if nombre == "lightgbm" else X
    return m.predict(X) if REGRESION else m.predict_proba(X)[:, 1]


# ------------------------------------------------------------------ 2. comparar con la misma validación
resultados = []
cv = KFold(PLIEGUES, shuffle=True, random_state=C.SEMILLA) if REGRESION else \
    StratifiedKFold(PLIEGUES, shuffle=True, random_state=C.SEMILLA)
for nombre in CANDIDATOS:
    oof = np.zeros(len(tr))
    try:
        for a, b in cv.split(Xtr, y):
            oof[b] = predecir(nombre, entrenar(nombre, Xtr.iloc[a], y_ajuste[a]), Xtr.iloc[b])
    except Exception as e:  # noqa: BLE001  -> un candidato roto no tumba a los demás
        alerta(f"{nombre} falló y se omite: {e}", alertas)
        continue
    resultados.append(dict(modelo=nombre, oof_metrica=metrica(y, oof), oof=oof))
    print(f"   {nombre:<13} {NOMBRE_METRICA} OOF = {resultados[-1]['oof_metrica']:.3f}")

res = pd.DataFrame(resultados)
best = res.oof_metrica.max()
elegido = next(r.modelo for r in res.itertuples() if r.oof_metrica >= best - TOLERANCIA)   # el más simple que empata
print(f"\n  Elegido: {elegido} (el más simple a menos de {TOLERANCIA} del mejor)")
if not REGRESION and best > 0.8:
    alerta(f"Gini {best:.2f} es sospechosamente alto: revisar fugas (paso 3)", alertas)

# ------------------------------------------------------------------ 3-4. examen y predicción final
finales = {}
for nombre in res.modelo:
    finales[nombre] = entrenar(nombre, Xtr, y_ajuste)
    if hay_examen:
        res.loc[res.modelo == nombre, "examen"] = metrica(te.target, predecir(nombre, finales[nombre], Xte))
modelo = finales[elegido]
pred = predecir(elegido, modelo, Xte)
if not REGRESION and CANDIDATOS[elegido] is None:                 # una regla no da probabilidad: ranking escalado
    pred = pd.Series(pred).rank(pct=True).to_numpy() * y.mean() * 2
col = "pred" if REGRESION else "prob"
salida = pd.DataFrame({"id": te.id, col: np.clip(pred, 0, None if REGRESION else 1)})
salida.to_parquet(SAL / "predicciones_modelo.parquet", index=False)
print(res.drop(columns="oof").round(3).to_string(index=False))
r_el = res[res.modelo == elegido].iloc[0]
if hay_examen and r_el.oof_metrica - r_el.examen > 0.05:
    alerta(f"El examen cae {r_el.oof_metrica - r_el.examen:.3f} frente al OOF: sobreajuste o fuga", alertas)

# ------------------------------------------------------------------ deciles
yv, sv, donde = (te.target.to_numpy(), pred, "examen") if hay_examen else (y, r_el.oof, "OOF de entrenamiento")
d = pd.DataFrame({"y": yv, "s": sv})
d["decil"] = pd.qcut(d.s.rank(method="first", ascending=False), 10, labels=range(1, 11))
dec = d.groupby("decil", observed=True).y.mean()
lift1 = dec.iloc[0] / d.y.mean()

# ------------------------------------------------------------------ 5. importancia por permutación
muestra = Xtr.sample(min(4000, len(Xtr)), random_state=C.SEMILLA)
ym = y_ajuste[Xtr.index.get_indexer(muestra.index)]
if CANDIDATOS[elegido] is None:
    imp = pd.DataFrame({"variable": [mejor], "caida": [f_num.get(mejor, 0)]})
else:
    puntaje = make_scorer(r2_score) if REGRESION else "roc_auc"
    pi = permutation_importance(modelo, a_lgb(muestra) if elegido == "lightgbm" else muestra, ym,
                                scoring=puntaje, n_repeats=3, random_state=C.SEMILLA)
    imp = pd.DataFrame({"variable": X_cols, "caida": pi.importances_mean * (1 if REGRESION else 2)})
imp = imp.sort_values("caida", ascending=False).head(12)


def sentido(v):
    """¿Cuando la variable sube, la predicción sube o baja? (las categorías no tienen dirección)"""
    if v not in NUM:
        return "categoría"
    x = Xte[v].astype(float)
    return "más → sube" if np.corrcoef(x.fillna(x.median()), pred)[0, 1] > 0 else "más → baja"


imp["sentido"] = imp.variable.map(sentido)
imp["significado"] = imp.variable.map(dic).fillna("")
imp.to_csv(SAL / "importancia.csv", index=False, encoding="utf-8-sig")
print("\n  Variables que más pesan (permutación):")
print(imp.round(4).to_string(index=False))

# ------------------------------------------------------------------ gráficos
fig, ax = grafico("4_modelos", "¿Qué modelo gana? Misma validación para todos",
                  f"{NOMBRE_METRICA} OOF (entrenamiento, {PLIEGUES} pliegues)" +
                  (" y en el examen (periodo que el modelo no vio)" if hay_examen else ""))
x = np.arange(len(res))
ax.bar(x - (0.2 if hay_examen else 0), res.oof_metrica, width=0.38, color=GRIS, label="OOF (entrena)")
if hay_examen:
    ax.bar(x + 0.2, res.examen, width=0.38, color=AZUL, label="examen")
for i, r in enumerate(res.itertuples()):
    v = r.examen if hay_examen else r.oof_metrica
    ax.text(i + (0.2 if hay_examen else 0), v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
ax.set_xticks(x, [f"{m}\n(ELEGIDO)" if m == elegido else m for m in res.modelo])
ax.set_ylabel(NOMBRE_METRICA)
ax.legend(frameon=False, fontsize=8.5)
graficos = [guardar_grafico(fig)]

titulo_dec = (f"El 10% con mayor predicción tiene {lift1:.1f} veces el promedio" if REGRESION else
              f"Si llamamos primero al 10% de arriba, convierte {lift1:.1f} veces el promedio")
fig, ax = grafico("4_deciles", titulo_dec,
                  ("Promedio real del target" if REGRESION else "Tasa de conversión real") + f" por decil · {donde}")
escala = 1 if REGRESION else 100
ax.bar(dec.index.astype(int), dec * escala, color=[AZUL] + [GRIS] * 9, width=0.7)
ax.axhline(d.y.mean() * escala, color=NARANJA, linestyle="--", linewidth=1.2)
ax.text(10.4, d.y.mean() * escala, "promedio", color=NARANJA, fontsize=8.5, va="bottom", ha="right")
for i, v in enumerate(dec, 1):
    ax.text(i, v * escala, f"{v:,.0f}" if REGRESION else f"{v:.0%}", ha="center", va="bottom", fontsize=8.5)
ax.set_xticks(range(1, 11), [f"D{i}" for i in range(1, 11)])
ax.set_xlabel("decil (D1 = el 10% con mayor predicción)")
ax.set_ylabel("promedio del target" if REGRESION else "% que convierte")
graficos.append(guardar_grafico(fig))

im = imp.iloc[::-1]
fig, ax = grafico("4_importancia", "¿Qué mira el modelo? Cuánto empeora si desordeno cada variable",
                  f"Caída del {NOMBRE_METRICA} al permutar la variable (más larga = más importante)", alto=4.8)
ax.barh(im.variable + "  (" + im.sentido + ")", im.caida, color=AZUL)
ax.set_xlabel(f"caída del {NOMBRE_METRICA}")
ax.tick_params(axis="y", labelsize=8)
graficos.append(guardar_grafico(fig))

regla = float(res.loc[res.modelo == "regla_1var", "examen" if hay_examen else "oof_metrica"].iloc[0]) \
    if "regla_1var" in set(res.modelo) else float("nan")
final = float(r_el.examen if hay_examen else r_el.oof_metrica)
frase = (f"Una regla simple (ordenar por {mejor}) da {NOMBRE_METRICA} {regla:.2f}; nuestro modelo ({elegido}) da "
         f"{final:.2f}" + (" en un periodo que no vio" if hay_examen else " en validación cruzada") +
         f". El 10% de arriba tiene {lift1:.1f} veces el promedio.")
print(f"\n  Frase para el jurado: \"{frase}\"")
guardar_resumen("4_modelo", dict(
    rol="Sophia", titulo="Paso 4 · Qué modelo y cuánto mide", pregunta="¿Qué modelo gana con una validación honesta?",
    numeros={"modelo elegido": elegido, f"{NOMBRE_METRICA} OOF": round(float(r_el.oof_metrica), 3),
             **({f"{NOMBRE_METRICA} examen": round(final, 3)} if hay_examen else {}),
             f"{NOMBRE_METRICA} regla simple": round(regla, 3), "lift decil 1": round(float(lift1), 2),
             "variables usadas": len(X_cols)},
    explicacion=[frase], alertas=alertas, graficos=graficos))
