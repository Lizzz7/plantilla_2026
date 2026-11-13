# PASO 1 · HELLEN: leer los archivos y dejarlos limpios en salidas/limpio/
# Idea: leer TODO como texto (nada se rompe al leer) y después decidir el tipo midiendo.
import re
import unicodedata
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import ajustes as A

DATOS, LIMPIO = Path(A.CARPETA_DATOS), Path(A.CARPETA_SALIDAS) / "limpio"
LIMPIO.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()

# Funciones de limpieza en SQL (una por tipo de dato)
con.execute(r"""
CREATE MACRO txt(x) AS CASE WHEN upper(strip_accents(trim(x))) IN ('', 'S/D', 'N/A', '#N/A', 'NULL', '-', 'SIN DATO')
                            THEN NULL ELSE upper(strip_accents(trim(x))) END;
CREATE MACRO idn(x) AS regexp_replace(txt(x), '\.0+$', '');                 -- '20123456789.0' -> '20123456789'
CREATE MACRO limpio(x) AS regexp_replace(upper(trim(x)), '(S/\.?|USD|\$|%|\s)', '', 'g');
CREATE MACRO europeo(s) AS regexp_matches(s, '^-?\d{1,3}(\.\d{3})+,\d+$') OR regexp_matches(s, '^-?\d+,\d{1,2}$');
CREATE MACRO num(x) AS CASE                                                   -- 'S/ 1,234.50' -> 1234.5
    WHEN europeo(limpio(x)) THEN TRY_CAST(replace(replace(limpio(x), '.', ''), ',', '.') AS DOUBLE)
    ELSE TRY_CAST(replace(limpio(x), ',', '') AS DOUBLE) END;
CREATE MACRO numero(x) AS CASE WHEN num(x) IN (999999, -999) THEN NULL ELSE num(x) END;  -- centinelas = sin dato
CREATE MACRO fecha(x) AS COALESCE(
    TRY_CAST(try_strptime(trim(x), ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']) AS DATE),
    TRY_CAST(try_strptime(substr(trim(x), 1, 10), '%Y-%m-%d') AS DATE),
    CASE WHEN regexp_matches(trim(x), '^\d{8}$') THEN TRY_CAST(try_strptime(trim(x), '%Y%m%d') AS DATE) END,
    CASE WHEN regexp_matches(trim(x), '^\d{5}(\.0+)?$')                                  -- serial de Excel
         THEN CAST(DATE '1899-12-30' + CAST(CAST(trim(x) AS DOUBLE) AS INTEGER) AS DATE) END);
""")


def nombre_limpio(texto):                       # 'Fecha Operación ' -> 'fecha_operacion'
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")


resumen = []
for archivo in sorted(DATOS.iterdir()):
    tabla = nombre_limpio(archivo.stem)
    # 1) leer como texto
    if archivo.suffix == ".csv":
        df = con.sql(f"SELECT * FROM read_csv('{archivo.as_posix()}', all_varchar=true)").df()
    elif archivo.suffix == ".xlsx":
        hojas = pd.read_excel(archivo, sheet_name=None, dtype=str)       # todas las hojas
        df = pd.concat(hojas.values(), ignore_index=True)
    else:
        continue
    df.columns = [nombre_limpio(c) for c in df.columns]
    df = df.astype(object).where(df.notna(), None)
    con.register("crudo", df)

    # 2) decidir el tipo de cada columna midiendo una muestra
    partes = []
    for c in df.columns:
        q = f'"{c}"'
        llenos, p_num, p_fec = con.execute(f"""SELECT count(txt({q})),
            avg(CASE WHEN num({q}) IS NOT NULL THEN 1 ELSE 0 END) FILTER (WHERE txt({q}) IS NOT NULL),
            avg(CASE WHEN fecha({q}) IS NOT NULL THEN 1 ELSE 0 END) FILTER (WHERE txt({q}) IS NOT NULL)
            FROM (SELECT * FROM crudo LIMIT 20000)""").fetchall()[0]
        if c.startswith(("ruc", "id_", "cod_")) or c == A.ID:
            partes.append(f"idn({q}) AS {q}")
        elif ("fec" in c or "periodo" in c) and (p_fec or 0) >= 0.95:
            partes.append(f"fecha({q}) AS {q}")
        elif (p_num or 0) >= 0.95:
            partes.append(f"numero({q}) AS {q}")
        else:
            partes.append(f"txt({q}) AS {q}")

    # 3) limpiar, quitar duplicados exactos y guardar
    con.execute(f"CREATE OR REPLACE TABLE t AS SELECT DISTINCT {', '.join(partes)} FROM crudo")
    con.execute(f"COPY t TO '{(LIMPIO / f'{tabla}.parquet').as_posix()}' (FORMAT parquet)")
    n_limpio = con.execute("SELECT count(*) FROM t").fetchall()[0][0]
    resumen.append((tabla, len(df), n_limpio))
    tipos = con.execute("DESCRIBE t").fetchall()
    print(f"\n{tabla}: {len(df):,} filas -> {n_limpio:,} (sin duplicados)")
    print("   " + ", ".join(f"{c}[{t.lower()[:4]}]" for c, t, *_ in tipos))
    con.unregister("crudo")

# 4) gráfico: filas antes y después
r = pd.DataFrame(resumen, columns=["tabla", "crudo", "limpio"])
ax = r.set_index("tabla")[["crudo", "limpio"]].plot.barh(color=["#9a9993", "#2a78d6"], figsize=(8, 4))
ax.set_title("Filas por tabla antes y después de limpiar (la diferencia = duplicados)", loc="left")
plt.tight_layout()
plt.savefig(Path(A.CARPETA_SALIDAS) / "1_filas.png", dpi=120)
print("\nListo: tablas en salidas/limpio/ y gráfico salidas/1_filas.png")
