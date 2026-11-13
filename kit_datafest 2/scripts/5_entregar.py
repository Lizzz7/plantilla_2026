# PASO 5 · LIZ: a quién llamar (valor esperado + cupos por zona) y el CSV de entrega.
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import ajustes as A

S = Path(A.CARPETA_SALIDAS)
tr, te = pd.read_parquet(S / "entrena.parquet"), pd.read_parquet(S / "predice.parquet")
d = te[["id", A.ZONA, A.RUBRO, "target"]].merge(pd.read_parquet(S / "prob.parquet"), on="id")

# 1) monto si convierte = mediana de lo que financiaron las de su rubro (en el corte anterior)
positivos = tr[tr.target == 1]
mediana_rubro = positivos.groupby(A.RUBRO).target_monto.median()
d["monto"] = d[A.RUBRO].map(mediana_rubro).fillna(positivos.target_monto.median())
d["valor"] = d.prob * d.monto                       # valor esperado = probabilidad x monto

# 2) cupos por zona que sumen exactamente la capacidad (método del resto mayor)
k = int(A.CAPACIDAD * len(d))
exacto = {z: k * v / sum(A.CUPOS.values()) for z, v in A.CUPOS.items()}
cupo = {z: int(x) for z, x in exacto.items()}
for z in sorted(exacto, key=lambda z: exacto[z] - cupo[z], reverse=True)[: k - sum(cupo.values())]:
    cupo[z] += 1

# 3) dentro de cada zona, las de mayor valor hasta llenar su cupo
d["priorizado"] = 0
for z, n in cupo.items():
    d.loc[d[d[A.ZONA] == z].nlargest(n, "valor").index, "priorizado"] = 1
pri = d[d.priorizado == 1]
print("cupos:", cupo, "| priorizadas:", len(pri))
if d.target.nunique() == 2:
    print(f"priorizadas convierten {pri.target.mean():.1%} vs {d.target.mean():.1%} de la base "
          f"({pri.target.mean() / d.target.mean():.1f}x)")

# 4) archivo de entrega con los nombres del enunciado + controles
sub = d[list(A.ENTREGA)].rename(columns=A.ENTREGA)
sub.to_csv(S / "submission.csv", index=False)
controles = {"1 fila por empresa": d.id.is_unique, "prob entre 0 y 1": d.prob.between(0, 1).all(),
             "sin vacíos": sub.notna().all().all(), f"priorizadas = {k}": len(pri) == k}
for texto, ok in controles.items():
    print(("[OK] " if ok else "[!!] ") + texto)

# 5) gráfico: conversión por rubro (hallazgo de negocio)
r = tr.groupby(A.RUBRO).target.mean().sort_values() * 100
ax = r.plot.barh(color=["#2a78d6" if v > tr.target.mean() * 100 else "#9a9993" for v in r], figsize=(7, 4))
ax.axvline(tr.target.mean() * 100, color="#eb6834", linestyle="--")
ax.set_title("% que toma factoring por rubro (línea = promedio)", loc="left")
plt.tight_layout()
plt.savefig(S / "5_rubros.png", dpi=120)
print("Entrega: salidas/submission.csv | gráfico: salidas/5_rubros.png")
