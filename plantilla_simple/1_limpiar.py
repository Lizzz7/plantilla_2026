"""
PASO 1 · HELLEN — de los archivos crudos a tablas limpias.

Pregunta: ¿entró todo y quedó bien convertido?

  python 1_limpiar.py

Qué hace, en orden:
  1. Lee cada archivo de datos/ (.csv, .txt, .xlsx con varias hojas) TODO COMO TEXTO.
     Por qué: si la herramienta adivina tipos, un RUC pierde ceros y un 'S/D' rompe la carga.
  2. Normaliza nombres ('Fecha Operación' -> 'fecha_operacion') y une las tablas de config.UNIR.
  3. Decide el tipo de cada columna MIDIENDO (función decidir_tipo, editable).
  4. Limpia con las funciones de comun.py (txt, idn, num, fecha) y quita filas 100% duplicadas.
  5. Concilia montos: suma antes vs después, y explica la diferencia (centinelas + duplicados).
  6. Guarda salidas/limpio/<tabla>.parquet + 3 gráficos + resumen.

QUÉ EDITAR SEGÚN EL RETO (casi todo se arregla en config.py, sin tocar este archivo):
  - Un Excel con título arriba, otra hoja, CSV con ';'      -> config.OPCIONES_LECTURA
  - train.csv + test.csv (o un archivo por mes)             -> config.UNIR
  - Una columna quedó con el tipo equivocado                -> config.FORZAR_TIPO
  - Fechas mes/día (EE. UU.)                                -> config.FORMATOS_FECHA
  - Otro código de "sin dato" (ej. -1, 'NO REGISTRA')       -> config.CENTINELAS_*
  - Otra regla para reconocer fechas/llaves por su nombre   -> bloque EDITABLE de abajo
  - Las filas duplicadas son legítimas (no hay id por fila) -> QUITAR_DUPLICADOS = False (abajo)

Salidas: salidas/limpio/*.parquet · salidas/columnas.csv · salidas/graficos/1_*.png
"""
import pandas as pd

from comun import AZUL, C, DATOS, GRIS, LIMPIO, NARANJA, ROJO, SAL, alerta, conectar, grafico, guardar_grafico, \
    guardar_resumen, normalizar, titulo

# >>> EDITABLE ---------------------------------------------------------------------------------
PISTAS_FECHA = ("fec", "fecha", "date", "periodo")              # nombre con esto + se lee como fecha -> fecha
PISTAS_LLAVE = ("ruc", "id_", "cod_", "codigo", "dni", "nro_doc")  # nombre que empieza así -> llave (texto)
QUITAR_DUPLICADOS = True                                         # filas 100% idénticas = error de carga
# <<< FIN EDITABLE -----------------------------------------------------------------------------

titulo("PASO 1 · HELLEN — archivos crudos -> tablas limpias")
con = conectar()
alertas = []

# Llaves y montos declarados en config, por tabla (las llaves SIEMPRE se tratan como texto)
LLAVES, MONTOS = {}, {}
for t in [C.EMPRESAS, *C.ATRIBUTOS, *C.EVENTOS, C.TARGET, C.PREDECIR or {}]:
    if t.get("tabla") and t.get("id"):
        LLAVES.setdefault(t["tabla"], set()).add(t["id"])
for e in C.EVENTOS:
    if e.get("monto"):
        MONTOS.setdefault(e["tabla"], []).append(e["monto"])


# ------------------------------------------------------------------ 1-2. leer todo como texto
def leer_crudo(ruta):
    """Devuelve {nombre_tabla: DataFrame (Excel) o fuente SQL (CSV)}. Excel con hojas iguales -> una sola tabla."""
    nombre = normalizar(ruta.stem)
    op = C.OPCIONES_LECTURA.get(ruta.name, {})
    if ruta.suffix.lower() in (".xlsx", ".xls"):
        hojas = pd.read_excel(ruta, sheet_name=op.get("hoja"), dtype=str, skiprows=op.get("saltar_filas", 0))
        if isinstance(hojas, pd.DataFrame):                       # se pidió una sola hoja
            hojas = {op.get("hoja"): hojas}
        grupos = {}
        for hoja, df in hojas.items():
            df.columns = [normalizar(c) for c in df.columns]
            grupos.setdefault(tuple(df.columns), []).append((hoja, df))
        if len(grupos) == 1:                                      # hojas con las mismas columnas: se unen
            return {nombre: pd.concat([d for _, d in next(iter(grupos.values()))], ignore_index=True)}
        return {f"{nombre}__{normalizar(h)}": d for g in grupos.values() for h, d in g}
    # CSV/TXT: DuckDB lo lee directo (sin pasar por pandas: poca RAM). Si falla, prueba latin-1 y al final pandas.
    base = f"'{ruta.as_posix()}', all_varchar=true, header=true, sample_size=-1"
    if op.get("separador"):
        base += f", delim='{op['separador']}'"
    if op.get("saltar_filas"):
        base += f", skip={int(op['saltar_filas'])}"
    for fuente in (f"read_csv({base})", f"read_csv({base}, encoding='latin-1')"):
        try:
            con.sql(f"SELECT * FROM {fuente} LIMIT 1").fetchall()
            return {nombre: fuente}
        except Exception as e:  # noqa: BLE001
            ultimo = e
    try:                                                          # último recurso (lento con archivos grandes)
        return {nombre: pd.read_csv(ruta, dtype=str, sep=op.get("separador"), engine="python", encoding="latin-1",
                                    skiprows=op.get("saltar_filas", 0))}
    except Exception as e:  # noqa: BLE001
        ultimo = e
    raise RuntimeError(f"No se pudo leer {ruta.name}: {ultimo}. Prueben OPCIONES_LECTURA en config.py")


