# PASO 2 · NAT: ¿ajustes.py apunta a cosas que existen? ¿Cómo se ve el problema?
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import ajustes as A

L = Path(A.CARPETA_SALIDAS) / "limpio"
con = duckdb.connect()


def columnas(tabla):
    return [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{L / tabla}.parquet'").fetchall()]


# 1) ¿existen las tablas y columnas que nombramos?
tablas = [p.stem for p in L.glob("*.parquet")]
pedidas = [(A.EMPRESAS, [A.ID, A.ZONA, A.RUBRO])] + [(t, [i, f, m]) for _, t, i, f, m in A.EVENTOS]
error = False
for tabla, cols in pedidas:
    if tabla not in tablas:
        print(f"[!!] no existe la tabla {tabla}. Hay: {tablas}")
        error = True
        continue
    faltan = [c for c in cols if c not in columnas(tabla)]
    if faltan:
        print(f"[!!] {tabla}: no existen {faltan}. Hay: {columnas(tabla)}")
        error = True
    else:
        print(f"[OK] {tabla}")
if error:
    raise SystemExit("Corrijan ajustes.py y vuelvan a correr.")

# 2) tasa base: % de empresas que convierte en cada corte
_, tt, ti, tf, tm = next(e for e in A.EVENTOS if e[1] == A.TARGET_TABLA)
for corte in (A.CORTE_ANTERIOR, A.CORTE):
    n_emp, n_pos = con.execute(f"""
        SELECT count(DISTINCT e.{A.ID}), count(DISTINCT t.{ti})
        FROM '{L / A.EMPRESAS}.parquet' e
        LEFT JOIN (SELECT * FROM '{L / tt}.parquet'
                   WHERE {tf} >= DATE '{corte}' AND {tf} < DATE '{corte}' + INTERVAL {A.HORIZONTE} MONTH
                     AND {A.TARGET_FILTRO}) t ON e.{A.ID} = t.{ti}""").fetchall()[0]
    print(f"corte {corte}: {n_pos:,} de {n_emp:,} empresas convierten = {n_pos / n_emp:.1%}")

# 3) capacidad
k = int(A.CAPACIDAD * n_emp)
print(f"capacidad: {k} empresas (el paso 5 las reparte por zona según CUPOS)")

# 4) gráfico: eventos del target por mes y los dos cortes
m = con.sql(f"""SELECT date_trunc('month', {tf}) mes, count(*) n FROM '{L / tt}.parquet'
                WHERE {A.TARGET_FILTRO} GROUP BY 1 ORDER BY 1""").df()
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(m.mes, m.n, width=20, color="#9a9993")
for corte, color, texto in ((A.CORTE_ANTERIOR, "#eb6834", "entrena"), (A.CORTE, "#2a78d6", "predice")):
    c = pd.Timestamp(corte)
    ax.axvspan(c, c + pd.DateOffset(months=A.HORIZONTE), color=color, alpha=0.15)
    ax.axvline(c, color=color)
    ax.text(c, m.n.max(), f" corte {corte}\n target para {texto}", color=color, va="top", fontsize=9)
ax.set_title("Eventos del target por mes: se entrena con el pasado y se predice el futuro", loc="left")
plt.tight_layout()
plt.savefig(Path(A.CARPETA_SALIDAS) / "2_linea_tiempo.png", dpi=120)
print("Gráfico: salidas/2_linea_tiempo.png")
