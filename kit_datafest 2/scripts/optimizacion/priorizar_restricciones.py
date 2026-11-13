# OPTIMIZACIÓN · LIZ: "prioricen el 10%" + restricciones (cupos, mínimos, presupuesto, ejecutivos).
# Dos formas de resolver y se comparan:
#   A) GREEDY (codicioso): ordenar por valor y tomar mientras no se rompa ninguna regla. Simple, explicable.
#   B) PROGRAMACIÓN ENTERA (PuLP): el óptimo matemático. Gana cuando hay presupuesto o reglas que chocan.
#   python optimizacion/priorizar_restricciones.py          (usa salidas/prob.parquet y predice.parquet)
#   python optimizacion/priorizar_restricciones.py demo     (inventa una columna de ejecutivo para practicar)
# Cambien SOLO el bloque AJUSTES; si una restricción no aplica, pónganla en None.
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import ajustes as A

S = BASE / A.CARPETA_SALIDAS

# ===================== AJUSTES =====================
CAPACIDAD = 0.10                 # % de empresas que se pueden contactar (o un número entero: 500)
OBJETIVO = "valor"               # "valor" = prob x monto (soles esperados) | "prob" = solo probabilidad
CUPOS_ZONA = "proporcional"      # "proporcional" (según el tamaño de cada zona) | A.CUPOS (pesos) | None
MIN_POR_RUBRO = 5                # cada rubro con al menos N empresas (diversificar) | None
MAX_POR_RUBRO = 0.30             # ningún rubro más del 30% de la lista (concentración) | None
PRESUPUESTO = 0.70               # suma de montos <= 70% de lo que sumaría el top sin reglas (o soles) | None
COL_EJECUTIVO = "ejecutivo"      # columna con el ejecutivo de cada empresa | None
MAX_POR_EJECUTIVO = 15           # cada ejecutivo atiende como máximo N | None
PROB_MINIMA = 0.05               # no contactar si la prob es menor (no vale la llamada) | None
EXCLUIR = None                   # filtro pandas de quiénes NO pueden entrar, ej.: "segmento == 'CORPORATIVO'"
# ===================================================

te = pd.read_parquet(S / "predice.parquet")
tr = pd.read_parquet(S / "entrena.parquet")
d = te.merge(pd.read_parquet(S / "prob.parquet"), on="id")
if "demo" in sys.argv and COL_EJECUTIVO not in d:
    d[COL_EJECUTIVO] = "EJ" + (pd.util.hash_pandas_object(d.id, index=False) % 60).astype(str).str.zfill(2)
    print("(demo) columna 'ejecutivo' inventada: 60 ejecutivos")

positivos = tr[tr.target == 1]
d["monto"] = d[A.RUBRO].map(positivos.groupby(A.RUBRO).target_monto.median()).fillna(positivos.target_monto.median())
d["valor"] = d.prob * d.monto
d["obj"] = d[OBJETIVO]

# ---------- traducir los ajustes a números ----------
N = len(d)
K = int(CAPACIDAD) if CAPACIDAD >= 1 else int(round(CAPACIDAD * N))
elegibles = pd.Series(True, index=d.index)
if PROB_MINIMA is not None:
    elegibles &= d.prob >= PROB_MINIMA
if EXCLUIR:
    elegibles &= ~d.eval(EXCLUIR)
print(f"Base {N:,} | capacidad K = {K} | elegibles {elegibles.sum():,}")


def resto_mayor(pesos, total):                    # reparte 'total' según pesos y que sume EXACTO
    exacto = {z: total * v / sum(pesos.values()) for z, v in pesos.items()}
    cupo = {z: int(x) for z, x in exacto.items()}
    for z in sorted(exacto, key=lambda z: exacto[z] - cupo[z], reverse=True)[: total - sum(cupo.values())]:
        cupo[z] += 1
    return cupo


if CUPOS_ZONA == "proporcional":
    cupo_zona = resto_mayor(d[A.ZONA].value_counts().to_dict(), K)
elif isinstance(CUPOS_ZONA, dict):
    cupo_zona = resto_mayor(CUPOS_ZONA, K)
else:
    cupo_zona = None
max_rubro = None if MAX_POR_RUBRO is None else (int(MAX_POR_RUBRO * K) if MAX_POR_RUBRO < 1 else MAX_POR_RUBRO)
if PRESUPUESTO is not None and PRESUPUESTO < 10:                 # proporción -> soles
    PRESUPUESTO = PRESUPUESTO * d[elegibles].nlargest(K, "obj").monto.sum()
usar_ejec = COL_EJECUTIVO is not None and MAX_POR_EJECUTIVO is not None and COL_EJECUTIVO in d
if COL_EJECUTIVO and not usar_ejec:
    print(f"(no hay columna '{COL_EJECUTIVO}': se ignora el máximo por ejecutivo; prueben con 'demo')")