# >>> EDITABLE: la regla que decide el tipo de cada columna ---------------------------------------
def decidir_tipo(tabla, col, p_num, p_fec):
    """p_num / p_fec = % de valores no vacíos que se pueden leer como número / fecha (medido)."""
    forzado = C.FORZAR_TIPO.get(f"{tabla}.{col}")
    if forzado:
        return forzado                                            # decisión humana manda
    if col in LLAVES.get(tabla, ()) or col.startswith(PISTAS_LLAVE) or col == "id":
        return "llave"
    if any(k in col for k in PISTAS_FECHA) and p_fec >= C.UMBRAL_TIPO:
        return "fecha"
    if p_num >= C.UMBRAL_TIPO:
        return "numero"
    return "texto"
# <<< FIN EDITABLE -----------------------------------------------------------------------------


FUNCION = {"llave": "idn", "fecha": "fecha", "numero": "num", "texto": "txt"}

DATOS.mkdir(exist_ok=True)
archivos = sorted(p for p in DATOS.iterdir() if p.suffix.lower() in (".csv", ".txt", ".xlsx", ".xls"))
if not archivos:
    raise SystemExit(f"  No hay archivos en {DATOS}. Copien ahí los datos del caso (o: python datos_practica.py)")

# Primero: cada archivo como VISTA de texto en DuckDB (no copia datos: aguanta archivos grandes)
crudas, origen_de = [], {}
for ruta in archivos:
    for tabla, fuente in leer_crudo(ruta).items():
        if isinstance(fuente, pd.DataFrame):                      # Excel: texto "clásico" (cualquier DuckDB)
            con.register(f"df_{tabla}", fuente.astype(object).where(fuente.notna(), None))
            fuente = f"df_{tabla}"
        nombres = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {fuente}").fetchall()]
        sel = ", ".join(f'"{c}" AS "{normalizar(c)}"' for c in nombres)
        con.execute(f'CREATE OR REPLACE VIEW "crudo__{tabla}" AS SELECT {sel} FROM {fuente}').fetchall()
        crudas.append(tabla)
        origen_de[tabla] = ruta.name

# Después: unir las tablas partidas (config.UNIR), con una columna _origen
for nueva, partes in C.UNIR.items():
    faltan = [x for x in partes if x not in crudas]
    if faltan:
        alerta(f"UNIR['{nueva}']: no existen {faltan}. Tablas leídas: {crudas}", alertas)
        continue
    union = " UNION ALL BY NAME ".join(f"SELECT *, '{x}' AS _origen FROM \"crudo__{x}\"" for x in partes)
    con.execute(f'CREATE OR REPLACE VIEW "crudo__{nueva}" AS {union}').fetchall()
    crudas = [x for x in crudas if x not in partes] + [nueva]
    origen_de[nueva] = " + ".join(origen_de[x] for x in partes)
    print(f"  Unidas {partes} -> {nueva}")

