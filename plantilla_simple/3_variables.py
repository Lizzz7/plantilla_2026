"""
PASO 3 · KATH — la tabla del modelo: una fila por empresa, sin datos del futuro.

Pregunta: ¿la tabla final es verdadera y sin futuro?

  python 3_variables.py        (después de los pasos 1 y 2)

Qué hace, en orden:
  1. Base = EMPRESAS (1 fila por id) + ATRIBUTOS (otras tablas de 1 fila por empresa):
       - quita COLUMNAS_FUERA (decisiones humanas: fugas, nombres, textos)
       - fechas -> "días antes del corte"; una fecha POSTERIOR al corte es posible fuga: se vacía y se avisa
       - columnas mensuales (saldo_202401 ... saldo_202512) -> saldo_m1 (mes anterior al corte) ... saldo_m6
       - texto con más de MAX_CATEGORIAS valores distintos o columnas constantes -> fuera
  2. EVENTOS: se resumen por empresa SOLO con fechas < corte (y hasta HISTORIA_MESES atrás), con la lista
     AGREGACIONES (editable). Montos en dólares -> soles con TIPO_CAMBIO.
  3. TARGET y qué filas entrenan / se predicen:
       forma A (evento):  entrena = corte anterior (su target ya ocurrió) · predice = corte actual
       forma B (columna): entrena = filas con target · predice = filas sin target (o PREDECIR)
  4. Controles: 1 fila por empresa (si un JOIN duplica, se detiene) y prueba de fuga.

QUÉ EDITAR SEGÚN EL RETO:
  - Agregar una variable de eventos           -> una línea en AGREGACIONES (abajo). Ej. n° de pagadores distintos.
  - Una variable que necesita otra columna    -> config.EVENTOS[...]["extra"] = dict(cp="ruc_pagador")
  - Una variable nueva de atributos (ratio)   -> función variables_extra() (abajo)
  - Más/menos meses en las columnas mensuales -> MESES_MENSUALES
  - Las categorías tienen más de 50 valores   -> MAX_CATEGORIAS (o agrúpenlas en variables_extra)
  - Una variable es fuga                      -> config.COLUMNAS_FUERA (no la borren aquí)

Salidas: salidas/tabla_entrena.parquet · salidas/tabla_predice.parquet · salidas/diccionario.csv · gráficos 3_*
"""
import datetime as dt
import re

import numpy as np
import pandas as pd

from comun import AZUL, C, GRIS, MODO, NARANJA, REGRESION, ROJO, SAL, alerta, conectar, fuerza, grafico, \
    guardar_grafico, guardar_resumen, hay_target, pct, sql_etiquetas, sql_target, tabla_limpia, titulo

# >>> EDITABLE: variables que se calculan para CADA tabla de EVENTOS ---------------------------------
# (nombre, SQL, significado, columna extra que necesita o None)
# En el SQL: f = fecha del evento · m = monto en soles · d = fecha de corte · extras por su nombre (cp, cat...)
AGREGACIONES = [
    ("n",               "count(*)",                                          "n° de eventos en la historia", None),
    ("monto_total",     "sum(m)",                                            "suma del monto (S/)", None),
    ("monto_prom",      "avg(m)",                                            "monto promedio", None),
    ("monto_max",       "max(m)",                                            "monto máximo", None),
    ("n_3m",            "count(*) FILTER (WHERE f >= d - INTERVAL 3 MONTH)", "n° de eventos en los últimos 3 meses", None),
    ("monto_3m",        "coalesce(sum(m) FILTER (WHERE f >= d - INTERVAL 3 MONTH), 0)", "monto de los últimos 3 meses", None),
    ("monto_12m",       "coalesce(sum(m) FILTER (WHERE f >= d - INTERVAL 12 MONTH), 0)", "monto de los últimos 12 meses", None),
    ("recencia_dias",   "date_diff('day', max(f), d)",                       "días desde el último evento", None),
    ("antiguedad_dias", "date_diff('day', min(f), d)",                       "días desde el primer evento", None),
    ("meses_activos",   "count(DISTINCT date_trunc('month', f))",            "meses con al menos un evento", None),
    ("n_contrapartes",  "count(DISTINCT cp)",                                "n° de contrapartes distintas", "cp"),
    # Ejemplos para copiar:
    # ("pct_usd",        "avg(CASE WHEN moneda_usd THEN 1 ELSE 0 END)",     "% de eventos en dólares", None),
    # ("n_canal_web",    "count(*) FILTER (WHERE cat = 'WEB')",             "eventos por canal web", "cat"),
]
MESES_MENSUALES = 6           # columnas saldo_AAAAMM -> saldo_m1 ... saldo_m6
MAX_CATEGORIAS = 50           # texto con más valores distintos que esto = texto libre (fuera)


