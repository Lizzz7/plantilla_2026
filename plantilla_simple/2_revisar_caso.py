"""
PASO 2 · NAT — el caso en números y la configuración revisada.

Pregunta: ¿qué problema resolvemos y config.py está bien?

  python 2_revisar_caso.py        (después del paso 1)

Qué hace, en orden:
  1. Revisa que cada tabla y columna que nombra config.py EXISTA. Si algo falta, dice qué hay en su
     lugar y se detiene ANTES de que los pasos 3-5 se caigan a mitad de camino.
  2. Revisa la llave de EMPRESAS: 1 fila por empresa, sin repetidos.
  3. El target:
       forma A (evento)  -> eventos por mes y la línea de tiempo con los dos cortes
       forma B (columna) -> cuántas filas tienen target (entrenan) y cuántas hay que predecir
  4. Tasa base (o promedio, en regresión) y con lead vs sin lead.
  5. Capacidad: a cuántas empresas se puede llamar y cuántas por zona.

QUÉ EDITAR SEGÚN EL RETO: este paso casi nunca se edita; lo que se corrige es config.py.
  Si quieren otra revisión (ej. "¿hay empresas de test que no están en EMPRESAS?"), agréguenla
  como un bloque más al final, con el mismo estilo: calcular -> imprimir -> alerta() si algo está mal.

Salidas: salidas/graficos/2_*.png · resumen para el reporte
"""
import pandas as pd

from comun import AZUL, C, GRIS, MODO, NARANJA, REGRESION, alerta, conectar, es_binario, evento, grafico, \
    guardar_grafico, guardar_resumen, hay_target, pct, sql_etiquetas, sql_target, tablas_disponibles, titulo, LIMPIO

titulo(f"PASO 2 · NAT — el caso en números ({C.TIPO_PROBLEMA}, target tipo '{MODO}')")
con = conectar()
alertas, graficos, numeros = [], [], {}
DISP = tablas_disponibles()


def ruta(tabla):
    return (LIMPIO / f"{tabla}.parquet").as_posix()