resumen_tablas, columnas, concilia, anulados = [], [], [], []
for tabla in crudas:
    con.execute(f'CREATE OR REPLACE VIEW crudo AS SELECT * FROM "crudo__{tabla}"').fetchall()
    n_crudo = con.execute("SELECT count(*) FROM crudo").fetchall()[0][0]
    df_cols = [r[0] for r in con.execute("DESCRIBE SELECT * FROM crudo").fetchall()]

    # ------------------------------------------------------------------ 3. tipo de cada columna
    expr = []
    con.execute("CREATE OR REPLACE TABLE muestra AS SELECT * FROM crudo USING SAMPLE 20000 ROWS").fetchall()
    n_muestra = con.execute("SELECT count(*) FROM muestra").fetchall()[0][0]
    for col in df_cols:
        q = f'"{col}"'
        llenos, p_num, p_fec = con.execute(
            f"SELECT count(txt({q})), avg(CASE WHEN num({q}) IS NOT NULL OR _num(_limpio({q})) IS NOT NULL "
            f"THEN 1 ELSE 0 END) FILTER (WHERE txt({q}) IS NOT NULL), "
            f"avg(CASE WHEN fecha({q}) IS NOT NULL THEN 1 ELSE 0 END) FILTER (WHERE txt({q}) IS NOT NULL) "
            f"FROM muestra").fetchall()[0]
        tipo = "texto" if col == "_origen" else decidir_tipo(tabla, col, p_num or 0, p_fec or 0)
        if tipo not in FUNCION:
            alerta(f"FORZAR_TIPO '{tabla}.{col}' = '{tipo}' no es válido (texto/numero/fecha/llave)", alertas)
            tipo = "texto"
        expr.append(f"{FUNCION[tipo]}({q}) AS {q}")
        columnas.append(dict(tabla=tabla, columna=col, tipo=tipo, pct_vacio=round(1 - llenos / max(n_muestra, 1), 3)))

    # ------------------------------------------------------------------ 4. limpiar + quitar duplicados
    distinct = "DISTINCT" if QUITAR_DUPLICADOS else ""
    con.execute(f"CREATE OR REPLACE TABLE limpio AS SELECT {distinct} {', '.join(expr)} FROM crudo").fetchall()
    n_limpio = con.execute("SELECT count(*) FROM limpio").fetchall()[0][0]
    con.execute(f"COPY limpio TO '{(LIMPIO / f'{tabla}.parquet').as_posix()}' (FORMAT parquet)").fetchall()

    # valores que tenían algo y quedaron vacíos (formato raro o centinela)
    for c in [x for x in columnas if x["tabla"] == tabla and x["tipo"] in ("numero", "fecha")]:
        f = "num" if c["tipo"] == "numero" else "fecha"
        n_anul = con.execute(f'SELECT count(*) FROM crudo WHERE txt("{c["columna"]}") IS NOT NULL '
                             f'AND {f}("{c["columna"]}") IS NULL').fetchall()[0][0]
        anulados.append(dict(tabla=tabla, columna=c["columna"], anulados=n_anul, pct=n_anul / max(n_crudo, 1)))

    # ------------------------------------------------------------------ 5. conciliación de montos
    for m in MONTOS.get(tabla, []):
        if m not in df_cols:
            alerta(f"config: el monto '{m}' no existe en {tabla}", alertas)
            continue
        antes, n_cent, s_cent = con.execute(
            f'SELECT sum(_num(_limpio("{m}"))), count(*) FILTER (WHERE num("{m}") IS NULL AND _num(_limpio("{m}")) IS NOT NULL), '
            f'sum(_num(_limpio("{m}"))) FILTER (WHERE num("{m}") IS NULL) FROM crudo').fetchall()[0]
        despues = con.execute(f'SELECT sum("{m}") FROM limpio').fetchall()[0][0]
        concilia.append(dict(tabla=tabla, monto=m, antes=antes or 0, centinelas=n_cent, suma_centinelas=s_cent or 0,
                             duplicados=n_crudo - n_limpio,
                             suma_duplicados=(antes or 0) - (s_cent or 0) - (despues or 0), despues=despues or 0))

    resumen_tablas.append(dict(tabla=tabla, archivo=origen_de[tabla], filas_crudo=n_crudo, filas_limpio=n_limpio,
                               duplicados=n_crudo - n_limpio, columnas=len(df_cols)))
    if n_crudo == 0:
        alerta(f"{tabla}: 0 filas. Revisar separador o encoding (OPCIONES_LECTURA)", alertas)
    if len(df_cols) == 1 and any(x in df_cols[0] for x in (";", "|", "\t")):
        alerta(f"{tabla}: una sola columna -> probablemente otro separador (OPCIONES_LECTURA separador=';')", alertas)

rt, cols, cc, an = map(pd.DataFrame, (resumen_tablas, columnas, concilia, anulados))
cols.to_csv(SAL / "columnas.csv", index=False, encoding="utf-8-sig")

print("\n  Tablas:")
print(rt.to_string(index=False))
print("\n  Columnas por tipo (detalle en salidas/columnas.csv):")
for t, g in cols.groupby("tabla"):
    print(f"   {t}: " + ", ".join(f"{r.columna}[{r.tipo[0]}]" for r in g.itertuples()))
