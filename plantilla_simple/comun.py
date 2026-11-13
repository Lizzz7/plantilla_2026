"""
COMÚN — herramientas que usan todos los pasos. No se corre solo.

  - rutas y config
  - conexión DuckDB con las 4 funciones de limpieza (txt, idn, num, fecha) en SQL
  - gini(): la métrica del concurso
  - grafico(): guarda un PNG con el estilo del equipo
  - guardar_resumen(): cada paso deja un .json que correr_todo.py junta en el reporte
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True

import duckdb  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")                     # sin ventana: solo guarda PNG
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
if "--config" in sys.argv:                       # python 3_variables.py --config config_prueba.py
    import importlib.util  # noqa: E402
    _ruta = Path(sys.argv[sys.argv.index("--config") + 1]).resolve()
    _spec = importlib.util.spec_from_file_location("config", _ruta)
    C = importlib.util.module_from_spec(_spec)
    sys.modules["config"] = C
    _spec.loader.exec_module(C)
    print(f"  (usando {_ruta.name})")
else:
    import config as C  # noqa: E402

# Valores por defecto: si alguien borra una línea opcional de config.py, la plantilla NO se cae.
_DEFECTOS = dict(TIPO_PROBLEMA="clasificacion", OPCIONES_LECTURA={}, UNIR={}, ATRIBUTOS=[], EVENTOS=[],
                 PREDECIR=None, COLUMNAS_FUERA={}, FORZAR_TIPO={}, ZONA=None, RUBRO=None, LEAD=None,
                 ELEGIBLES="todos", CAPACIDAD=None, CUPOS_ZONA=None, TIPO_CAMBIO=3.75,
                 MONEDAS_USD=["USD", "US$", "DOLARES", "DOLAR"], UMBRAL_TIPO=0.95, SEMILLA=42,
                 FORMATOS_FECHA=["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"],
                 CENTINELAS_TEXTO=["", "S/D", "N/A", "#N/A", "NULL", "-"], CENTINELAS_NUMERO=[999999],
                 HISTORIA_MESES=12, CORTE_ANTERIOR=None, HORIZONTE_MESES=6)
for _k, _v in _DEFECTOS.items():
    if not hasattr(C, _k):
        setattr(C, _k, _v)
C.TARGET.setdefault("tipo", "evento")
MODO = C.TARGET["tipo"]                       # "evento" (se construye) o "columna" (ya viene)
REGRESION = C.TIPO_PROBLEMA == "regresion"

DATOS = RAIZ / C.CARPETA_DATOS
SAL = RAIZ / C.CARPETA_SALIDAS
LIMPIO = SAL / "limpio"
GRAF = SAL / "graficos"
for _d in (SAL, LIMPIO, GRAF):
    _d.mkdir(parents=True, exist_ok=True)

pd.set_option("display.width", 150)
pd.set_option("display.max_columns", 12)

# Colores (paleta validada para daltonismo): azul = principal, naranja = comparación,
# rojo = SOLO alertas, gris = referencia.
AZUL, NARANJA, ROJO, GRIS, TINTA = "#2a78d6", "#eb6834", "#e34948", "#9a9993", "#52514e"


# ---------------------------------------------------------------- nombres
def normalizar(nombre):
    """'Fecha Operación ' -> 'fecha_operacion'  (minúsculas, sin tildes, _)."""
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "col"


# ---------------------------------------------------------------- DuckDB + limpieza
def conectar():
    """DuckDB con las funciones de limpieza. Todo se hace en SQL: rápido y con poca RAM."""
    con = duckdb.connect()
    txt_cent = ", ".join(f"'{c}'" for c in C.CENTINELAS_TEXTO)
    num_cent = ", ".join(str(float(c)) for c in C.CENTINELAS_NUMERO)
    formatos = ", ".join(f"'{f}'" for f in C.FORMATOS_FECHA)
    con.execute(f"""
    -- TEXTO: sin espacios, sin tildes, MAYÚSCULAS; centinelas ('S/D', '#N/A'...) -> NULL
    CREATE MACRO txt(x) AS CASE WHEN upper(strip_accents(trim(CAST(x AS VARCHAR)))) IN ({txt_cent})
                                THEN NULL ELSE upper(strip_accents(trim(CAST(x AS VARCHAR)))) END;

    -- LLAVE (RUC, código): como texto, sin el '.0' que pega Excel
    CREATE MACRO idn(x) AS regexp_replace(txt(x), '\\.0+$', '');

    -- NÚMERO: 'S/ 1,234.50' -> 1234.5 · '1.234,50' -> 1234.5 · '(500)' -> -500 · '12%' -> 12
    CREATE MACRO _limpio(x) AS regexp_replace(upper(trim(CAST(x AS VARCHAR))), '(S/\\.?|US\\$|USD|PEN|\\$|%|\\s)', '', 'g');
    CREATE MACRO _num2(s) AS CASE
        -- formato europeo SOLO si no hay duda: '1.234,50' · '1.234.567' · '12,5'  ('0.751' es decimal normal)
        WHEN regexp_matches(s, '^-?\\d{{1,3}}(\\.\\d{{3}})+,\\d+$') OR regexp_matches(s, '^-?\\d{{1,3}}(\\.\\d{{3}}){{2,}}$')
             OR regexp_matches(s, '^-?\\d+,\\d{{1,2}}$')
             THEN TRY_CAST(replace(replace(s, '.', ''), ',', '.') AS DOUBLE)
        ELSE TRY_CAST(replace(s, ',', '') AS DOUBLE) END;
    CREATE MACRO _num(s) AS CASE
        WHEN regexp_matches(s, '^\\(.*\\)$') THEN -1 * _num2(substr(s, 2, length(s) - 2))
        ELSE _num2(s) END;
    CREATE MACRO num(x) AS CASE WHEN _num(_limpio(x)) IN ({num_cent}) THEN NULL ELSE _num(_limpio(x)) END;

    -- FECHA: formatos de config.FORMATOS_FECHA + AAAAMMDD + número de serie de Excel (45356 = 2024-03-05)
    CREATE MACRO _fecha(v) AS COALESCE(
        TRY_CAST(try_strptime(v, [{formatos}]) AS DATE),
        TRY_CAST(try_strptime(substr(v, 1, 10), '%Y-%m-%d') AS DATE),
        CASE WHEN regexp_matches(v, '^\\d{{8}}$') THEN TRY_CAST(try_strptime(v, '%Y%m%d') AS DATE) END,
        CASE WHEN regexp_matches(v, '^\\d{{5}}(\\.0+)?$')
             THEN CAST(DATE '1899-12-30' + CAST(CAST(v AS DOUBLE) AS INTEGER) AS DATE) END);
    CREATE MACRO fecha(x) AS CASE WHEN _fecha(trim(CAST(x AS VARCHAR))) >= DATE '1901-01-01'
                                  THEN _fecha(trim(CAST(x AS VARCHAR))) END;
    """.replace("{{", "{").replace("}}", "}"))
    return con


def tabla_limpia(nombre):
    """Ruta (como texto para SQL) de una tabla limpia del paso 1."""
    p = LIMPIO / f"{nombre}.parquet"
    if not p.exists():
        sys.exit(f"\n  Falta la tabla limpia '{nombre}'. ¿Corriste el paso 1? ¿El nombre en config.py es correcto?\n"
                 f"  Tablas disponibles: {sorted(x.stem for x in LIMPIO.glob('*.parquet'))}\n")
    return p.as_posix()


# ---------------------------------------------------------------- métricas
def gini(y, score):
    """Gini = 2·AUC − 1. 0 = azar, 1 = ordena perfecto. Usa el ranking (no importa la escala)."""
    y = np.asarray(y, dtype=float)
    s = pd.Series(np.asarray(score, dtype=float)).fillna(np.nanmin(score) if np.isfinite(np.nanmin(score)) else 0)
    pos, neg = y.sum(), len(y) - y.sum()
    if pos == 0 or neg == 0:
        return float("nan")
    r = s.rank().to_numpy()
    auc = (r[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)
    return 2 * auc - 1


# ---------------------------------------------------------------- gráficos y resumen
def grafico(nombre, titulo, subtitulo=None, ancho=8, alto=4.2):
    """Crea una figura con el estilo del equipo. Devuelve (fig, ax). Guardar con guardar_grafico()."""
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRIS, "axes.labelcolor": TINTA,
                         "xtick.color": TINTA, "ytick.color": TINTA, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12})
    fig, ax = plt.subplots(figsize=(ancho, alto))
    fig.suptitle(titulo, x=0.01, ha="left", fontsize=12.5, fontweight="bold", color="#0b0b0b")
    if subtitulo:
        ax.set_title(subtitulo, loc="left", fontsize=9.5, color=TINTA, fontweight="normal")
    ax.grid(axis="both", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)
    fig._nombre = nombre
    return fig, ax


def guardar_grafico(fig):
    fig.tight_layout()
    ruta = GRAF / f"{fig._nombre}.png"
    fig.savefig(ruta, dpi=130, facecolor="#fcfcfb")
    plt.close(fig)
    print(f"  [gráfico] {ruta}")
    return ruta.name


def guardar_resumen(paso, datos):
    """Cada paso guarda salidas/resumen_<paso>.json: correr_todo.py lo pone en el reporte."""
    (SAL / f"resumen_{paso}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2, default=str),
                                              encoding="utf-8")


def leer_resumen(paso):
    p = SAL / f"resumen_{paso}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def titulo(texto):
    print("\n" + "=" * 72 + f"\n  {texto}\n" + "=" * 72)


def alerta(texto, lista=None):
    print(f"  [!!] {texto}")
    if lista is not None:
        lista.append(texto)


def pct(x):
    return f"{100 * x:.1f}%"


# ---------------------------------------------------------------- target (lo usan los pasos 2 y 3)
def evento(tabla):
    """La definición de EVENTOS (id, fecha, monto...) de una tabla."""
    for e in C.EVENTOS:
        if e["tabla"] == tabla:
            return e
    sys.exit(f"  config: con TARGET tipo 'evento', la tabla '{tabla}' debe estar también en EVENTOS "
             "(para saber id, fecha y monto)")


def sql_target(corte):
    """(forma A) SQL: empresas con eventos del target en [corte, corte + horizonte) y la suma de su monto."""
    e = evento(C.TARGET["tabla"])
    filtro = f"AND ({C.TARGET['filtro']})" if C.TARGET.get("filtro") else ""
    monto = f'sum("{e["monto"]}")' if e.get("monto") else "count(*)"
    return f"""SELECT "{e['id']}" AS id, 1 AS target, {monto} AS target_monto
               FROM '{tabla_limpia(e['tabla'])}'
               WHERE "{e['fecha']}" >= DATE '{corte}'
                 AND "{e['fecha']}" <  DATE '{corte}' + INTERVAL {C.HORIZONTE_MESES} MONTH {filtro}
               GROUP BY 1"""


def hay_target(con, corte):
    """(forma A) ¿Los datos cubren la ventana del target de este corte? (en el evento, el corte actual NO)."""
    e = evento(C.TARGET["tabla"])
    maxf = con.execute(f'SELECT max("{e["fecha"]}") FROM \'{tabla_limpia(e["tabla"])}\'').fetchall()[0][0]
    return maxf is not None and str(maxf) >= str(corte)


def es_binario(y):
    v = pd.Series(y).dropna().unique()
    return len(v) == 2 and set(v) <= {0, 1}


def fuerza(y, x):
    """Qué tan bien ORDENA una variable sola: |Gini| si el target es 0/1, |Spearman| si es un número."""
    y, x = pd.Series(np.asarray(y, dtype=float)), pd.Series(np.asarray(x, dtype=float))
    ok = y.notna()
    y, x = y[ok], x[ok].fillna(x[ok].median())
    if x.nunique() < 2:
        return 0.0
    if es_binario(y):
        return abs(gini(y, x))
    return abs(x.rank().corr(y.rank()))


def sql_etiquetas():
    """(forma B) SQL: id + target de la columna que ya viene. 'SI'/'NO', 'S'/'N', 'TRUE'/'FALSE' -> 1/0."""
    T = C.TARGET
    v = f'upper(CAST("{T["columna"]}" AS VARCHAR))'
    return f"""SELECT "{T['id']}" AS id,
                      CASE WHEN {v} IN ('SI', 'S', 'YES', 'Y', 'TRUE', 'VERDADERO', '1', '1.0') THEN 1
                           WHEN {v} IN ('NO', 'N', 'FALSE', 'FALSO', '0', '0.0') THEN 0
                           ELSE TRY_CAST("{T['columna']}" AS DOUBLE) END AS target
               FROM '{tabla_limpia(T['tabla'])}' WHERE "{T['columna']}" IS NOT NULL"""


def tablas_disponibles():
    return sorted(x.stem for x in LIMPIO.glob("*.parquet"))