def columnas_de(tabla):
    return {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{ruta(tabla)}'").fetchall()}


# ------------------------------------------------------------------ 1. config apunta a cosas que existen
print("\n  1) ¿Existen las tablas y columnas de config.py?")
revisar = [("EMPRESAS", C.EMPRESAS["tabla"], [C.EMPRESAS["id"], C.ZONA, C.RUBRO, C.LEAD])]
revisar += [("ATRIBUTOS", a["tabla"], [a["id"]]) for a in C.ATRIBUTOS]
revisar += [("EVENTOS", e["tabla"], [e["id"], e["fecha"], e.get("monto"), e.get("moneda"),
                                     *(e.get("extra") or {}).values()]) for e in C.EVENTOS]
if MODO == "columna":
    revisar.append(("TARGET", C.TARGET["tabla"], [C.TARGET["id"], C.TARGET["columna"]]))
if C.PREDECIR:
    revisar.append(("PREDECIR", C.PREDECIR["tabla"], [C.PREDECIR["id"]]))
todo_ok = True
for donde, tabla, cols in revisar:
    if tabla not in DISP:
        todo_ok = False
        alerta(f"{donde}: la tabla '{tabla}' no existe. Tablas limpias: {DISP}", alertas)
        continue
    existentes = columnas_de(tabla)
    faltan = [c for c in cols if c and c not in existentes]
    if faltan:
        todo_ok = False
        alerta(f"{donde} {tabla}: no existen {faltan}. Columnas reales: {sorted(existentes)}", alertas)
    else:
        print(f"   [OK] {donde}: {tabla}")
if MODO == "evento" and todo_ok:
    try:
        con.execute(sql_target(C.FECHA_CORTE)).fetchall()
        print("   [OK] el filtro del TARGET funciona")
    except Exception as e:  # noqa: BLE001
        todo_ok = False
        alerta(f"El filtro del TARGET falla: {e}", alertas)
elif MODO not in ("evento", "columna"):
    todo_ok = False
    alerta(f"TARGET tipo '{MODO}' no existe: use 'evento' o 'columna'", alertas)
if not todo_ok:
    raise SystemExit("\n  Corrijan config.py y vuelvan a correr este paso.\n")
todas = set().union(*[columnas_de(t) for _, t, _ in revisar])
for c in C.COLUMNAS_FUERA:
    if c not in todas:
        alerta(f"COLUMNAS_FUERA: '{c}' no existe en ninguna tabla (¿nombre mal escrito?)", alertas)

# ------------------------------------------------------------------ 2. llave de empresas
emp, eid = ruta(C.EMPRESAS["tabla"]), C.EMPRESAS["id"]
n, nd = con.execute(f'SELECT count(*), count(DISTINCT "{eid}") FROM \'{emp}\'').fetchall()[0]
print(f"\n  2) Empresas: {n:,} filas, {nd:,} ids distintos")
numeros["empresas"] = nd
if n != nd:
    alerta(f"{n - nd:,} empresas repetidas en {C.EMPRESAS['tabla']}: el paso 3 se quedará con una fila por id", alertas)
if C.PREDECIR:
    fuera = con.execute(f"""SELECT count(DISTINCT "{C.PREDECIR['id']}") FROM '{ruta(C.PREDECIR['tabla'])}'
                            WHERE "{C.PREDECIR['id']}" NOT IN (SELECT "{eid}" FROM '{emp}')""").fetchall()[0][0]
    if fuera:
        alerta(f"{fuera:,} empresas de PREDECIR no están en EMPRESAS: no tendrán variables. "
               "Unan esas tablas (config.UNIR) o elijan otra tabla EMPRESAS", alertas)

# ------------------------------------------------------------------ 3. el target
print("\n  3) El target")
if MODO == "evento":
    esperado = (pd.Timestamp(C.FECHA_CORTE) - pd.DateOffset(months=C.HORIZONTE_MESES)).strftime("%Y-%m-%d")
    if C.CORTE_ANTERIOR != esperado:
        alerta(f"CORTE_ANTERIOR = {C.CORTE_ANTERIOR}, pero corte − horizonte = {esperado}. ¿Es a propósito?", alertas)
    inicio = pd.Timestamp(C.CORTE_ANTERIOR) - pd.DateOffset(months=C.HISTORIA_MESES)
    for e in C.EVENTOS:
        minf = con.execute(f'SELECT min("{e["fecha"]}") FROM \'{ruta(e["tabla"])}\'').fetchall()[0][0]
        if minf is not None and pd.Timestamp(minf) > inicio + pd.DateOffset(days=31):
            alerta(f"{e['tabla']} empieza en {minf}, pero HISTORIA_MESES = {C.HISTORIA_MESES} pide datos desde "
                   f"{inicio:%Y-%m-%d}. Si se quedan así, sus variables no son comparables entre cortes", alertas)
    e = evento(C.TARGET["tabla"])
    filtro = f"WHERE {C.TARGET['filtro']}" if C.TARGET.get("filtro") else ""
    meses = con.sql(f"""SELECT date_trunc('month', "{e['fecha']}") mes, count(*) n
                        FROM '{ruta(e['tabla'])}' {filtro} GROUP BY 1 ORDER BY 1""").df().dropna()
    print(f"   eventos del target: de {meses.mes.min():%Y-%m} a {meses.mes.max():%Y-%m}")
    corte, ca = pd.Timestamp(C.FECHA_CORTE), pd.Timestamp(C.CORTE_ANTERIOR)
    fin = lambda d: d + pd.DateOffset(months=C.HORIZONTE_MESES)  # noqa: E731
    fig, ax = grafico("2_linea_tiempo", "Cómo se valida: entrenar con el pasado, examinar con un periodo que no vio",
                      f"Eventos del target por mes ({C.TARGET['tabla']}, con el filtro del config)", ancho=9, alto=4.4)
    ax.bar(meses.mes, meses.n, width=20, color=GRIS)
    top = meses.n.max() * 1.25
    ax.axvspan(ca, fin(ca), color=NARANJA, alpha=0.15)
    ax.axvspan(corte, fin(corte), color=AZUL, alpha=0.15)
    for x, txt, col in ((ca, "corte anterior", NARANJA), (corte, "corte actual", AZUL)):
        ax.axvline(x, color=col, linewidth=1.5)
        ax.text(x, top * 0.97, f" {txt}\n {x:%Y-%m-%d}", color=col, fontsize=8.5, va="top")
    ax.text(ca + (fin(ca) - ca) / 2, top * 0.72, "target para\nENTRENAR", ha="center", fontsize=8.5)
    ax.text(corte + (fin(corte) - corte) / 2, top * 0.72, "target a\nPREDECIR", ha="center", fontsize=8.5)
    ax.set_ylim(0, top)
    ax.set_ylabel("eventos por mes")
    graficos.append(guardar_grafico(fig))
    # etiquetas por empresa para el corte anterior (y el actual si ya ocurrió)
    etiquetas = {}
    for nombre, c in (("corte anterior", C.CORTE_ANTERIOR), ("corte actual", C.FECHA_CORTE)):
        if not hay_target(con, c):
            print(f"   {nombre} ({c}): sin datos después del corte -> su target es el FUTURO (normal en el evento)")
            continue
        t = con.sql(f"""SELECT e.id, coalesce(t.target, 0) target, coalesce(t.target_monto, 0) monto
                        FROM (SELECT DISTINCT "{eid}" id FROM '{emp}') e LEFT JOIN ({sql_target(c)}) t USING (id)""").df()
        if REGRESION:
            t["target"] = t.monto
        etiquetas[nombre] = t
else:
    lab = con.sql(sql_etiquetas()).df()
    a_predecir = (con.execute(f"SELECT count(DISTINCT \"{C.PREDECIR['id']}\") FROM '{ruta(C.PREDECIR['tabla'])}'")
                  .fetchall()[0][0] if C.PREDECIR else nd - lab.id.nunique())
    print(f"   con target (entrenan): {lab.id.nunique():,} · a predecir: {a_predecir:,}")
    if a_predecir <= 0:
        alerta("No hay filas sin target ni PREDECIR: se predecirá sobre las mismas filas de entrenamiento", alertas)
    if lab.target.isna().any():
        alerta(f"{int(lab.target.isna().sum())} valores del target no son 0/1 ni números: revisar la columna", alertas)
    if not REGRESION and not es_binario(lab.target):
        alerta(f"TIPO_PROBLEMA = clasificacion pero el target tiene {lab.target.nunique()} valores distintos. "
               "¿Es regresión? ¿Hay que convertirlo a 0/1?", alertas)
    etiquetas = {"entrenamiento": lab}
    numeros["a predecir"] = a_predecir

# ------------------------------------------------------------------ 4. tasa base / promedio y lead
print("\n  4) " + ("Promedio del target" if REGRESION else "Tasa base"))
for nombre, t in etiquetas.items():
    v = t.target.mean()
    txt = f"{v:,.2f} (promedio) · {pct((t.target > 0).mean())} con valor > 0" if REGRESION else pct(v)
    print(f"   {nombre}: {len(t):,} empresas -> {txt}")
    numeros[f"{'promedio' if REGRESION else 'tasa base'} {nombre}"] = f"{v:,.0f}" if REGRESION else pct(v)
    if not REGRESION and v < 0.01:
        alerta("Menos de 1% convierte: problema muy desbalanceado (reportar también AUC-PR)", alertas)

if C.LEAD and etiquetas:
    nombre, t = next(iter(etiquetas.items()))
    lead = con.sql(f'SELECT DISTINCT "{eid}" id, "{C.LEAD}" lead FROM \'{emp}\'').df()
    ab = t.merge(lead, on="id").assign(lead=lambda x: pd.to_numeric(x.lead, errors="coerce").fillna(0).astype(int))
    ab = ab.groupby("lead").agg(empresas=("id", "size"), tasa=("target", "mean")).reset_index()
    print(f"\n   Con lead vs sin lead ({nombre}):")
    for r in ab.itertuples():
        print(f"   lead={r.lead}: {r.empresas:,} empresas -> " + (f"{r.tasa:,.0f}" if REGRESION else pct(r.tasa)))
    fig, ax = grafico("2_lead", "¿Dónde está la oportunidad? Con lead vs sin lead",
                      "Forma A = convertir más a los que tienen lead · Forma B = elegir a quién habilitar")
    etiq = ["sin lead (forma B)" if r.lead == 0 else "con lead (forma A)" for r in ab.itertuples()]
    escala = 1 if REGRESION else 100
    ax.bar(etiq, ab.tasa * escala, color=[GRIS, AZUL][: len(ab)], width=0.5)
    for i, r in enumerate(ab.itertuples()):
        ax.text(i, r.tasa * escala, (f"{r.tasa:,.0f}" if REGRESION else pct(r.tasa)) + f"\n{r.empresas:,} empresas",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("promedio del target" if REGRESION else "% que convierte")
    ax.set_ylim(0, ab.tasa.max() * escala * 1.4)
    graficos.append(guardar_grafico(fig))

# ------------------------------------------------------------------ 5. capacidad
if C.CAPACIDAD:
    k = int(C.CAPACIDAD * nd) if C.CAPACIDAD < 1 else int(C.CAPACIDAD)
    print(f"\n  5) Capacidad: {C.CAPACIDAD} -> {k:,} empresas (de {nd:,} en EMPRESAS)")
    numeros["capacidad (empresas)"] = k
    if C.CUPOS_ZONA and C.ZONA:
        zonas = con.sql(f'SELECT "{C.ZONA}" zona, count(DISTINCT "{eid}") n FROM \'{emp}\' GROUP BY 1').df()
        fuera = int(zonas[~zonas.zona.isin(list(C.CUPOS_ZONA))].n.sum())
        if fuera:
            alerta(f"{fuera:,} empresas con zona vacía o fuera de CUPOS_ZONA: no pueden ocupar cupo. "
                   f"Zonas reales: {sorted(zonas.zona.dropna().unique())[:15]}", alertas)
        tot = sum(C.CUPOS_ZONA.values())
        for z, v in C.CUPOS_ZONA.items():
            print(f"   {z}: {round(k * v / tot):,} empresas")
    elif C.CUPOS_ZONA and not C.ZONA:
        alerta("Hay CUPOS_ZONA pero ZONA = None: se priorizará sin cupos", alertas)
else:
    print("\n  5) Sin CAPACIDAD: no se arma lista de priorizados (solo probabilidades)")

guardar_resumen("2_revisar_caso", dict(
    rol="Nat", titulo="Paso 2 · El caso en números", pregunta="¿Qué problema resolvemos y config.py está bien?",
    numeros={"tipo de problema": C.TIPO_PROBLEMA, "target": MODO, **numeros},
    explicacion=([f"Decidimos el {C.FECHA_CORTE} con datos anteriores; el target mira los {C.HORIZONTE_MESES} "
                  "meses siguientes. Para medir honestamente entrenamos con el corte anterior."] if MODO == "evento"
                 else ["El target ya viene en una columna: se entrena con las filas que lo tienen y se predicen "
                       "las demás. La validación es por pliegues (no hay corte anterior)."]),
    alertas=alertas, graficos=graficos))
print("\n  Listo. Si no hubo [!!], Kath puede correr el paso 3." if not alertas else
      "\n  Revisen los [!!] (pueden ser decisiones, no errores) y sigan con el paso 3.")
