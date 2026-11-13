## Configuración que gobierna el script

En `scripts/ajustes.py`

```python
CORTE = "2025-07-01"
CORTE_ANTERIOR = "2025-01-01"
HORIZONTE = 6       # meses del resultado futuro
HISTORIA = 12       # meses de eventos anteriores
EMPRESAS = "maestro_clientes"
ID = "ruc_cliente"
EVENTOS = [
    ("fact", "facturas_electronicas", "ruc_emisor", "fec_emision", "imp_factura"),
    ("ops", "operaciones_factoring", "ruc", "fecha_operacion", "monto_financiado"),
]
TARGET_TABLA = "operaciones_factoring"
TARGET_FILTRO = "estado <> 'ANULADA' AND banco = 'BCP'"
FUERA = ["fecha_cancelacion_cuenta", "razon_social", "observaciones", "ventas_copia"]
```

Cada tupla `EVENTOS` significa `(alias, nombre_tabla, columna_id, columna_fecha, columna_monto)`! Nat puede ajusta el archivo según los esquemas reales.

### Línea de tiempo (regla de oro)

| Tabla | Historia para variables | Target observado | Uso |
|---|---|---|---|
| Entrena, corte 2025-01-01 | `[2024-01-01, 2025-01-01)` | `[2025-01-01, 2025-07-01)` | Aprender y validar |
| Predice, corte 2025-07-01 | `[2024-07-01, 2025-07-01)` | `[2025-07-01, 2026-01-01)` | Puntuar empresas; el target normalmente es desconocido |

**Los intervalos son semiabiertos:** inicio incluido, fin excluido. `fecha < corte` es imprescindible para las *features*; `fecha >= corte AND fecha < corte + INTERVAL 6 MONTH` es para construir la etiqueta del pasado, no para fabricar características.

**Precaución crítica del script actual:** `armar_tabla()` crea `target` para ambos cortes y rellena con cero a quienes no tienen eventos en el archivo. Si el horizonte futuro de `predice` no está completamente observado, **cero no significa negativo**: significa que la etiqueta es desconocida. No uses el `target` de `predice` para medir desempeño; lo ideal es que el código distinga entre etiqueta disponible y no disponible.


## Diccionario de funciones - Python, pandas y gráficos

| Función / método | Entrada → salida | Propósito y precaución |
|---|---|---|
| `Path(...)`, `/` | cadenas → ruta | Rutas multiplataforma; directorio debe existir. |
| `duckdb.connect()` | configuración → conexión | Ejecutar SQL local; `:memory:` por defecto. |
| `con.sql(sql)` | SQL → relación DuckDB | Consulta diferida/relacional; `.df()` materializa. |
| `.df()` | relación → DataFrame | Fácil integración; **puede consumir mucha RAM**. |
| `.drop_duplicates(A.ID)` | tabla → filas únicas | Ojo con elegir un registro arbitrario. |
| `.drop(columns=...)` | DataFrame → DataFrame | Excluir fugas/textos; revisar lista `FUERA`. |
| `.rename(columns=...)` | DataFrame → DataFrame | Normalizar llave `id`. |
| `pd.api.types.is_datetime64_any_dtype(...)` | columna → booleano | Detectar fechas pandas; no detecta cualquier texto con fechas. |
| `pd.Timestamp(corte)` | fecha → Timestamp | Cálculos de antigüedad. |
| `.dt.days` | timedelta → entero | Días de diferencia. |
| `.merge(..., how='left')` | dos tablas → tabla | Mantener universo de empresas; validar cardinalidad. |
| `.fillna(0)` | nulos → cero | Solo cuando cero representa ausencia real. |
| `.astype(int)` | tipo → entero | Etiqueta binaria. |
| `.is_unique` | serie → booleano | Detectar IDs repetidos. |
| `assert` | condición → error si falsa | Falla temprano; para producción también usar validaciones explícitas. |
| `.sort_values('id')` | DataFrame → ordenado | Orden reproducible. |
| `.reset_index(drop=True)` | índice → secuencia | Evitar índices antiguos. |
| `.to_parquet(..., index=False)` | DataFrame → archivo | Persistir columnas sin índice pandas. |
| `.mean()` | serie → promedio | En target binario = tasa positiva. |
| `.select_dtypes('number')` | DataFrame → numéricas | Selección para diagnóstico univariado. |
| `.nunique()` | serie → número | Comprobar existencia de 2 clases. |
| `.median()` | serie → mediana | Imputación rápida para Gini. |
| `roc_auc_score(y, x)` | verdad + score → AUC | Requiere dos clases y score válido. |
| `abs(...)` | número → magnitud | Detecta señal positiva o negativa. |
| `np.nan` | — → faltante | Indica cálculo no disponible. |
| `pd.DataFrame(...)` | datos → tabla | Reúne métricas por feature. |
| `.iterrows()` | tabla → pares fila | Iterar reporte, no procesar millones de filas. |
| `matplotlib.use('Agg')` | backend → sin GUI | Guardar imágenes en ejecución sin pantalla. |
| `.plot.barh()` | tabla → gráfico | Comparar Gini por variable. |
| `ax.axvline(0.5)` | número → línea | Umbral visual heurístico. |
| `ax.set_title(...)` | texto → título | Interpretabilidad del gráfico. |
| `plt.tight_layout()` | figura → ajuste | Evita recortes. |
| `plt.savefig(...)` | figura → PNG | Guardar evidencia. |
| `if __name__ == '__main__'` | ejecución directa → bloque | Permite importar funciones sin ejecutar todo el pipeline. |

