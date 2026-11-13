"""
CONFIG — lo primero que se edita para un reto nuevo. Lo cuida NAT (los demás proponen cambios).

Cómo leer este archivo:
  - Cada bloque dice QUÉ es, CUÁNDO cambiarlo y trae EJEMPLOS comentados (# ...) de otros retos.
  - Si algo no aplica al reto, se pone None o [] (lista vacía). La plantilla se salta esa parte
    y lo avisa; NO se cae.
  - Nombres de tablas y columnas NORMALIZADOS: minúsculas, sin tildes, '_' en vez de espacios.
    "Operaciones Factoring.xlsx" -> tabla "operaciones_factoring"; "Fecha Operación" -> "fecha_operacion".
    El paso 1 imprime todos los nombres reales: cópienlos de ahí.

Viene llenado para los DATOS DE PRÁCTICA (python datos_practica.py). Recetas para otros retos: README.md.
"""

# ================================================================= 0. TIPO DE RETO
# "clasificacion" = predecir SI/NO (¿tomará factoring?)  -> métrica Gini, salida = probabilidad
# "regresion"     = predecir un NÚMERO (¿cuánto financiará?) -> métrica R², salida = valor predicho
TIPO_PROBLEMA = "clasificacion"

# ================================================================= 1. CARPETAS Y LECTURA
CARPETA_DATOS = "datos"        # archivos del caso (.csv, .txt, .xlsx). NUNCA se suben a git
CARPETA_SALIDAS = "salidas"    # todo lo que produce la plantilla

# Opciones por archivo, SOLO si alguno viene raro (nombre del archivo tal cual está en datos/):
#   hoja="Datos"        -> leer solo esa hoja del Excel
#   saltar_filas=2      -> el encabezado no está en la fila 1 (hay un título arriba)
#   separador=";"       -> CSV separado por ; o | o tab ("\t")
OPCIONES_LECTURA = {
    # "Reporte Ventas.xlsx": dict(hoja="Detalle", saltar_filas=3),
    # "transacciones.txt": dict(separador="|"),
}

# Tablas que vienen PARTIDAS y deben ser UNA (mismas columnas). Queda una columna "_origen".
# Ej. reto estilo Kaggle: train.csv (con target) + test.csv (sin target) -> una tabla "base".
UNIR = {
    # "base": ["train", "test"],
}

# ================================================================= 2. FECHAS (del enunciado)
FECHA_CORTE = "2025-07-01"     # el "día de decidir": variables con datos ANTES, target DESPUÉS
HORIZONTE_MESES = 6            # el target mira [corte, corte + 6 meses)
CORTE_ANTERIOR = "2025-01-01"  # corte - horizonte: con este se ENTRENA (validación fuera de tiempo)
HISTORIA_MESES = 12            # meses ANTES de cada corte que usan las variables. Los datos deben
                               # cubrirlos también para el CORTE ANTERIOR (el paso 2 lo revisa).

# ================================================================= 3. TABLAS
# EMPRESAS: define las filas del modelo (1 fila = 1 empresa/cliente). Debe tener a TODAS las que
# se van a predecir. Sus columnas (zona, rubro, ventas...) entran como variables.
EMPRESAS = dict(tabla="maestro_clientes", id="ruc_cliente")

# ATRIBUTOS: otras tablas de 1 fila por empresa (perfil, buró...). [] si no hay.
ATRIBUTOS = [
    dict(tabla="perfil_cliente", id="cod_cliente"),
]

# EVENTOS: tablas con MUCHAS filas por empresa y una fecha (facturas, operaciones, pagos, saldos
# mensuales). Se resumen por empresa SOLO con fechas < corte. [] si no hay.
#   alias  = prefijo corto de sus variables (fact__n, fact__monto_total...)
#   monto  = columna de importe (opcional) · moneda = columna con 'USD'/'PEN' (opcional)
#   extra  = otras columnas para variables especiales (ver AGREGACIONES en 3_variables.py),
#            ej. cp = contraparte/pagador, cat = categoría/canal
EVENTOS = [
    dict(alias="fact", tabla="facturas_electronicas", id="ruc_emisor", fecha="fec_emision",
         monto="imp_factura", moneda="moneda", extra=dict(cp="ruc_pagador")),
    dict(alias="ops", tabla="operaciones_factoring", id="ruc", fecha="fecha_operacion",
         monto="monto_financiado"),
    dict(alias="saldo", tabla="saldos_productos_largo", id="cod_cliente", fecha="periodo",
         monto="saldo_prom"),
]

