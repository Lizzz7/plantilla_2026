"""PASO 2 · HELLEN (DE1): auditoría de salidas/limpio/*.parquet.

Ejecución desde cualquier carpeta:
    python "scripts/2_auditar.py"
    python "scripts/2_auditar.py" --sin-crudos

No modifica los Parquet, los datos de origen ni ajustes.py.
Genera CSV y Markdown en salidas/auditoria/.
Requiere: duckdb, pandas, openpyxl (solo para contar Excel crudos).
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import ajustes as A  # noqa: E402


def ruta_configurada(valor: str) -> Path:
    ruta = Path(valor)
    return ruta if ruta.is_absolute() else KIT / ruta


def nombre_limpio(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")


def qid(nombre: str) -> str:
    return '"' + nombre.replace('"', '""') + '"'


def fecha_configurada() -> date | None:
    try:
        return date.fromisoformat(str(A.CORTE))
    except (ValueError, TypeError):
        return None


def contar_crudo(archivo: Path, con: duckdb.DuckDBPyConnection) -> int | None:
    suf = archivo.suffix.lower()
    try:
        if suf == ".csv":
            return int(con.execute("SELECT count(*) FROM read_csv(?, all_varchar=true)", [str(archivo)]).fetchone()[0])
        if suf == ".xlsx":
            hojas = pd.read_excel(archivo, sheet_name=None, dtype=str)
            return sum(len(df) for df in hojas.values())
    except Exception as exc:
        print(f"[AVISO] No pude contar {archivo.name}: {exc}")
    return None


def principal() -> int:
    parser = argparse.ArgumentParser(description="Auditoría DE1, solo lectura de datos")
    parser.add_argument("--sin-crudos", action="store_true", help="No contar CSV/Excel originales")
    args = parser.parse_args()
    datos = ruta_configurada(A.CARPETA_DATOS)
    salidas = ruta_configurada(A.CARPETA_SALIDAS)
    limpio = salidas / "limpio"
    auditoria = salidas / "auditoria"
    if not limpio.is_dir():
        print(f"[ERROR] No existe {limpio}. Ejecuta primero scripts/1_leer_limpiar.py")
        return 2
    archivos = sorted(limpio.glob("*.parquet"))
    if not archivos:
        print(f"[ERROR] No hay Parquet en {limpio}")
        return 2
    auditoria.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    tablas: list[dict] = []
    columnas: list[dict] = []
    llaves: list[dict] = []
    fechas: list[dict] = []
    montos: list[dict] = []
    relaciones: list[dict] = []
    alertas: list[dict] = []
    nombres = {p.stem: p for p in archivos}
    corte = fecha_configurada()
    eventos = {tabla: (alias, id_, fecha, monto) for alias, tabla, id_, fecha, monto in getattr(A, "EVENTOS", [])}
    crudos: dict[str, Path] = {}
    if datos.is_dir() and not args.sin_crudos:
        for p in sorted(datos.iterdir()):
            if p.is_file() and p.suffix.lower() in {".csv", ".xlsx"}:
                crudos.setdefault(nombre_limpio(p.stem), p)
    elif not args.sin_crudos:
        alertas.append(dict(nivel="AVISO", tabla="*", detalle=f"No existe carpeta de datos: {datos}"))

    def aviso(nivel: str, tabla: str, detalle: str) -> None:
        alertas.append(dict(nivel=nivel, tabla=tabla, detalle=detalle))

    for tabla, archivo in nombres.items():
        ruta = str(archivo)
        esquema = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [ruta]).fetchall()
        tipos = {str(f[0]): str(f[1]) for f in esquema}
        n = int(con.execute("SELECT count(*) FROM read_parquet(?)", [ruta]).fetchone()[0])
        n_raw = contar_crudo(crudos[tabla], con) if tabla in crudos else None
        diferencia = (n_raw - n) if n_raw is not None else None
        tablas.append(dict(tabla=tabla, filas_limpias=n, filas_crudas=n_raw, diferencia_filas=diferencia,
                           columnas=len(tipos), archivo=str(archivo)))
        if diferencia is not None and diferencia < 0:
            aviso("REVISAR", tabla, "Silver tiene más filas que el crudo contado; revisar lectura/hojas")
        if diferencia is not None and diferencia > 0:
            aviso("REVISAR", tabla, f"Se redujeron {diferencia} filas; no asumir que son duplicados exactos originales")
        if n == 0:
            aviso("CRITICO", tabla, "Tabla limpia sin filas")
        for columna, tipo in tipos.items():
            nulos, distintos = con.execute(
                f"SELECT count(*) FILTER (WHERE {qid(columna)} IS NULL), "
                f"count(DISTINCT {qid(columna)}) FROM read_parquet(?)", [ruta]
            ).fetchone()
            tasa = (100 * nulos / n) if n else None
            columnas.append(dict(tabla=tabla, columna=columna, tipo=tipo, nulos=nulos,
                                 pct_nulos=round(tasa, 3) if tasa is not None else None,
                                 distintos=distintos))
            if n and nulos == n:
                aviso("REVISAR", tabla, f"Columna completamente nula: {columna}")
            if n and distintos <= 1:
                aviso("AVISO", tabla, f"Columna sin variación: {columna}")
        claves = []
        if tabla == getattr(A, "EMPRESAS", None):
            claves.append((getattr(A, "ID", ""), "maestra"))
        if tabla in eventos:
            claves.append((eventos[tabla][1], "evento"))
        for clave, papel in claves:
            if clave not in tipos:
                aviso("CRITICO", tabla, f"Falta la llave configurada: {clave}")
                continue
            nulos, distintos = con.execute(
                f"SELECT count(*) FILTER (WHERE {qid(clave)} IS NULL), count(DISTINCT {qid(clave)}) "
                "FROM read_parquet(?)", [ruta]
            ).fetchone()
            repeticiones = n - nulos - distintos
            llaves.append(dict(tabla=tabla, llave=clave, papel=papel, filas=n, nulos=nulos,
                               ids_distintos=distintos, repeticiones_no_nulas=repeticiones))
            if nulos:
                aviso("REVISAR", tabla, f"{nulos} filas con llave nula ({clave})")
            if papel == "maestra" and repeticiones:
                aviso("CRITICO", tabla, f"Llave maestra no única: {repeticiones} repeticiones no nulas")
        if tabla in eventos:
            _, _, col_fecha, col_monto = eventos[tabla]
            if col_fecha not in tipos:
                aviso("CRITICO", tabla, f"Falta fecha de eventos configurada: {col_fecha}")
            else:
                try:
                    mini, maxi, posteriores = con.execute(
                        f"SELECT min(TRY_CAST({qid(col_fecha)} AS DATE)), "
                        f"max(TRY_CAST({qid(col_fecha)} AS DATE)), "
                        f"count(*) FILTER (WHERE TRY_CAST({qid(col_fecha)} AS DATE) >= ?) "
                        "FROM read_parquet(?)", [corte, ruta]
                    ).fetchone() if corte else (None, None, None)
                    fechas.append(dict(tabla=tabla, columna=col_fecha, minimo=mini, maximo=maxi,
                                       desde_corte=posteriores, corte=corte))
                    if posteriores:
                        aviso("AVISO", tabla, f"{posteriores} eventos desde el corte; pueden ser target válido, NO usarlos como features")
                except Exception as exc:
                    aviso("REVISAR", tabla, f"No se pudo auditar fecha {col_fecha}: {exc}")
            if col_monto not in tipos:
                aviso("CRITICO", tabla, f"Falta monto configurado: {col_monto}")
            else:
                try:
                    total, nulos, negativos, ceros = con.execute(
                        f"SELECT sum(TRY_CAST({qid(col_monto)} AS DOUBLE)), "
                        f"count(*) FILTER (WHERE {qid(col_monto)} IS NULL), "
                        f"count(*) FILTER (WHERE TRY_CAST({qid(col_monto)} AS DOUBLE) < 0), "
                        f"count(*) FILTER (WHERE TRY_CAST({qid(col_monto)} AS DOUBLE) = 0) "
                        "FROM read_parquet(?)", [ruta]
                    ).fetchone()
                    montos.append(dict(tabla=tabla, columna=col_monto, suma_limpia=total,
                                       nulos=nulos, negativos=negativos, ceros=ceros))
                    if negativos:
                        aviso("REVISAR", tabla, f"{negativos} montos negativos: verificar si son notas de crédito/ajustes")
                except Exception as exc:
                    aviso("REVISAR", tabla, f"No se pudo auditar monto {col_monto}: {exc}")
    maestra = getattr(A, "EMPRESAS", "")
    llave_maestra = getattr(A, "ID", "")
    if maestra not in nombres:
        aviso("CRITICO", maestra, "No existe la tabla maestra configurada")
    else:
        maestro_cols = {r[0] for r in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(nombres[maestra])]).fetchall()}
        if llave_maestra in maestro_cols:
            for tabla, (_, clave, _, _) in eventos.items():
                if tabla not in nombres:
                    aviso("CRITICO", tabla, "Tabla de eventos configurada ausente")
                    continue
                cols_evt = {r[0] for r in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(nombres[tabla])]).fetchall()}
                if clave not in cols_evt:
                    continue
                consulta = f"""
                WITH e AS (SELECT DISTINCT CAST({qid(clave)} AS VARCHAR) id
                           FROM read_parquet(?) WHERE {qid(clave)} IS NOT NULL),
                     m AS (SELECT DISTINCT CAST({qid(llave_maestra)} AS VARCHAR) id
                           FROM read_parquet(?) WHERE {qid(llave_maestra)} IS NOT NULL)
                SELECT count(*) AS ids_evento,
                       count(*) FILTER (WHERE m.id IS NOT NULL) AS encontrados
                FROM e LEFT JOIN m ON e.id = m.id
                """
                total, encontrados = con.execute(consulta, [str(nombres[tabla]), str(nombres[maestra])]).fetchone()
                relaciones.append(dict(tabla_evento=tabla, llave_evento=clave, tabla_maestra=maestra,
                                       llave_maestra=llave_maestra, ids_evento=total, ids_encontrados=encontrados,
                                       pct_cobertura=round(100 * encontrados / total, 3) if total else None))
                if encontrados < total:
                    aviso("REVISAR", tabla, f"{total - encontrados} IDs de eventos no están en la maestra")
    for tabla in eventos:
        if tabla not in nombres:
            aviso("CRITICO", tabla, "Falta el Parquet de una tabla EVENTOS configurada")
    if not corte:
        aviso("CRITICO", "ajustes", "CORTE no es fecha ISO YYYY-MM-DD")

    def escribir_csv(nombre: str, registros: list[dict], campos: list[str]) -> None:
        with (auditoria / nombre).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos)
            w.writeheader()
            w.writerows(registros)

    escribir_csv("tablas.csv", tablas, ["tabla", "filas_limpias", "filas_crudas", "diferencia_filas", "columnas", "archivo"])
    escribir_csv("columnas.csv", columnas, ["tabla", "columna", "tipo", "nulos", "pct_nulos", "distintos"])
    escribir_csv("llaves.csv", llaves, ["tabla", "llave", "papel", "filas", "nulos", "ids_distintos", "repeticiones_no_nulas"])
    escribir_csv("fechas.csv", fechas, ["tabla", "columna", "minimo", "maximo", "desde_corte", "corte"])
    escribir_csv("montos.csv", montos, ["tabla", "columna", "suma_limpia", "nulos", "negativos", "ceros"])
    escribir_csv("relaciones.csv", relaciones, ["tabla_evento", "llave_evento", "tabla_maestra", "llave_maestra", "ids_evento", "ids_encontrados", "pct_cobertura"])
    escribir_csv("alertas.csv", alertas, ["nivel", "tabla", "detalle"])
    texto = ["# Auditoría DE1 — Hellen", "", f"- Kit: `{KIT}`", f"- Corte configurado: `{A.CORTE}`",
             f"- Tablas limpias: **{len(tablas)}**", f"- Alertas: **{len(alertas)}**", "",
             "## Tablas", "", "| Tabla | Filas crudas | Filas limpias | Diferencia |", "|---|---:|---:|---:|"]
    for t in tablas:
        texto.append(f"| {t['tabla']} | {t['filas_crudas'] if t['filas_crudas'] is not None else 'N/D'} | {t['filas_limpias']} | {t['diferencia_filas'] if t['diferencia_filas'] is not None else 'N/D'} |")
    texto += ["", "## Alertas", "", "| Nivel | Tabla | Hallazgo |", "|---|---|---|"]
    for a in alertas:
        texto.append(f"| {a['nivel']} | {a['tabla']} | {a['detalle'].replace('|', '/')} |")
    if not alertas:
        texto.append("| — | — | No se generaron alertas automáticas |")
    texto += ["", "## Interpretación y límites", "",
              "- La reducción de filas NO demuestra por sí sola duplicados exactos originales: la limpieza transforma antes de aplicar DISTINCT.",
              "- Los eventos desde CORTE pueden servir para TARGET, pero NO deben usarse como variables predictoras históricas.",
              "- La suma monetaria es sobre Silver y NO concilia automáticamente contra Raw; verificar moneda, parseo, centinelas y deduplicación por separado.",
              "- Las relaciones comparan IDs distintos; no sustituyen validación de grano ni agregación 1:N.",
              "- Revisar manualmente hallazgos y confirmar reglas del negocio antes de borrar, imputar o modificar datos.",
              "", "## Entrega a Kath", "", "- Ubicación de Parquet: `salidas/limpio/`", "- Archivos de auditoría: `salidas/auditoria/`",
              "- Pendiente: confirmar nombres, tipos, cardinalidad y ventanas con el enunciado.", ""]
    (auditoria / "RESUMEN_DE1.md").write_text("\n".join(texto), encoding="utf-8")
    print(f"[OK] {len(tablas)} tablas auditadas. {len(alertas)} alertas. Reportes: {auditoria}")
    print("[IMPORTANTE] Revisa alertas.csv; no se modificaron los datos limpios.")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