def variables_extra(df):
    """Variables nuevas a partir de las ya calculadas (ratios, banderas). Se aplica a ambas tablas."""
    # Ejemplos (descomenten y adapten los nombres):
    # df["ops_sobre_ventas"] = df["ops__monto_total"] / df["ventas_anuales"].replace(0, np.nan)
    # df["es_grande"] = (df["num_trabajadores"] > 100).astype(int)
    return df
# <<< FIN EDITABLE -----------------------------------------------------------------------------------

titulo(f"PASO 3 · KATH — tabla del modelo (target '{MODO}', {C.TIPO_PROBLEMA})")
con = conectar()
alertas, diccionario = [], {}
MES = re.compile(r"^(.*?)_?(20\d{2})(0[1-9]|1[0-2])$")      # saldo_202401 -> ('saldo', '2024', '01')
QUITAR = set(C.COLUMNAS_FUERA) | ({C.TARGET["columna"]} if MODO == "columna" else set()) | {"_origen"}


def una_fila_por_id(tabla, id_col):
    """Tabla de 1 fila por empresa (si hay repetidos, se queda con una)."""
    df = con.sql(f"""SELECT * FROM '{tabla_limpia(tabla)}'
                     QUALIFY row_number() OVER (PARTITION BY "{id_col}") = 1""").df()
    return df.rename(columns={id_col: "id"})


def preparar_atributos(df, corte, origen):
    """Fechas -> días; meses -> m1..m6; fuera columnas decididas, constantes y texto libre."""
    corte_ts, salida, mensuales = pd.Timestamp(corte), {"id": df["id"]}, {}
    for c in df.columns.drop("id"):
        if c in QUITAR:
            continue
        s, m = df[c], MES.match(c)
        if m:                                              # columna mensual: se guarda para m1..m6
            mensuales.setdefault(m.group(1) or "valor", {})[pd.Timestamp(f"{m.group(2)}-{m.group(3)}-01")] = s
            continue
        es_fecha = pd.api.types.is_datetime64_any_dtype(s) or (
            s.dtype == object and s.notna().any() and s.dropna().head(50).map(lambda v: isinstance(v, dt.date)).all())
        if es_fecha:
            s = pd.to_datetime(s)
            despues = s >= corte_ts
            if despues.mean() > 0.01:
                alerta(f"{origen}.{c}: {pct(despues.mean())} de fechas son POSTERIORES al corte {corte} "
                       "-> posible fuga. Si no existía el día de decidir, agréguenla a COLUMNAS_FUERA", alertas)
            salida[f"{c}_dias"] = (corte_ts - s.where(~despues)).dt.days
            diccionario[f"{c}_dias"] = (origen, f"días entre {c} y el corte")
        elif pd.api.types.is_numeric_dtype(s):
            if s.nunique(dropna=True) > 1:
                salida[c] = s
                diccionario[c] = (origen, f"{c} tal cual")
        else:
            nd = s.nunique(dropna=True)
            if 1 < nd <= MAX_CATEGORIAS:
                salida[c] = s.astype("string")
                diccionario[c] = (origen, f"{c} (categoría)")
            elif nd > MAX_CATEGORIAS:
                print(f"   (fuera {origen}.{c}: {nd} valores distintos = texto libre; ver MAX_CATEGORIAS)")
    for base, cols in mensuales.items():                  # m1 = mes anterior al corte, m2 = el anterior...
        meses = sorted(d for d in cols if d < corte_ts)[-MESES_MENSUALES:][::-1]
        for i, d in enumerate(meses, 1):
            salida[f"{base}_m{i}"] = cols[d]
            diccionario[f"{base}_m{i}"] = (origen, f"{base} hace {i} mes(es) antes del corte")
        if len(meses) >= 6:
            salida[f"{base}_tend"] = sum(cols[d] for d in meses[:3]) / 3 - sum(cols[d] for d in meses[3:6]) / 3
            diccionario[f"{base}_tend"] = (origen, f"{base}: promedio últimos 3 meses menos los 3 anteriores")
    return pd.DataFrame(salida)


