"""
PASO 5 · LIZ — a quién llamamos, cuánto vale y el archivo de entrega.

Pregunta: ¿a quién llamamos primero y la entrega está lista?

  python 5_priorizar_entregar.py        (después del paso 4)

Qué hace, en orden (cada parte es una FUNCIÓN editable de abajo):
  1. monto_si_convierte(): cuánto financiaría cada empresa SI convierte (por defecto: mediana de su rubro
     entre las que convirtieron al entrenar). En regresión el modelo ya predice el monto.
  2. valor esperado = probabilidad x monto si convierte.
  3. elegibles(): quiénes pueden entrar a la lista (todos / con lead / sin lead = "habilitar").
  4. priorizar(): dentro de cada zona, de mayor a menor valor, hasta llenar su cupo (o global si no hay cupos).
  5. Hallazgos de negocio (rubros, zonas, curva de captura) y ENTREGA con 6 controles automáticos.

QUÉ EDITAR SEGÚN EL RETO:
  - Otra forma de estimar el monto (regresor, historial propio, ventas)   -> monto_si_convierte()
  - Solo priorizar a quienes tienen/no tienen lead, u otra condición        -> config.ELEGIBLES o elegibles()
  - Ordenar por probabilidad y no por valor (foco en n° de clientes)        -> ORDENAR_POR = "prob"
  - Otra regla de reparto (mínimo por rubro, tope por segmento)             -> priorizar()
  - Nombres/columnas del archivo final                                      -> config.ENTREGA

Salidas: salidas/<config.ENTREGA archivo> · salidas/priorizados.csv · salidas/graficos/5_*.png
"""
import numpy as np
import pandas as pd

from comun import AZUL, C, GRIS, NARANJA, REGRESION, SAL, alerta, grafico, guardar_grafico, guardar_resumen, pct, \
    titulo

# >>> EDITABLE ---------------------------------------------------------------------------------
ORDENAR_POR = "valor"          # "valor" (prob x monto: más soles) o "prob" (más clientes que convierten)
MIN_CASOS_RUBRO = 30           # un rubro con menos casos usa la mediana global


def monto_si_convierte(d, tr):
    """Cuánto financiaría cada empresa SI convierte. d = empresas a predecir, tr = tabla que entrena."""
    if REGRESION:
        return d["pred"]                                          # el modelo ya predice el monto
    pos = tr[tr.target == 1]
    if "target_monto" not in pos or pos.target_monto.isna().all():
        return pd.Series(1.0, index=d.index)                      # sin montos: el valor = la probabilidad
    global_med = pos.target_monto.median()
    if "rubro" not in d or not C.RUBRO or C.RUBRO not in pos:
        return pd.Series(global_med, index=d.index)
    por_rubro = pos.groupby(C.RUBRO).target_monto.agg(["median", "size"])
    por_rubro = por_rubro[por_rubro["size"] >= MIN_CASOS_RUBRO]["median"]
    return d["rubro"].map(por_rubro).fillna(global_med)
    # Alternativa: el monto que la empresa ya financió antes (si existe la variable):
    # return d["ops__monto_prom"].where(d["ops__monto_prom"] > 0, global_med)


def elegibles(d):
    """True = puede entrar a la lista. Por defecto según config.ELEGIBLES."""
    if C.ELEGIBLES == "todos" or "lead" not in d:
        return pd.Series(True, index=d.index)
    con_lead = pd.to_numeric(d["lead"], errors="coerce").fillna(0) == 1
    return con_lead if C.ELEGIBLES == "con_lead" else ~con_lead


def priorizar(d, k):
    """Marca priorizado = 1 en k empresas elegibles. Con cupos: por zona, con 'resto mayor' para sumar k."""
    d["priorizado"] = 0
    cand = d[d.elegible]
    if C.CUPOS_ZONA and "zona" in d:
        tot = sum(C.CUPOS_ZONA.values())
        exacto = {z: k * v / tot for z, v in C.CUPOS_ZONA.items()}
        cupo = {z: int(x) for z, x in exacto.items()}
        for z in sorted(exacto, key=lambda z: exacto[z] - cupo[z], reverse=True)[: k - sum(cupo.values())]:
            cupo[z] += 1                                          # los cupos suman exactamente k
        for z, n in cupo.items():
            idx = cand[cand.zona == z].nlargest(n, ORDENAR_POR).index
            d.loc[idx, "priorizado"] = 1
            if len(idx) < n:
                alerta(f"Zona {z}: cupo {n} pero solo hay {len(idx)} empresas elegibles", alertas)
    else:
        d.loc[cand.nlargest(k, ORDENAR_POR).index, "priorizado"] = 1
    return d
