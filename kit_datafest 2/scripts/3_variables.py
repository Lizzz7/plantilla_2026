# PASO 3 · KATH: una fila por empresa, con variables que SOLO miran antes del corte.
# Se arma dos veces: corte anterior (entrena, su target ya pasó) y corte actual (predice).
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import ajustes as A

S = Path(A.CARPETA_SALIDAS)
L = S / "limpio"
con = duckdb.connect()


def gini(y, x):                                  # qué tan bien ordena x al target: 0 azar, 1 perfecto
    from sklearn.metrics import roc_auc_score
    return 2 * roc_auc_score(y, x.fillna(x.median())) - 1


def armar_tabla(corte):
    d = f"DATE '{corte}'"
    # a) la empresa: sus columnas tal cual (sin las de FUERA); fechas -> días antes del corte
    base = con.sql(f"SELECT * FROM '{L / A.EMPRESAS}.parquet'").df().drop_duplicates(A.ID)
    base = base.drop(columns=[c for c in A.FUERA if c in base]).rename(columns={A.ID: "id"})
    for c in base.columns:
        if pd.api.types.is_datetime64_any_dtype(base[c]):
            base[c + "_dias"] = (pd.Timestamp(corte) - base[c]).dt.days
            base = base.drop(columns=c)

    # b) cada tabla de eventos: un resumen por empresa SOLO con fechas < corte
    for alias, tabla, i, f, m in A.EVENTOS:
        ev = con.sql(f"""
            SELECT {i} AS id,
                   count(*)                                             AS {alias}_n,
                   sum({m})                                             AS {alias}_monto,
                   avg({m})                                             AS {alias}_monto_prom,
                   count(*) FILTER (WHERE {f} >= {d} - INTERVAL 3 MONTH) AS {alias}_n_3m,
                   date_diff('day', max({f}), {d})                      AS {alias}_recencia
            FROM '{L / tabla}.parquet'
            WHERE {f} < {d} AND {f} >= {d} - INTERVAL {A.HISTORIA} MONTH   -- << la línea que evita la fuga
            GROUP BY 1""").df()
        base = base.merge(ev, on="id", how="left")
        base[[f"{alias}_n", f"{alias}_monto", f"{alias}_n_3m"]] = base[[f"{alias}_n", f"{alias}_monto", f"{alias}_n_3m"]].fillna(0)
        base[f"{alias}_recencia"] = base[f"{alias}_recencia"].fillna(A.HISTORIA * 31)   # nunca = muy antiguo

    # c) target: 1 si hubo un evento (con el filtro) en [corte, corte + horizonte)
    _, tt, ti, tf, tm = next(e for e in A.EVENTOS if e[1] == A.TARGET_TABLA)
    tg = con.sql(f"""SELECT {ti} AS id, 1 AS target, sum({tm}) AS target_monto FROM '{L / tt}.parquet'
                     WHERE {tf} >= {d} AND {tf} < {d} + INTERVAL {A.HORIZONTE} MONTH AND {A.TARGET_FILTRO}
                     GROUP BY 1""").df()
    base = base.merge(tg, on="id", how="left")
    base["target"] = base.target.fillna(0).astype(int)
    base["target_monto"] = base.target_monto.fillna(0)
    assert base.id.is_unique, "un JOIN duplicó empresas"
    return base.sort_values("id").reset_index(drop=True)


# (este bloque solo corre si ejecutas el archivo; así otros scripts pueden importar armar_tabla)
if __name__ == "__main__":
    entrena, predice = armar_tabla(A.CORTE_ANTERIOR), armar_tabla(A.CORTE)
    entrena.to_parquet(S / "entrena.parquet", index=False)
    predice.to_parquet(S / "predice.parquet", index=False)
    print(f"entrena: {len(entrena):,} filas, tasa {entrena.target.mean():.1%} | predice: {len(predice):,} filas")
    print("variables:", [c for c in entrena.columns if c not in ("id", "target", "target_monto")])

    # d) prueba de fuga: una variable SOLA no debería ordenar demasiado bien
    num = [c for c in entrena.select_dtypes("number").columns if c not in ("target", "target_monto")]
    g = pd.DataFrame({"entrena": [abs(gini(entrena.target, entrena[c])) for c in num],
                      "predice": [abs(gini(predice.target, predice[c])) if predice.target.nunique() == 2 else np.nan
                                  for c in num]}, index=num).sort_values("entrena")
    for v, r in g.iterrows():
        if r.max() > 0.5 or r.predice - r.entrena > 0.3:
            print(f"[!!] posible fuga: {v} (Gini {r.entrena:.2f} entrena / {r.predice:.2f} predice)")
    ax = g.plot.barh(color=["#eb6834", "#2a78d6"], figsize=(8, 5))
    ax.axvline(0.5, color="#e34948", linestyle="--")
    ax.set_title("Prueba de fuga: Gini de cada variable sola (más de 0.5 = sospecha)", loc="left")
    plt.tight_layout()
    plt.savefig(S / "3_fugas.png", dpi=120)
    print("Gráfico: salidas/3_fugas.png")