def resumir_eventos(e, corte):
    """Una fila por empresa con la historia de eventos ANTES del corte."""
    t, a, f = tabla_limpia(e["tabla"]), e["alias"], f'"{e["fecha"]}"'
    m = f'"{e["monto"]}"' if e.get("monto") else "1"
    if e.get("moneda"):
        usd = ", ".join(f"'{x}'" for x in C.MONEDAS_USD)
        m = f"""CASE WHEN "{e['moneda']}" IN ({usd}) THEN {m} * {C.TIPO_CAMBIO} ELSE {m} END"""
    extra = e.get("extra") or {}
    cols_extra = "".join(f', "{col}" AS {alias}' for alias, col in extra.items())
    aggs = [(n, sql, sig) for n, sql, sig, req in AGREGACIONES if req is None or req in extra]
    d = f"DATE '{corte}'"
    sel = ",\n               ".join(f"{sql} AS {a}__{n}" for n, sql, _ in aggs)
    df = con.sql(f"""
        WITH ev AS (SELECT "{e['id']}" AS id, {f} AS f, {m} AS m, {d} AS d {cols_extra} FROM '{t}'
                    WHERE {f} < {d} AND {f} >= {d} - INTERVAL {C.HISTORIA_MESES} MONTH)   -- SOLO antes del corte
        SELECT id,
               {sel}
        FROM ev GROUP BY id, d""").df()
    if f"{a}__monto_3m" in df and f"{a}__monto_12m" in df:
        df[f"{a}__tendencia"] = df[f"{a}__monto_3m"] / (df[f"{a}__monto_12m"] / 4).replace(0, np.nan)
        diccionario[f"{a}__tendencia"] = (e["tabla"], "últimos 3 meses vs promedio trimestral del año (>1 crece)")
    for n, _, sig in aggs:
        diccionario[f"{a}__{n}"] = (e["tabla"], sig)
    return df


def construir(corte):
    """Tabla de 1 fila por empresa con las variables al 'corte' (sin target)."""
    print(f"\n  Variables al corte {corte} ...")
    base = preparar_atributos(una_fila_por_id(C.EMPRESAS["tabla"], C.EMPRESAS["id"]), corte, C.EMPRESAS["tabla"])
    n_emp = len(base)
    for a in C.ATRIBUTOS:
        at = preparar_atributos(una_fila_por_id(a["tabla"], a["id"]), corte, a["tabla"])
        at = at.rename(columns={c: f"{c}_{a['tabla'][:6]}" for c in at.columns if c in base.columns and c != "id"})
        base = base.merge(at, on="id", how="left")
    for e in C.EVENTOS:
        ev = resumir_eventos(e, corte)
        base = base.merge(ev, on="id", how="left")
        a = e["alias"]
        conteos = [c for c in ev.columns if c.startswith(f"{a}__") and
                   not c.endswith(("_dias", "_prom", "_max", "tendencia"))]
        base[conteos] = base[conteos].fillna(0)                       # sin eventos = 0 eventos
        for c in (f"{a}__recencia_dias", f"{a}__antiguedad_dias"):
            if c in base:
                base[c] = base[c].fillna(C.HISTORIA_MESES * 31)       # sin eventos = "más antiguo que la historia"
    base = variables_extra(base)
    base["fecha_corte"] = corte
    assert len(base) == n_emp and base.id.is_unique, "Un JOIN duplicó empresas: revisar ids de ATRIBUTOS/EVENTOS"
    return base


def con_target_evento(base, corte):
    """(forma A) agrega target (0/1 o monto en regresión). Vacío si su ventana aún no ocurrió."""
    tg = con.sql(sql_target(corte)).df()
    base = base.merge(tg, on="id", how="left")
    if hay_target(con, corte):
        base["target_monto"] = base.target_monto.fillna(0)
        base["target"] = base.target_monto if REGRESION else base.target.fillna(0).astype(int)
    else:
        base["target"], base["target_monto"] = np.nan, np.nan       # el futuro: no se conoce
    return base