print("   ([l]lave [f]echa [n]úmero [t]exto)  -> copien estos nombres a config.py")

print("\n  Conciliación de montos:")
for r in cc.itertuples():
    print(f"   {r.tabla}.{r.monto}: {r.antes:,.0f} -> {r.despues:,.0f}")
    if abs(r.antes - r.despues) > 1e-6 * max(abs(r.antes), 1):
        print(f"      = {r.centinelas:,} centinelas ({r.suma_centinelas:,.0f}) + {r.duplicados:,} filas duplicadas "
              f"({r.suma_duplicados:,.0f}) quitadas")

malos = an[an.pct > 0.05]
for r in malos.itertuples():
    alerta(f"{r.tabla}.{r.columna}: {r.pct:.0%} de valores no se pudieron convertir -> mirar sus valores", alertas)

# ------------------------------------------------------------------ 6. gráficos
fig, ax = grafico("1_filas", "¿Entró todo? Filas por tabla, antes y después de limpiar",
                  "La diferencia son filas 100% duplicadas que se quitaron")
y = range(len(rt))
ax.barh([i + 0.2 for i in y], rt.filas_crudo, height=0.38, color=GRIS, label="crudo")
ax.barh([i - 0.2 for i in y], rt.filas_limpio, height=0.38, color=AZUL, label="limpio")
for i, r in enumerate(rt.itertuples()):
    ax.text(r.filas_crudo, i + 0.2, f"  {r.filas_crudo:,}", va="center", fontsize=8.5, color="#52514e")
    ax.text(r.filas_limpio, i - 0.2, f"  {r.filas_limpio:,}" + (f"  (−{r.duplicados:,} duplicadas)" if r.duplicados else ""),
            va="center", fontsize=8.5, color="#0b0b0b")
ax.set_yticks(list(y), rt.tabla)
ax.set_xlim(0, rt.filas_crudo.max() * 1.45)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
g1 = guardar_grafico(fig)

g2 = None
if len(cc):
    fig, ax = grafico("1_conciliacion", "¿Se perdió plata? Suma de cada monto antes y después",
                      "Toda diferencia debe explicarse: centinelas (999999 = sin dato) y duplicados")
    etiquetas = [f"{r.tabla}\n{r.monto}" for r in cc.itertuples()]
    x = range(len(cc))
    ax.bar([i - 0.2 for i in x], cc.antes / 1e6, width=0.38, color=GRIS, label="antes (texto leído como número)")
    ax.bar([i + 0.2 for i in x], cc.despues / 1e6, width=0.38, color=AZUL, label="después (limpio)")
    for i, r in enumerate(cc.itertuples()):
        if r.centinelas or r.duplicados:
            ax.annotate(f"−{r.centinelas:,} centinelas\n−{r.duplicados:,} duplicadas", (i + 0.2, r.despues / 1e6),
                        textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8, color=NARANJA)
    ax.set_xticks(list(x), etiquetas, fontsize=8.5)
    ax.set_ylabel("millones")
    ax.legend(frameon=False, fontsize=8.5)
    g2 = guardar_grafico(fig)

top = an.sort_values("pct", ascending=False).head(12)
fig, ax = grafico("1_calidad", "¿Qué columnas trajeron valores que no se pudieron convertir?",
                  "% de valores no vacíos que quedaron vacíos (centinelas o formato raro). Más de 5% = revisar")
ax.barh(top.tabla + "." + top.columna, top.pct * 100, color=[ROJO if p > 0.05 else AZUL for p in top.pct])
ax.axvline(5, color=ROJO, linestyle="--", linewidth=1)
ax.text(5, len(top) - 0.5, " 5%", color=ROJO, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("% de valores anulados")
g3 = guardar_grafico(fig)

guardar_resumen("1_limpiar", dict(
    rol="Hellen", titulo="Paso 1 · De archivos crudos a tablas limpias",
    pregunta="¿Entró todo y quedó bien convertido?",
    numeros={"tablas": len(rt), "filas limpias": int(rt.filas_limpio.sum()),
             "duplicados quitados": int(rt.duplicados.sum()), "columnas": len(cols)},
    explicacion=[f"{r.tabla}.{r.monto}: {r.antes:,.0f} → {r.despues:,.0f} "
                 f"({r.centinelas:,} centinelas y {r.duplicados:,} duplicadas quitadas)" for r in cc.itertuples()],
    alertas=alertas, graficos=[g for g in (g1, g2, g3) if g]))
print(f"\n  Listo: {len(rt)} tablas limpias en {LIMPIO}")