## Diccionario SQL DuckDB 

| Expresión | Significado | Uso |
|---|---|---|
| `SELECT ... FROM 'x.parquet'` | Consulta archivo Parquet directamente | Evita cargar todo a pandas. |
| `COUNT(*)` | Filas por grupo | Frecuencia. |
| `COUNT(DISTINCT pagador)` | Entidades diferentes | Diversificación. |
| `SUM(monto)` / `AVG(monto)` | Total / promedio | Volumen y ticket. |
| `MIN(fecha)` / `MAX(fecha)` | Primer / último evento | Antigüedad / recencia. |
| `FILTER (WHERE ...)` | Agregado condicionado | Ventanas 3m/6m. |
| `DATE_DIFF('day', a, b)` | Días de a a b | Recencia. |
| `DATE_TRUNC('month', fecha)` | Mes de evento | Meses activos. |
| `INTERVAL 12 MONTH` | Duración temporal | Ventanas móviles. |
| `GROUP BY 1` | Agrupar por primera expresión | Una fila por empresa. |
| `LEFT JOIN ... USING (id)` | Conserva filas izquierda | Integrar variables. |
| `COALESCE(x, 0)` | Sustituye NULL | Conteos/volúmenes ausentes. |
| `NULLIF(denominador,0)` | 0 → NULL | Evita división entre cero. |
| `TRY_CAST(x AS DOUBLE)` | Convierte o NULL | Limpieza de números. |
| `TRY_STRPTIME(x, [...])` | Texto → fecha o NULL | Fechas heterogéneas. |
| `DESCRIBE SELECT ...` | Esquema de resultado | Inspección. |
| `EXPLAIN SELECT ...` | Plan de ejecución | Optimización. |
| `COPY (SELECT ...) TO 'x.parquet' (FORMAT PARQUET)` | SQL → Parquet | No materializar en pandas. |
| `ROW_NUMBER() OVER (PARTITION BY id ORDER BY fecha DESC)` | Posición dentro de empresa | Seleccionar registro más reciente. |
| `SUM(m) OVER (PARTITION BY id)` | Total por empresa sin colapsar filas | Ratios/concentración. |

### Cómo pensar una consulta DuckDB?

1. **FROM**: ¿qué archivo leo? ¿Cuál es su grano (una fila = qué)?
2. **WHERE**: ¿qué fechas están permitidas? ¿Hay nulos/operaciones anuladas?
3. **GROUP BY**: ¿cuál es la llave del resultado? ¿Es única?
4. **SELECT**: ¿qué variable de negocio representa cada cálculo?
5. **JOIN**: ¿estoy multiplicando filas? ¿Conservo el universo correcto?
6. **OUTPUT**: ¿puedo guardar en Parquet sin traer millones de filas a memoria?