# ------------------------------------------------------------------ armar entrena / predice
if MODO == "evento":
    entrena = con_target_evento(construir(C.CORTE_ANTERIOR), C.CORTE_ANTERIOR)
    predice = con_target_evento(construir(C.FECHA_CORTE), C.FECHA_CORTE)
    explic = [f"Entrena con el corte {C.CORTE_ANTERIOR} (su target ya ocurrió) y predice el corte {C.FECHA_CORTE}.",
              f"Cada variable usa solo eventos con fecha < corte (hasta {C.HISTORIA_MESES} meses atrás)."]
else:
    todo = construir(C.FECHA_CORTE)
    lab = con.sql(sql_etiquetas()).df().drop_duplicates("id")
    todo = todo.merge(lab, on="id", how="left")
    todo["target_monto"] = todo.target if REGRESION else np.nan
    if C.PREDECIR:
        ids = set(con.sql(f"SELECT DISTINCT \"{C.PREDECIR['id']}\" id FROM '{tabla_limpia(C.PREDECIR['tabla'])}'").df().id)
        predice = todo[todo.id.isin(ids)].copy()
        entrena = todo[todo.target.notna() & ~todo.id.isin(ids)].copy()
    else:
        entrena, predice = todo[todo.target.notna()].copy(), todo[todo.target.isna()].copy()
    if predice.empty:
        alerta("No hay filas para predecir: se predicen las mismas de entrenamiento", alertas)
        predice = entrena.copy()
    predice["target"] = np.nan if not predice.equals(entrena) else predice.target
    explic = ["El target ya viene en una columna: entrenan las filas que lo tienen, se predicen las demás.",
              f"Las variables de eventos usan solo fechas < {C.FECHA_CORTE}."]

comunes = [c for c in entrena.columns if c in predice.columns]
entrena = entrena[comunes].sort_values("id").reset_index(drop=True)    # mismo orden = reproducible
predice = predice[comunes].sort_values("id").reset_index(drop=True)
entrena.to_parquet(SAL / "tabla_entrena.parquet", index=False)
predice.to_parquet(SAL / "tabla_predice.parquet", index=False)
dic = pd.DataFrame([(v, o, s) for v, (o, s) in diccionario.items() if v in comunes],
                   columns=["variable", "origen", "significado"])
dic.to_csv(SAL / "diccionario.csv", index=False, encoding="utf-8-sig")
hay_examen = predice.target.notna().any()
desc = (lambda t: f"promedio {t.mean():,.0f}") if REGRESION else (lambda t: f"tasa {pct(t.mean())}")
print(f"\n  Entrena: {len(entrena):,} filas, {desc(entrena.target)} · "
      f"Predice: {len(predice):,} filas, " + (desc(predice.target) if hay_examen else "sin target (lo que se entrega)"))
print(f"  Variables: {len(comunes) - 4}")

# ------------------------------------------------------------------ prueba de fuga
medida = "Spearman" if REGRESION else "Gini"
print(f"\n  Prueba de fuga: ¿alguna variable SOLA ordena demasiado bien? ({medida})")
num = [c for c in comunes if c not in ("id", "target", "target_monto", "fecha_corte")
       and pd.api.types.is_numeric_dtype(entrena[c])]
g = pd.DataFrame({"variable": num,
                  "entrena": [fuerza(entrena.target, entrena[c]) for c in num],
                  "predice": [fuerza(predice.target, predice[c]) if hay_examen else np.nan for c in num]})
g["max"] = g[["entrena", "predice"]].max(axis=1)
g = g.sort_values("max", ascending=False)
sospechosas = g[(g["max"] > 0.5) | (g.predice - g.entrena > 0.3)]
for r in sospechosas.itertuples():
    alerta(f"{r.variable}: {medida} {r.entrena:.2f} (entrena) / {r.predice:.2f} (predice). "
           "¿Existía el día de decidir? Si no -> COLUMNAS_FUERA", alertas)
if sospechosas.empty:
    print(f"   [OK] ninguna variable sola supera {medida} 0.5 ni salta entre tablas")
print(g.head(8).round(3).to_string(index=False))

top = g.head(15).iloc[::-1]
fig, ax = grafico("3_fugas", "Prueba de fuga: ¿alguna variable predice 'demasiado bien' sola?",
                  f"{medida} de cada variable sola. > 0.5, o un salto entre tablas, = sospecha de dato del futuro",
                  alto=5)
