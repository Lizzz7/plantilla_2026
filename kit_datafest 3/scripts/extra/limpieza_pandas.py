# EXTRA · HELLEN: plan B si 1_leer_limpiar.py (DuckDB) falla o limpia mal.
# Hace lo MISMO en pandas puro, columna por columna, y además DIAGNOSTICA cada columna:
# qué % es número, qué % es fecha y ejemplos de los valores que NO se pudieron convertir.
#   python extra/limpieza_pandas.py               -> escribe en salidas/limpio_pandas/ (no pisa nada)
#   python extra/limpieza_pandas.py reemplazar    -> escribe en salidas/limpio/ (lo que lee 3_variables.py)
#   python extra/limpieza_pandas.py solo_diagnostico
# Si una columna sale mal, NO toques todo: agrega la columna a FORZAR_TIPO abajo y vuelve a correr.
import csv
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ajustes as A

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / A.CARPETA_DATOS
DESTINO = BASE / A.CARPETA_SALIDAS / ("limpio" if "reemplazar" in sys.argv else "limpio_pandas")
SOLO_DIAG = "solo_diagnostico" in sys.argv

NULOS = {"", "S/D", "N/A", "#N/A", "NA", "NULL", "NONE", "NAN", "-", "SIN DATO", "?"}
CENTINELAS = {999999, -999, 9999999}             # códigos de "sin dato" que se disfrazan de número (revisen el suyo)
FORZAR_TIPO = {                                   # override manual: "tabla.columna": "id|num|fecha|texto"
    # "maestro_clientes.ventas_anuales": "num",
}
UMBRAL = 0.95                                     # % de valores que deben convertirse para aceptar el tipo


