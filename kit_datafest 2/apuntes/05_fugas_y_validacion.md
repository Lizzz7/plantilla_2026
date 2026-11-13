# Fugas y validación · cómo nacen, cómo se detectan, cómo se corrigen

**Fuga (leakage)**: el modelo usa información que no existía el día de decidir. El Gini sube en casa y se cae
cuando el banco evalúa. La pregunta que lo resuelve todo: **¿este dato existía, con este valor, el día del corte?**

## 1. Lo que medimos rompiendo la plantilla a propósito

| Experimento | Gini OOF | Gini examen | Lección |
| --- | --- | --- | --- |
| Correcto | 0.308 | 0.268 | — |
| Columna "foto tomada hoy" (`ops_ultimo_semestre`) | **0.870** | 0.474 | Una fuga sube muchísimo el Gini |
| Error de frontera (eventos hasta 3 meses después del corte) | **0.620** | **0.636** | El examen NO lo detecta: las dos tablas tienen el mismo error |

## 2. Los tipos de fuga

| Tipo | Ejemplo | Cómo nace | Cómo se ve |
| --- | --- | --- | --- |
| Foto tomada hoy | `ops_ultimo_semestre`, `total_operaciones_hist` | El banco extrajo la tabla hoy: ya incluye el periodo del target | Gini bajo en el corte anterior, altísimo en el actual (0.16 → 0.91) |
| Fecha posterior al corte | `fecha_cancelacion`, `fecha_ultimo_contacto` | Registra algo que pasó después | Fechas ≥ corte. Ojo: puede contaminar solo la tabla del corte anterior |
| Frontera | `<=` en vez de `<`, ventana mal calculada | Error de código | Variables de recencia/últimos meses con Gini > 0.5 |
| Columnas mensuales | `saldo_202507` con corte 2025-07-01 | Tablas anchas | Nombres con meses ≥ corte |
| De proceso | lead asignado después de ver el resultado | Decisión del negocio | Una bandera con conversión altísima. Preguntar al mentor |
| De validación | escalar o seleccionar con todos los datos antes de validar | Código | OOF mejor que el examen |

## 3. Flujo de diagnóstico (del síntoma a la causa)

1. **Gini > 0.8 o una variable sola > 0.5** → fuga probable. Consultas Q1–Q3.
2. **OOF bien pero el examen cae > 0.05** → cambio entre periodos o sobreajuste. Consulta Q4.
3. **El modelo no le gana a la regla, o Gini ≈ 0** → ruido, llaves rotas o target mal hecho. Q5–Q6.

## 4. Consultas (probadas; cambien nombres según el reto)

```python
import duckdb, pandas as pd
L = "salidas/limpio/"; con = duckdb.connect()
tr = pd.read_parquet("salidas/entrena.parquet"); te = pd.read_parquet("salidas/predice.parquet")

# Q1 · ¿"foto tomada hoy"? ¿se parece más al PASADO o al FUTURO de la empresa?
con.sql(f"""
WITH pasado AS (SELECT ruc id, count(*) n FROM '{L}operaciones_factoring.parquet'
                WHERE fecha_operacion >= DATE '2025-01-01' AND fecha_operacion < DATE '2025-07-01' GROUP BY 1),
     futuro AS (SELECT ruc id, count(*) n FROM '{L}operaciones_factoring.parquet'
                WHERE fecha_operacion >= DATE '2025-07-01' AND fecha_operacion < DATE '2026-01-01' GROUP BY 1)
SELECT corr(p.ops_ultimo_semestre, coalesce(pa.n, 0)) AS con_pasado,
       corr(p.ops_ultimo_semestre, coalesce(fu.n, 0)) AS con_futuro
FROM '{L}perfil_cliente.parquet' p
LEFT JOIN pasado pa ON p.cod_cliente = pa.id LEFT JOIN futuro fu ON p.cod_cliente = fu.id""").df()
# real: pasado 0.20, futuro 1.00 -> es el futuro disfrazado

# Q2 · ¿fechas posteriores al corte? (revisar LOS DOS cortes)
con.sql(f"""SELECT avg(CASE WHEN fecha_ultimo_contacto >= DATE '2025-01-01' THEN 1 ELSE 0 END) AS tras_corte_anterior,
                   avg(CASE WHEN fecha_ultimo_contacto >= DATE '2025-07-01' THEN 1 ELSE 0 END) AS tras_corte_actual
            FROM '{L}perfil_cliente.parquet'""").df()
# real: 0.185 y 0.0 -> contamina la tabla que ENTRENA

# Q3 · frontera: ¿la variable cuenta exactamente los eventos ANTES del corte?
ej = tr.id.iloc[0]
con.sql(f"""SELECT count(*) FROM '{L}facturas_electronicas.parquet'
            WHERE ruc_emisor = '{ej}' AND fec_emision < DATE '2025-01-01'
              AND fec_emision >= DATE '2025-01-01' - INTERVAL 12 MONTH""").df(), tr.loc[tr.id == ej, "fact_n"]
# deben ser iguales; si la variable es mayor, se cuela el futuro

# Q4 · ¿la variable significa lo mismo en las dos tablas?
cols = ["fact_monto", "ops_monto", "ventas_anuales"]
pd.DataFrame({"entrena": tr[cols].mean(), "predice": te[cols].mean()}).assign(razon=lambda d: d.predice / d.entrena)
# razón lejos de 1 en un acumulado = historia desigual entre cortes

# Q5 · ¿las llaves calzan?
con.sql(f"""SELECT count(DISTINCT f.ruc_emisor) total,
                   count(DISTINCT f.ruc_emisor) FILTER (WHERE m.ruc_cliente IS NOT NULL) calzan
            FROM '{L}facturas_electronicas.parquet' f
            LEFT JOIN '{L}maestro_clientes.parquet' m ON f.ruc_emisor = m.ruc_cliente""").df()

# Q6 · ¿el target cuenta lo que pide el enunciado?
con.sql(f"""SELECT estado, banco, count(*) n FROM '{L}operaciones_factoring.parquet'
            WHERE fecha_operacion >= DATE '2025-07-01' AND fecha_operacion < DATE '2026-01-01'
            GROUP BY ALL ORDER BY n DESC""").df()
```

## 5. Cómo corregir

| Hallazgo | Corrección | Dónde |
| --- | --- | --- |
| La columna no existía el día de decidir | Sacarla y anotar el motivo | `ajustes.FUERA` |
| Error de frontera | Arreglar el `WHERE fecha < corte` | `3_variables.py`, bloque b |
| Historia desigual entre cortes | Igualar `HISTORIA` a lo que cubren los datos en el corte anterior | `ajustes.HISTORIA` |
| Acumulados que crecen con el tiempo | Reemplazar por ratios (últimos 3 meses / 12 meses) | `3_variables.py` |
| Llaves que no calzan | `idn()` o el formato correcto | `1_leer_limpiar.py` |
| Target mal filtrado | Corregir el filtro | `ajustes.TARGET_FILTRO` |

## 6. Rutina (cada vez que corren)

1. Paso 3: lean cada `[!!]` y el gráfico `3_fugas.png`. Para cada sospechosa: Q1 o Q2 y decisión escrita.
2. Paso 4: ¿le gana a la regla? ¿Gini < 0.8? ¿examen y OOF parecidos?
3. Sin target del periodo actual (lo normal en el evento) **no hay examen**: la prueba por variable y Q1–Q3 son su
   única defensa. Háganlas siempre.

Frase: "Probamos que nuestras variables no ven el futuro: cuando metimos una fuga a propósito, el Gini saltó de 0.31
a 0.87 y nuestra prueba la detectó."
