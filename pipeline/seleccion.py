"""
PASO 7 · EMBUDO DE SELECCIÓN (decisiones solo con train; PSI compara train vs validación).

  F1 copias      : dos variables con los mismos valores -> se queda una
  F2 estabilidad : PSI > 0.25 -> la variable cambió de distribución entre periodos;
                   el modelo aprendería un mundo que ya no existe. (También atrapa fugas.)
  F3 fuga        : Gini individual > 0.5 -> una sola variable "adivina" demasiado: casi
                   siempre es información posterior al corte. NO se borra sola: va a revisión.
  F4 sin señal   : Gini < 0.02 -> no separa nada
  F5 redundancia : Spearman > 0.9 entre dos -> me quedo con la de mayor Gini
  IV (Information Value): lenguaje de riesgo bancario. <0.02 nada, 0.1-0.3 media,
                   >0.5 sospechosa. Lo pide cualquier jurado de banco.

Gini = 2*AUC - 1 : 0 = azar, 1 = perfecto. Es la métrica estándar de scoring en banca.
"""
import numpy as np
import pandas as pd

import config as C


def auc_rapido(x, y):
    """AUC por rangos (Mann-Whitney), sin sklearn. Nulos = grupo propio en el extremo bajo."""
    x = pd.Series(x).astype(float)
    x = x.fillna(x.min() - 1 if x.notna().any() else 0)
    r = x.rank(method="average").values
    y = np.asarray(y)
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return 0.5
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def gini(x, y):
    return abs(2 * auc_rapido(x, y) - 1)


def _bins(x_ref, n=10):
    q = np.unique(np.nanquantile(x_ref, np.linspace(0, 1, n + 1)))
    return q if len(q) > 2 else np.unique(np.concatenate([q, [np.nanmin(x_ref) - 1, np.nanmax(x_ref) + 1]]))


def psi(ref, act, n=10):
    """Population Stability Index: <0.1 estable, 0.1-0.25 vigilar, >0.25 cambió."""
    ref, act = pd.Series(ref).astype(float), pd.Series(act).astype(float)
    if ref.notna().sum() < 10:
        return 0.0
    b = _bins(ref.dropna().values, n)
    def dist(s):
        h = np.histogram(s.dropna().clip(b[0], b[-1]), bins=b)[0].astype(float)
        h = np.append(h, s.isna().sum())
        return np.clip(h / max(h.sum(), 1), 1e-4, None)
    p, q = dist(ref), dist(act)
    return float(np.sum((q - p) * np.log(q / p)))


def iv(x, y, n=10):
    x = pd.Series(x).astype(float)
    try:
        g = pd.qcut(x, n, duplicates="drop").cat.add_categories("NULO").fillna("NULO")
    except Exception:
        return 0.0
    t = pd.DataFrame({"g": g, "y": np.asarray(y)}).groupby("g", observed=True).y.agg(["sum", "count"])
    b = (t["sum"] + 0.5) / (t["sum"].sum() + 0.5)
    m = (t["count"] - t["sum"] + 0.5) / ((t["count"] - t["sum"]).sum() + 0.5)
    return float(((b - m) * np.log(b / m)).sum())


def embudo(df, target="target", split="split", excluir=("id", "target_monto", "fecha_corte")):
    U = C.U
    tr = df[df[split] == "train"] if split in df else df
    va = df[df[split] != "train"] if split in df else None
    cand = [c for c in df.columns if c not in set(excluir) | {target, split}]
    filas = []
    num = {}
    for c in cand:
        s = tr[c]
        if not pd.api.types.is_numeric_dtype(s):  # categóricas: se evalúan por su tasa (frecuencia)
            s = s.astype("string").map(s.astype("string").value_counts(normalize=True)).astype(float)
        num[c] = s
        filas.append(dict(variable=c, gini=gini(s, tr[target]), iv=iv(s, tr[target]),
                          psi=psi(s, va[c] if (va is not None and pd.api.types.is_numeric_dtype(tr[c])) else s),
                          pct_nulo=float(tr[c].isna().mean())))
    r = pd.DataFrame(filas).set_index("variable")
    r["decision"], r["motivo"] = "QUEDA", ""
    def marcar(mask, dec, mot):
        sel = mask & (r.decision == "QUEDA")
        r.loc[sel, "decision"], r.loc[sel, "motivo"] = dec, mot
    # F1 copias
    h = {c: pd.util.hash_pandas_object(num[c].fillna(-9.99e18), index=False).sum() for c in cand}
    vistos = {}
    for c in r.sort_values("gini", ascending=False).index:
        if h[c] in vistos:
            r.loc[c, ["decision", "motivo"]] = ["FUERA", f"F1 copia de {vistos[h[c]]}"]
        vistos.setdefault(h[c], c)
    marcar(r.psi > U["psi_drop"], "FUERA", "F2 inestable (PSI > 0.25)")
    marcar((r.gini > U["gini_fuga"]) | (r.iv > U["iv_fuga"]), "REVISAR_FUGA", "F3 demasiado buena: ¿existe el día de decidir?")
    marcar(r.gini < U["gini_min"], "FUERA", "F4 sin señal (Gini < 0.02)")
    # F5 redundancia, de mayor a menor Gini
    vivas = r[r.decision == "QUEDA"].sort_values("gini", ascending=False).index.tolist()
    if len(vivas) > 1:
        corr = pd.DataFrame({c: num[c] for c in vivas}).rank().corr().abs()
        quedan = []
        for c in vivas:
            par = next((q for q in quedan if corr.loc[c, q] > U["spearman_max"]), None)
            if par:
                r.loc[c, ["decision", "motivo"]] = ["FUERA", f"F5 redundante con {par} (ρ={corr.loc[c, par]:.2f})"]
            else:
                quedan.append(c)
    r["alerta_psi"] = np.where(r.psi > U["psi_alerta"], "vigilar", "")
    orden = {"REVISAR_FUGA": 0, "QUEDA": 1, "FUERA": 2}
    return r.assign(_o=r.decision.map(orden)).sort_values(["_o", "gini"], ascending=[True, False]).drop(columns="_o").reset_index()


def ejecutar(bit, path_modelo, split_fn=None):
    print("\n== PASO 7 · SELECCIÓN ==")
    df = pd.read_parquet(path_modelo)
    if "target" not in df:
        print("  (sin target definido en config.TARGET -> se omite el embudo)")
        return None
    if split_fn:
        df["split"] = split_fn(df)
    elif "split" not in df:  # por defecto: 70/30 aleatorio estratificado. Mejor: fuera de tiempo.
        rng = np.random.default_rng(42)
        df["split"] = np.where(rng.random(len(df)) < 0.7, "train", "valid")
    r = embudo(df)
    r.to_csv(C.OUT_DIR / "seleccion_variables.csv", index=False, encoding="utf-8-sig")
    resumen = r.decision.value_counts().to_dict()
    bit.registrar("seleccion", "tabla_modelo", len(df), int((r.decision == "QUEDA").sum()), {"embudo": resumen})
    for _, x in r[r.decision == "REVISAR_FUGA"].iterrows():
        print(f"  ⚠ REVISAR FUGA: {x.variable}  Gini={x.gini:.2f}  IV={x.iv:.2f}")
    return r