y = np.arange(len(top))
ax.barh(y + 0.2, top.entrena, height=0.38, color=NARANJA, label="tabla que entrena")
if hay_examen:
    ax.barh(y - 0.2, top.predice, height=0.38, color=AZUL, label="tabla que predice")
ax.axvline(0.5, color=ROJO, linestyle="--", linewidth=1)
ax.text(0.505, len(top) - 0.6, "zona de fuga", color=ROJO, fontsize=8.5)
ax.set_yticks(y, top.variable, fontsize=8)
ax.set_xlim(0, max(0.6, top["max"].max() * 1.1))
ax.set_xlabel(f"{medida} de la variable sola")
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
graficos = [guardar_grafico(fig)]

# ------------------------------------------------------------------ una empresa en el tiempo (si hay eventos)
if C.EVENTOS:
    # una empresa "legible": entre 2 y 15 eventos en cada tabla (si existe), para que se vean los puntos
    legible = sum(predice[f"{e['alias']}__n"].between(2, 15).astype(int) for e in C.EVENTOS)
    ej = predice.assign(_l=legible).sort_values(["_l", "id"], ascending=[False, True]).id.iloc[0]
    corte = pd.Timestamp(C.FECHA_CORTE)
    fig, ax = grafico("3_una_empresa", "Así se arma una fila: solo cuenta lo que pasó ANTES del corte",
                      f"Empresa {ej} · azul = se usa · gris = más antiguo que la historia · naranja = futuro (no se usa)",
                      ancho=9, alto=1.6 + 0.7 * len(C.EVENTOS))
    for i, e in enumerate(C.EVENTOS):
        fechas = pd.to_datetime(con.sql(f"""SELECT "{e['fecha']}" f FROM '{tabla_limpia(e['tabla'])}'
                                            WHERE "{e['id']}" = '{ej}' AND "{e['fecha']}" IS NOT NULL""").df().f)
        inicio = corte - pd.DateOffset(months=C.HISTORIA_MESES)
        for sel, col in ((fechas < inicio, GRIS), ((fechas < corte) & (fechas >= inicio), AZUL), (fechas >= corte, NARANJA)):
            ax.scatter(fechas[sel], [i] * int(sel.sum()), color=col, s=28, zorder=3)
        valor = int(predice.loc[predice.id == ej, f"{e['alias']}__n"].iloc[0])     # la variable calculada
        ax.text(corte + pd.DateOffset(months=C.HORIZONTE_MESES + 1), i, f"{e['alias']}__n = {valor}",
                va="center", fontsize=8.5)
    ax.axvline(corte, color="#0b0b0b", linewidth=1.2)
    ax.axvspan(corte - pd.DateOffset(months=C.HISTORIA_MESES), corte, color=AZUL, alpha=0.06)
    ax.axvspan(corte, corte + pd.DateOffset(months=C.HORIZONTE_MESES), color=NARANJA, alpha=0.12)
    ax.text(corte, len(C.EVENTOS) - 0.4, f" corte {C.FECHA_CORTE}", fontsize=8.5)
    ax.set_yticks(range(len(C.EVENTOS)), [e["tabla"] for e in C.EVENTOS], fontsize=8.5)
    ax.set_ylim(-0.6, len(C.EVENTOS) - 0.2)
    ax.set_xlim(right=corte + pd.DateOffset(months=C.HORIZONTE_MESES + 5))
    graficos.append(guardar_grafico(fig))

guardar_resumen("3_variables", dict(
    rol="Kath", titulo="Paso 3 · La tabla del modelo", pregunta="¿La tabla final es verdadera y sin futuro?",
    numeros={"filas que entrenan": len(entrena), "filas a predecir": len(predice), "variables": len(comunes) - 4,
             ("promedio target (entrena)" if REGRESION else "tasa (entrena)"):
                 f"{entrena.target.mean():,.0f}" if REGRESION else pct(entrena.target.mean()),
             "variables sospechosas de fuga": len(sospechosas)},
    explicacion=explic, alertas=alertas, graficos=graficos))
print("\n  Listo: salidas/tabla_entrena.parquet y salidas/tabla_predice.parquet")
