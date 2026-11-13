# AJUSTES DEL RETO: lo único que se cambia cuando llegan los datos (lo cuida Nat).
# Nombres en minúsculas, sin tildes, con _ (el paso 1 imprime los nombres reales).

CARPETA_DATOS = "datos"
CARPETA_SALIDAS = "salidas"

CORTE = "2025-07-01"           # día de decidir: variables ANTES, target DESPUÉS
CORTE_ANTERIOR = "2025-01-01"  # corte - horizonte: con este se entrena
HORIZONTE = 6                  # meses que mira el target
HISTORIA = 12                  # meses de historia para las variables

# tabla con 1 fila por empresa
EMPRESAS = "maestro_clientes"
ID = "ruc_cliente"

# tablas con muchas filas por empresa: (alias, tabla, id, fecha, monto)
EVENTOS = [
    ("fact", "facturas_electronicas", "ruc_emisor", "fec_emision", "imp_factura"),
    ("ops", "operaciones_factoring", "ruc", "fecha_operacion", "monto_financiado"),
]

# target: hubo un evento de esta tabla, con este filtro, en [corte, corte + horizonte)
TARGET_TABLA = "operaciones_factoring"
TARGET_FILTRO = "estado <> 'ANULADA' AND banco = 'BCP'"

# columnas que NO entran (fugas, nombres, textos)
FUERA = ["fecha_cancelacion_cuenta", "razon_social", "observaciones", "ventas_copia"]

ZONA = "zona"
RUBRO = "rubro_economico"
CAPACIDAD = 0.025              # 2.5% de las empresas
CUPOS = {"LIMA": 50, "NORTE": 18, "SUR": 17, "CENTRO": 10, "ORIENTE": 5}

# nombres que pide el enunciado para el archivo final
ENTREGA = {"id": "id_empresa", "prob": "prob_factoring", "valor": "monto_esperado", "priorizado": "priorizado"}