### Ejemplos DuckDB reutilizables!

**Inspección y conteo sin cargar todo a RAM:**

```python
import duckdb
con = duckdb.connect()
print(con.sql("DESCRIBE SELECT * FROM 'salidas/limpio/facturas_electronicas.parquet'").df())
print(con.sql("SELECT COUNT(*) AS filas FROM 'salidas/limpio/facturas_electronicas.parquet'").fetchone())
```

**Control de cardinalidad antes del JOIN:**

```sql
SELECT ruc_emisor, COUNT(*) AS n
FROM 'salidas/limpio/facturas_electronicas.parquet'
GROUP BY 1
HAVING COUNT(*) > 1
LIMIT 10;
```

Aquí **es normal** que haya varias facturas por emisor. El punto es **agregar primero** y recién después unir con el maestro. Para comprobar que un agregado sí es único:

```sql
WITH agregado AS (
  SELECT ruc_emisor AS id, COUNT(*) AS fact_n
  FROM 'salidas/limpio/facturas_electronicas.parquet'
  GROUP BY 1
)
SELECT COUNT(*) AS filas, COUNT(DISTINCT id) AS ids_unicos FROM agregado;
```

**Guardar un agregado directamente en Parquet:**

```sql
COPY (
  SELECT ruc_emisor AS id, COUNT(*) AS fact_n, SUM(imp_factura) AS fact_monto
  FROM 'salidas/limpio/facturas_electronicas.parquet'
  WHERE fec_emision >= DATE '2024-07-01' AND fec_emision < DATE '2025-07-01'
  GROUP BY 1
) TO 'salidas/fact_agregado.parquet' (FORMAT PARQUET);
```

**Ratios seguros:**

```sql
SELECT id, ops_monto / NULLIF(fact_monto, 0) AS ratio_ops_fact
FROM 'salidas/tabla_features.parquet';
```

**Fechas y meses activos:**

```sql
SELECT ruc_emisor AS id,
       COUNT(DISTINCT DATE_TRUNC('month', fec_emision)) AS meses_activos,
       DATE_DIFF('day', MIN(fec_emision), DATE '2025-07-01') AS antiguedad_dias
FROM 'salidas/limpio/facturas_electronicas.parquet'
WHERE fec_emision >= DATE '2024-07-01' AND fec_emision < DATE '2025-07-01'
GROUP BY 1;
```

**Revisar plan y coste:**

```sql
EXPLAIN SELECT ruc_emisor, COUNT(*)
FROM 'salidas/limpio/facturas_electronicas.parquet'
WHERE fec_emision < DATE '2025-07-01'
GROUP BY 1;
```

## Nuevas variables que se pueden proponer.

| Variable | Idea SQL | Valor de negocio | Precaución |
|---|---|---|---|
| `fact_monto_3m` | `SUM(monto) FILTER (WHERE fecha >= corte - INTERVAL 3 MONTH)` | Volumen reciente | Respetar filtro global 12m. |
| `fact_meses_activos` | `COUNT(DISTINCT DATE_TRUNC('month',fecha))` | Regularidad | Comparabilidad entre cortes. |
| `fact_pagadores` | `COUNT(DISTINCT pagador)` | Diversificación | Solo si columna existe. |
| `fact_antiguedad` | `DATE_DIFF('day',MIN(fecha),corte)` | Tiempo operando | Primer evento solo dentro de ventana si filtras 12m. |
| `fact_tendencia` | `monto_3m / NULLIF(monto_12m / 4,0)` | Crecimiento reciente | Ruido con poco volumen. |
| `ops_fact_ratio` | `ops_monto / NULLIF(fact_monto,0)` | Uso relativo de factoring | Unidades y definición consistentes. |
| HHI pagadores | `SUM(participacion*participacion)` por empresa | Concentración de clientes | Pagadores identificados y montos no negativos. |

**Regla de priorización:** crear pocas variables justificables, comparar resultados en validación temporal y retirar las que no aporten o tengan fuga.