def nombre_limpio(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")


# ---------------- 1) LEER: probar varias formas hasta que una funcione ----------------
def leer(archivo):
    suf = archivo.suffix.lower()
    if suf in (".xlsx", ".xls"):
        hojas = pd.read_excel(archivo, sheet_name=None, dtype=str)
        if len(hojas) > 1:
            print(f"   {archivo.name}: {len(hojas)} hojas -> se apilan ({list(hojas)})")
        return pd.concat(hojas.values(), ignore_index=True)
    if suf == ".parquet":
        return pd.read_parquet(archivo).astype(str).replace({"None": None, "nan": None})
    if suf == ".json":
        return pd.read_json(archivo, dtype=False).astype(str)
    if suf in (".csv", ".txt", ".tsv"):
        for enc in ("utf-8-sig", "latin-1", "cp1252"):              # tildes rotas = encoding equivocado
            try:
                with open(archivo, encoding=enc) as f:
                    muestra = f.read(20000)
                sep = csv.Sniffer().sniff(muestra, delimiters=",;|\t").delimiter   # adivina el separador
                return pd.read_csv(archivo, sep=sep, dtype=str, encoding=enc, keep_default_na=False,
                                   on_bad_lines="warn")                              # filas rotas: avisa y sigue
            except (UnicodeDecodeError, csv.Error):
                continue
        return pd.read_csv(archivo, sep=None, engine="python", dtype=str, encoding="latin-1")
    return None


# ---------------- 2) FUNCIONES DE LIMPIEZA (una por tipo) ----------------
def a_texto(s):
    t = s.astype(object).where(s.notna(), "").astype(str).str.strip().str.upper()
    t = t.map(lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode())
    return t.where(~t.isin(NULOS), None)


def a_id(s):                                       # '20123456789.0' -> '20123456789' ; ' 2012 ' -> '2012'
    t = a_texto(s)
    return t.str.replace(r"\.0+$", "", regex=True).str.replace(r"\s", "", regex=True)


def a_numero(s):                                   # 'S/ 1,234.50' 'USD 1.234,5' '15%' '(200)' -> float
    t = a_texto(s)
    t = t.str.replace(r"(S/\.?|USD|US\$|\$|%|\s)", "", regex=True)
    t = t.str.replace(r"^\((.*)\)$", r"-\1", regex=True)                 # (200) contable = -200
    europeo = t.str.match(r"^-?\d{1,3}(\.\d{3})+,\d+$|^-?\d+,\d{1,2}$", na=False)
    t = t.where(~europeo, t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    t = t.where(europeo, t.str.replace(",", "", regex=False))
    x = pd.to_numeric(t, errors="coerce")
    return x.where(~x.isin(CENTINELAS))


def a_fecha(s):                                    # prueba formato por formato; gana el primero que funcione
    t = a_texto(s)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[s]")      # [s]: aguanta años raros como 9999
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m"):
        falta = out.isna() & t.notna()
        if not falta.any():
            break
        out[falta] = pd.to_datetime(t[falta], format=fmt, errors="coerce").astype("datetime64[s]")
    serial = out.isna() & t.str.fullmatch(r"\d{5}(\.0+)?", na=False)      # serial de Excel: 45123
    out[serial] = (pd.Timestamp("1899-12-30") + pd.to_timedelta(t[serial].astype(float), unit="D")).astype("datetime64[s]")
    out = out.where((out >= "1990-01-01") & (out <= "2030-12-31"))       # 1900-01-01, 2099... = basura
    return out.dt.date


# ---------------- 3) DIAGNÓSTICO: medir antes de decidir ----------------
def diagnostico(df, tabla):
    filas = []
    for c in df.columns:
        t = a_texto(df[c])
        llenos = t.notna()
        n = a_numero(df[c])[llenos]
        f = pd.Series(a_fecha(df[c]))[llenos]
        no_num = t[llenos & a_numero(df[c]).isna()].drop_duplicates().head(3).tolist()
        filas.append({"tabla": tabla, "columna": c, "%nulos": round(100 * (1 - llenos.mean()), 1),
                      "%numero": round(100 * n.notna().mean(), 1) if llenos.any() else 0,
                      "%fecha": round(100 * f.notna().mean(), 1) if llenos.any() else 0,
                      "distintos": t.nunique(), "ejemplos_no_numero": " | ".join(no_num)[:40]})
    return pd.DataFrame(filas)


def decidir_tipo(tabla, c, fila):
    if f"{tabla}.{c}" in FORZAR_TIPO:
        return FORZAR_TIPO[f"{tabla}.{c}"]
    if c.startswith(("ruc", "id_", "cod_", "nro_", "dni")) or c == A.ID:
        return "id"                                 # los IDs NUNCA son números (perderías ceros y decimales)
    if ("fec" in c or "periodo" in c or "fecha" in c) and fila["%fecha"] >= 100 * UMBRAL:
        return "fecha"
    if fila["%numero"] >= 100 * UMBRAL:
        return "num"
    return "texto"


LIMPIAR = {"id": a_id, "num": a_numero, "fecha": a_fecha, "texto": a_texto}

if __name__ == "__main__":
    DESTINO.mkdir(parents=True, exist_ok=True)
    diags = []
    for archivo in sorted(DATOS.iterdir()):
        df = leer(archivo)
        if df is None:
            print(f"   {archivo.name}: formato no reconocido, se salta")
            continue
        tabla = nombre_limpio(archivo.stem)
        df.columns = [nombre_limpio(c) or f"col_{i}" for i, c in enumerate(df.columns)]
        df = df.loc[:, ~df.columns.duplicated()]                 # columnas repetidas: queda la primera
        diag = diagnostico(df.head(20000), tabla)
        diag["tipo"] = [decidir_tipo(tabla, f["columna"], f) for f in diag.to_dict("records")]
        diags.append(diag)
        if SOLO_DIAG:
            continue
        limpio = pd.DataFrame({c: LIMPIAR[t](df[c]) for c, t in zip(diag.columna, diag.tipo)})
        antes = len(limpio)
        limpio = limpio.drop_duplicates()
        for c, t in zip(diag.columna, diag.tipo):               # parquet con tipos correctos
            if t == "fecha":
                limpio[c] = pd.to_datetime(limpio[c])
            elif t in ("id", "texto"):
                limpio[c] = limpio[c].astype(object)
        limpio.to_parquet(DESTINO / f"{tabla}.parquet", index=False)
        print(f"{tabla}: {antes:,} filas -> {len(limpio):,}   "
              + ", ".join(f"{c}[{t}]" for c, t in zip(diag.columna, diag.tipo)))

    d = pd.concat(diags, ignore_index=True)
    pd.set_option("display.width", 200, "display.max_colwidth", 40, "display.max_rows", 300)
    print("\n== DIAGNÓSTICO (revisen las que dicen texto pero tienen %numero alto, o al revés) ==")
    print(d.to_string(index=False))
    sospechosas = d[(d.tipo == "texto") & (d["%numero"].between(50, 100 * UMBRAL))]
    if len(sospechosas):
        print("\n[!] Casi-números que quedaron como texto (miren 'ejemplos_no_numero' y agreguen a FORZAR_TIPO):")
        print(sospechosas[["tabla", "columna", "%numero", "ejemplos_no_numero"]].to_string(index=False))
    d.to_csv(BASE / A.CARPETA_SALIDAS / "diagnostico_columnas.csv", index=False)
    print(f"\nDiagnóstico guardado en {A.CARPETA_SALIDAS}/diagnostico_columnas.csv"
          + ("" if SOLO_DIAG else f";  tablas en {DESTINO.relative_to(BASE)}/"))