# <<< FIN EDITABLE -----------------------------------------------------------------------------

titulo("PASO 5 · LIZ — priorizar y entregar")
alertas, graficos = [], []
tr = pd.read_parquet(SAL / "tabla_entrena.parquet")
te = pd.read_parquet(SAL / "tabla_predice.parquet")
pr = pd.read_parquet(SAL / "predicciones_modelo.parquet")
extra = {c: n for c, n in ((C.ZONA, "zona"), (C.RUBRO, "rubro"), (C.LEAD, "lead")) if c and c in te}
d = te[["id", "target", *extra]].merge(pr, on="id").rename(columns=extra)

# ------------------------------------------------------------------ 1-2. monto y valor
d["monto"] = monto_si_convierte(d, tr)
d["valor"] = d.pred if REGRESION else d.prob * d.monto
if REGRESION:
    d["prob"] = np.nan
print(f"\n  Monto si convierte: {'predicho por el modelo' if REGRESION else 'mediana por rubro'} · "
      f"valor esperado total {d.valor.sum():,.0f}")

# ------------------------------------------------------------------ 3-4. elegibles y priorizar
d["elegible"] = elegibles(d)
k = 0
if C.CAPACIDAD:
    k = int(C.CAPACIDAD * len(d)) if C.CAPACIDAD < 1 else int(C.CAPACIDAD)
    if ORDENAR_POR not in d or d[ORDENAR_POR].isna().all():
        alerta(f"ORDENAR_POR = '{ORDENAR_POR}' no está disponible: se ordena por 'valor'", alertas)
        ORDENAR_POR = "valor"
    d = priorizar(d, k)
    print(f"  Elegibles: {int(d.elegible.sum()):,} ({C.ELEGIBLES}) · priorizadas: {int(d.priorizado.sum()):,}")
else:
    d["priorizado"] = 0
    print("  Sin CAPACIDAD en config: no se arma lista (priorizado = 0 para todos)")
pri = d[d.priorizado == 1]

# ------------------------------------------------------------------ 5. hallazgos
hay_examen = d.target.notna().any()
base = d.target.mean() if hay_examen else tr.target.mean()
captura = None
if hay_examen and len(pri):
    lift_pri = pri.target.mean() / base
    print(f"  Las priorizadas: {pri.target.mean():,.2f} vs {base:,.2f} de la base ({lift_pri:.1f}x)" if REGRESION else
          f"  Las priorizadas convierten {pct(pri.target.mean())} vs {pct(base)} de la base ({lift_pri:.1f}x)")

if C.RUBRO and C.RUBRO in tr:
    rub = (tr.assign(r=tr[C.RUBRO].fillna("(vacío)")).groupby("r").target.agg(["mean", "size"])
           .query(f"size >= {MIN_CASOS_RUBRO}").sort_values("mean"))
    escala = 1 if REGRESION else 100
    fig, ax = grafico("5_rubros", "¿Qué rubros " + ("tienen mayor target?" if REGRESION else "convierten más?") + " (entrena)",
                      "Promedio por rubro · línea = promedio general", alto=max(3.5, 0.3 * len(rub) + 1))
    ax.barh(rub.index, rub["mean"] * escala, color=[AZUL if m > tr.target.mean() else GRIS for m in rub["mean"]])
    ax.axvline(tr.target.mean() * escala, color=NARANJA, linestyle="--", linewidth=1.2)
    for i, (m, n) in enumerate(zip(rub["mean"], rub["size"])):
        ax.text(m * escala, i, f" {m:,.0f} ({n:,})" if REGRESION else f" {m:.0%} ({n:,})", va="center", fontsize=8)
    ax.set_xlabel("promedio del target" if REGRESION else "% que convierte (entre paréntesis: n° de empresas)")
    graficos.append(guardar_grafico(fig))
    hallazgo = f"El rubro con mayor resultado es {rub.index[-1]} ({rub['mean'].iloc[-1]:,.2f} vs {tr.target.mean():,.2f})."
else:
    hallazgo = "Sin columna de rubro: no hay hallazgo por rubro."