print("cupos por zona:", cupo_zona)
print(f"rubros: mínimo {MIN_POR_RUBRO}, máximo {max_rubro} | presupuesto: "
      + (f"S/ {PRESUPUESTO:,.0f}" if PRESUPUESTO else "sin límite"))


# ---------- A) GREEDY ----------
def greedy():
    elegido = pd.Series(False, index=d.index)
    cuenta = {"zona": {}, "rubro": {}, "ejec": {}}
    gasto = 0.0

    def cabe(i):
        r = d.loc[i]
        if cupo_zona and cuenta["zona"].get(r[A.ZONA], 0) >= cupo_zona.get(r[A.ZONA], 0):
            return False
        if max_rubro and cuenta["rubro"].get(r[A.RUBRO], 0) >= max_rubro:
            return False
        if usar_ejec and cuenta["ejec"].get(r[COL_EJECUTIVO], 0) >= MAX_POR_EJECUTIVO:
            return False
        if PRESUPUESTO and gasto + r.monto > PRESUPUESTO:
            return False
        return True

    def tomar(i):
        nonlocal gasto
        r = d.loc[i]
        elegido[i] = True
        gasto += r.monto
        for k, col in [("zona", A.ZONA), ("rubro", A.RUBRO)] + ([("ejec", COL_EJECUTIVO)] if usar_ejec else []):
            cuenta[k][r[col]] = cuenta[k].get(r[col], 0) + 1

    orden = d[elegibles].sort_values("obj", ascending=False).index
    if MIN_POR_RUBRO:                                # 1) primero asegurar los mínimos, con los mejores de cada rubro
        for rubro, g in d[elegibles].groupby(A.RUBRO):
            for i in g.sort_values("obj", ascending=False).index:
                if cuenta["rubro"].get(rubro, 0) >= MIN_POR_RUBRO:
                    break
                if cabe(i):
                    tomar(i)
    for i in orden:                                  # 2) después llenar con los de mayor valor
        if elegido.sum() >= K:
            break
        if not elegido[i] and cabe(i):
            tomar(i)
    return elegido


# ---------- B) PROGRAMACIÓN ENTERA ----------
# Instalar: pip install "pulp<3"   (la 2.x trae el solver CBC adentro; la 4.x no).
# Si PuLP no está o no tiene solver, se usa scipy (HiGHS), que viene con scikit-learn: mismo resultado.
def entera():
    try:
        import pulp
        if pulp.LpSolverDefault is None:
            raise ImportError("PuLP sin solver")
    except ImportError as e:
        print(f"PuLP no disponible ({e}): uso scipy.optimize.milp")
        return entera_scipy()
    idx = d.index[elegibles]
    prob = pulp.LpProblem("priorizar", pulp.LpMaximize)
    if hasattr(prob, "add_variable_dict"):                       # PuLP 4.x
        x = prob.add_variable_dict("x", list(idx), cat="Binary")  # x_i = 1 si contactamos a la empresa i
    else:                                                        # PuLP 2.x (la que suele venir instalada)
        x = pulp.LpVariable.dicts("x", list(idx), cat="Binary")
    prob += pulp.lpSum(d.at[i, "obj"] * x[i] for i in idx)       # maximizar valor total
    prob += pulp.lpSum(x[i] for i in idx) <= K                   # capacidad
    sub = d.loc[idx]
    if cupo_zona:
        for z, n in cupo_zona.items():
            prob += pulp.lpSum(x[i] for i in sub.index[sub[A.ZONA] == z]) <= n
    for rubro, g in sub.groupby(A.RUBRO):
        if MIN_POR_RUBRO:
            prob += pulp.lpSum(x[i] for i in g.index) >= min(MIN_POR_RUBRO, len(g))
        if max_rubro:
            prob += pulp.lpSum(x[i] for i in g.index) <= max_rubro
    if usar_ejec:
        for e, g in sub.groupby(COL_EJECUTIVO):
            prob += pulp.lpSum(x[i] for i in g.index) <= MAX_POR_EJECUTIVO
    if PRESUPUESTO:
        prob += pulp.lpSum(d.at[i, "monto"] * x[i] for i in idx) <= PRESUPUESTO
    solver = pulp.LpSolverDefault                                # CBC (viene con PuLP); el nombre cambia entre versiones
    if solver is not None:
        solver.msg, solver.timeLimit = False, 60
    estado = prob.solve(solver)
    print(f"PuLP: {pulp.LpStatus[estado]}" + ("  <- revisen: reglas imposibles de cumplir juntas" if estado != 1 else ""))
    elegido = pd.Series(False, index=d.index)
    elegido[[i for i in idx if (x[i].value() or 0) > 0.5]] = True
    return elegido