# ================================================================= 4. TARGET (qué se predice)
# FORMA A · "evento": se CONSTRUYE. 1 si la empresa tuvo un evento de 'tabla' que cumple 'filtro'
#   en [corte, corte + horizonte). id/fecha/monto se toman de EVENTOS (la misma tabla).
#   En regresión el target es la SUMA del monto en esa ventana.
TARGET = dict(tipo="evento", tabla="operaciones_factoring", filtro="estado <> 'ANULADA' AND banco = 'BCP'")

# FORMA B · "columna": el target YA VIENE en una columna (0/1 o un número). Sin cortes: se entrena
#   con las filas que tienen target y se predicen las que no (o las de PREDECIR).
# TARGET = dict(tipo="columna", tabla="base", id="id_cliente", columna="compro")

# A quién hay que predecir, si el reto da una lista aparte (archivo de test). None = automático:
#   forma A -> todas las EMPRESAS en el corte actual · forma B -> las filas sin target.
PREDECIR = None
# PREDECIR = dict(tabla="empresas_a_evaluar", id="id_empresa")

# ================================================================= 5. DECISIONES HUMANAS
# Columnas que NO entran al modelo, con su motivo (se cita al jurado). Se aplica en todas las tablas.
COLUMNAS_FUERA = {
    "fecha_cancelacion_cuenta": "posterior al corte (fuga)",
    "ops_ultimo_semestre": "foto tomada hoy: en el corte actual ya conoce el futuro (fuga)",
    "total_operaciones_hist": "acumulado tomado hoy, incluye el periodo del target (fuga)",
    "razon_social": "nombre: no predice, identifica",
    "observaciones": "texto libre",
    "ventas_copia": "copia de ventas_anuales",
}

# Forzar el tipo de una columna cuando la detección automática se equivoca:
#   "tabla.columna": "texto" | "numero" | "fecha" | "llave"
FORZAR_TIPO = {
    # "maestro_clientes.codigo_ciiu": "texto",     # parece número pero es una categoría
    # "pagos.dia_pago": "numero",                  # se llama 'dia' pero no es fecha
}

# ================================================================= 6. NEGOCIO Y ENTREGA
ZONA = "zona"                   # columna de EMPRESAS con la zona. None si no hay
RUBRO = "rubro_economico"       # columna de EMPRESAS con el rubro. None si no hay
LEAD = "flag_lead_factoring"    # columna 0/1 de lead. None si no hay

# A quiénes se puede priorizar: "todos" · "con_lead" (forma A: convertir más) · "sin_lead" (forma B: habilitar)
ELEGIBLES = "todos"

CAPACIDAD = 0.025               # fracción de la base (0.025 = 2.5%) o número de empresas (ej. 1000). None = sin lista
CUPOS_ZONA = {"LIMA": 50, "NORTE": 18, "SUR": 17, "CENTRO": 10, "ORIENTE": 5}   # % por zona; None = sin cupos

# Archivo final: columna interna -> nombre que pide el enunciado. Borren las que no pidan.
#   id · prob (clasificación) · pred (regresión) · monto (si convierte) · valor (prob x monto)
#   priorizado (1 = en la lista) · zona
ENTREGA = dict(archivo="submission.csv",
               columnas={"id": "id_empresa", "prob": "prob_factoring", "valor": "monto_esperado",
                         "priorizado": "priorizado"})

# ================================================================= 7. LIMPIEZA (rara vez se toca)
TIPO_CAMBIO = 3.75                                     # USD -> PEN
MONEDAS_USD = ["USD", "US$", "DOLARES", "DOLAR"]       # valores de la columna moneda que son dólares
CENTINELAS_TEXTO = ["", "S/D", "SD", "N/A", "NA", "#N/A", "NULL", "NONE", "-", "--", "?", "SIN DATO"]
CENTINELAS_NUMERO = [999999, 9999999, -999, -9999]     # números que significan "sin dato"
# Formatos de fecha en ORDEN de prioridad. Si las fechas vienen mes/día (EE. UU.): pongan '%m/%d/%Y' primero.
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y"]
UMBRAL_TIPO = 0.95                                     # % de valores que deben leerse como número/fecha
SEMILLA = 42                                           # para que todo sea reproducible