if len(pri) and "zona" in d:
    z = d.groupby(d.zona.fillna("(vacía)")).agg(priorizadas=("priorizado", "sum"), empresas=("id", "size")).reset_index()
    fig, ax = grafico("5_zonas", f"A quién llamamos: {len(pri):,} empresas por zona",
                      f"Dentro de cada zona se eligen las de mayor '{ORDENAR_POR}'" + (" según los cupos" if C.CUPOS_ZONA else ""))
    ax.bar(z.zona, z.priorizadas, color=AZUL, width=0.55)
    for i, r in enumerate(z.itertuples()):
        ax.text(i, r.priorizadas, f"{r.priorizadas}\nde {r.empresas:,}", ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(0, max(z.priorizadas.max(), 1) * 1.35)
    ax.set_ylabel("empresas priorizadas")
    graficos.append(guardar_grafico(fig))

if hay_examen and k:
    o = d.sort_values(ORDENAR_POR, ascending=False)
    x = np.arange(1, len(o) + 1) / len(o)
    yc = o.target.cumsum().to_numpy() / o.target.sum()
    captura = float(yc[k - 1])
    fig, ax = grafico("5_captura", f"Con {k:,} contactos capturamos {captura / (k / len(d)):.1f} veces más que al azar",
                      f"Curva de captura (examen): el {pct(k / len(d))} de arriba trae el {pct(captura)} del total; "
                      f"al azar traería el {pct(k / len(d))}")
    ax.plot(x * 100, yc * 100, color=AZUL, linewidth=2, label="con el modelo")
    ax.plot([0, 100], [0, 100], color=GRIS, linestyle="--", linewidth=1.2, label="al azar")
    ax.scatter([k / len(d) * 100], [captura * 100], color=NARANJA, s=40, zorder=3)
    ax.annotate(f"capacidad: {k:,}", (k / len(d) * 100, captura * 100), xytext=(12, -4),
                textcoords="offset points", fontsize=8.5, color=NARANJA)
    ax.set_xlabel("% de empresas contactadas (ordenadas por el modelo)")
    ax.set_ylabel("% del total capturado")
    ax.legend(frameon=False, loc="lower right")
    graficos.append(guardar_grafico(fig))

# ------------------------------------------------------------------ 6. entrega
cols = C.ENTREGA["columnas"]
faltan = [c for c in cols if c not in d]
if faltan:
    raise SystemExit(f"  config.ENTREGA pide {faltan}, que no existen. Disponibles: {sorted(d.columns)}")
sub = d[list(cols)].rename(columns=cols)
destino = SAL / C.ENTREGA["archivo"]
sub.to_csv(destino, index=False, encoding="utf-8")
d.sort_values(ORDENAR_POR if k else "valor", ascending=False).to_csv(SAL / "priorizados.csv", index=False,
                                                                      encoding="utf-8-sig")
print(f"\n  Entrega: {destino} ({len(sub):,} filas, columnas {list(sub.columns)})")
controles = [
    ("1 fila por empresa", d.id.is_unique),
    ("todas las empresas a predecir", len(d) == len(te)),
    ("predicción sin vacíos" + ("" if REGRESION else " y entre 0 y 1"),
     d.pred.notna().all() if REGRESION else d.prob.between(0, 1).all()),
    ("valor esperado sin vacíos", d.valor.notna().all()),
    (f"priorizadas = capacidad ({k:,})", int(d.priorizado.sum()) == k),
    ("priorizadas solo elegibles y con zona válida",
     bool(pri.elegible.all()) and (not (C.CUPOS_ZONA and "zona" in d) or pri.zona.isin(list(C.CUPOS_ZONA)).all())),
]
for txt, ok in controles:
    print(f"   [{'OK' if ok else '!!'}] {txt}")
    if not ok:
        alertas.append(f"Control fallido: {txt}")

guardar_resumen("5_priorizar", dict(
    rol="Liz", titulo="Paso 5 · A quién llamar y la entrega", pregunta="¿A quién llamamos primero y la entrega está lista?",
    numeros={"filas entregadas": len(sub), "priorizadas": len(pri), "valor esperado priorizadas": f"{pri.valor.sum():,.0f}",
             **({"resultado priorizadas vs base": f"{pri.target.mean() / base:.1f}x",
                 "capturado con la capacidad": pct(captura)} if hay_examen and len(pri) and captura else {}),
             "controles OK": f"{sum(bool(ok) for _, ok in controles)}/{len(controles)}"},
    explicacion=[hallazgo, f"Valor esperado = {'monto predicho' if REGRESION else 'probabilidad × monto si convierte'}.",
                 f"Elegibles: {C.ELEGIBLES}. Se ordena por '{ORDENAR_POR}'" +
                 (" dentro de cada zona hasta llenar su cupo." if C.CUPOS_ZONA else ".")],
    alertas=alertas, graficos=graficos))