def entera_scipy():                                # lo mismo que entera(), escrito como matrices
    from scipy.optimize import Bounds, LinearConstraint, milp
    sub = d[elegibles]
    filas, lo, hi = [np.ones(len(sub))], [0], [K]                  # cada fila = una restricción: lo <= A x <= hi
    if cupo_zona:
        for z, n in cupo_zona.items():
            filas.append((sub[A.ZONA] == z).values.astype(float)); lo.append(0); hi.append(n)
    for rubro, g in sub.groupby(A.RUBRO):
        m = (sub[A.RUBRO] == rubro).values.astype(float)
        filas.append(m); lo.append(min(MIN_POR_RUBRO or 0, len(g))); hi.append(max_rubro or np.inf)
    if usar_ejec:
        for e in sub[COL_EJECUTIVO].unique():
            filas.append((sub[COL_EJECUTIVO] == e).values.astype(float)); lo.append(0); hi.append(MAX_POR_EJECUTIVO)
    if PRESUPUESTO:
        filas.append(sub.monto.values); lo.append(0); hi.append(PRESUPUESTO)
    r = milp(c=-sub.obj.values, constraints=LinearConstraint(np.vstack(filas), lo, hi),  # milp minimiza: -valor
             integrality=np.ones(len(sub)), bounds=Bounds(0, 1), options={"time_limit": 60})
    print(f"scipy milp: {r.message}")
    elegido = pd.Series(False, index=d.index)
    if r.x is not None:
        elegido[sub.index[r.x > 0.5]] = True
    return elegido


def revisar(sel, nombre):
    s = d[sel]
    fila = {"metodo": nombre, "n": len(s), "valor_esperado": s.valor.sum(), "monto_total": s.monto.sum(),
            "cumple_capacidad": len(s) <= K,
            "cumple_zonas": (not cupo_zona) or all(s[A.ZONA].value_counts().get(z, 0) <= n for z, n in cupo_zona.items()),
            "cumple_min_rubro": (not MIN_POR_RUBRO) or all(
                s[A.RUBRO].value_counts().get(r, 0) >= min(MIN_POR_RUBRO, n)          # (si el rubro tiene menos, todas)
                for r, n in d[elegibles][A.RUBRO].value_counts().items()),
            "cumple_max_rubro": (not max_rubro) or s[A.RUBRO].value_counts().max() <= max_rubro,
            "cumple_presupuesto": (not PRESUPUESTO) or s.monto.sum() <= PRESUPUESTO + 1e-6,
            "cumple_ejecutivo": (not usar_ejec) or s[COL_EJECUTIVO].value_counts().max() <= MAX_POR_EJECUTIVO}
    if d.target.nunique() == 2:                                   # si ya sabemos qué pasó: ¿cuánto se ganó de verdad?
        fila["convierten"] = s.target.mean()
        fila["monto_real_capturado"] = s.target_monto.sum()
    return fila


sin_reglas = pd.Series(False, index=d.index)
sin_reglas[d.nlargest(K, "obj").index] = True
sel = {"top K sin reglas (referencia)": sin_reglas, "greedy": greedy(), "programacion entera": entera()}
if "scipy" in sys.argv:                                          # para comprobar que ambos solvers coinciden
    sel["entera (scipy)"] = entera_scipy()
tabla = pd.DataFrame([revisar(s, n) for n, s in sel.items()]).set_index("metodo")
pd.set_option("display.width", 200)
print("\n", tabla.T.to_string())
print("\nLectura: el 'top K sin reglas' es el techo; cada regla cuesta algo de valor (es el PRECIO de la regla)."
      "\nSi greedy y entera empatan, usen greedy (se explica en una frase). Si la entera gana, úsenla y digan cuánto.")

ganador = "programacion entera" if tabla.loc["programacion entera", "valor_esperado"] > \
    tabla.loc["greedy", "valor_esperado"] * 1.001 else "greedy"
out = d[["id", A.ZONA, A.RUBRO, "prob", "monto", "valor"]].copy()
out["priorizado"] = sel[ganador].astype(int)
out.to_csv(S / "priorizados_restricciones.csv", index=False)
print(f"\nGuardado: salidas/priorizados_restricciones.csv (método: {ganador})")

# gráfico: valor esperado por método + composición por zona
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
tabla.valor_esperado.plot.barh(ax=ax[0], color=["#9a9993", "#eb6834", "#2a78d6", "#1baf7a"][: len(tabla)])
ax[0].invert_yaxis()
ax[0].set_title("Valor esperado (S/) por método", loc="left")
comp = pd.DataFrame({n: d[s][A.ZONA].value_counts() for n, s in sel.items()}).fillna(0)
comp.plot.bar(ax=ax[1], rot=0, color=["#9a9993", "#eb6834", "#2a78d6", "#1baf7a"][: comp.shape[1]])
ax[1].set_title("Empresas priorizadas por zona", loc="left")
ax[1].legend(frameon=False, fontsize=8)
plt.tight_layout()
plt.savefig(S / "optim_restricciones.png", dpi=120)
print("Gráfico: salidas/optim_restricciones.png")
