# 16 · ¿Y si las funciones de limpieza no sirven?

**Quién:** Hellen. **Código:** `scripts/extra/limpieza_pandas.py` (plan B en pandas puro, con diagnóstico por columna).

## Escalera de soluciones (de rápida a lenta)

Subir un escalón solo si el anterior no resolvió. **No reescriban todo:** arreglen la columna que falla.

| # | Síntoma | Solución | Dónde |
|---|---|---|---|
| 1 | Una columna salió como texto y era número/fecha | agregarla a `FORZAR_TIPO` | `extra/limpieza_pandas.py` |
| 2 | Un formato raro de número/fecha | agregar el formato a `a_numero` / `a_fecha` (o al macro SQL) | ídem / `1_leer_limpiar.py` |
| 3 | DuckDB falla al leer el archivo | `python extra/limpieza_pandas.py reemplazar` | escribe en `salidas/limpio/` |
| 4 | El archivo es enorme y pandas no aguanta | DuckDB leyendo directo `read_csv(..., all_varchar=true, ignore_errors=true)` | consola DuckDB |
| 5 | Nada lee el archivo | abrirlo como texto, ver las primeras 5 líneas, cortarlo | `head -5 archivo.csv` |

## Paso 0 siempre: diagnosticar antes de limpiar

```
python extra/limpieza_pandas.py solo_diagnostico
```

Imprime por columna: `%nulos`, `%numero`, `%fecha`, cuántos valores distintos y **ejemplos de los valores que NO se pudieron convertir**. Eso dice exactamente qué agregar. Queda guardado en `salidas/diagnostico_columnas.csv`.

Lectura rápida:
- `%numero` entre 50 y 95 y tipo `texto` → hay un formato que no conocemos. Mirar `ejemplos_no_numero`.
- `%nulos` > 90 → columna casi vacía; probablemente no sirve como variable.
- `distintos` = 1 → constante; fuera.
- `distintos` ≈ número de filas y es texto → es un ID o un texto libre; no es variable.

## Problemas reales y su arreglo

| Problema | Cómo se ve | Arreglo en el plan B |
|---|---|---|
| Encoding | `MarÃ­a`, `Ã‘` | `leer()` prueba utf-8 → latin-1 → cp1252 |
| Separador | todo en una columna | `csv.Sniffer` adivina `,` `;` `|` tab |
| Filas rotas | "expected 10 fields, saw 11" | `on_bad_lines="warn"`: avisa y sigue |
| Excel con varias hojas | faltan filas | se apilan todas las hojas (y lo imprime) |
| Montos | `S/ 1,234.50`, `USD 1.234,5`, `(200)`, `15%` | `a_numero`: quita símbolos, detecta formato europeo, paréntesis = negativo |
| Centinelas | `999999`, `-999` | `CENTINELAS` → nulo (revisen cuál usa su base) |
| Fechas mezcladas | `2025-01-03`, `03/01/2025`, `20250103`, `45123` | `a_fecha` prueba formato por formato + serial de Excel |
| Fechas basura | `1900-01-01`, `9999-12-31` | fuera de [1990, 2030] → nulo |
| IDs como número | `20123456789.0`, pierde ceros | todo `ruc/id_/cod_/nro_/dni` se trata como texto |
| Nulos disfrazados | `S/D`, `N/A`, `-`, `?`, `NULL` | `NULOS` → nulo |
| Columnas repetidas | dos `fecha` | queda la primera |
| Duplicados | filas idénticas | `drop_duplicates()` |

## Comprobado en la práctica

El plan B produce las **mismas filas** que DuckDB en las 5 tablas y el modelo da **el mismo Gini** (0.295 OOF / 0.292 examen). Única diferencia: `fecha_ultimo_contacto` sale como fecha (DuckDB la dejaba texto por los `1900-01-01`). O sea: si DuckDB falla, pueden cambiar de motor sin perder nada.

## Reglas de Hellen (para no romper el resto del flujo)

1. **El crudo no se toca.** Todo se escribe en `salidas/`.
2. **Mismo contrato de salida:** una `.parquet` por tabla en `salidas/limpio/`, nombres de columna en minúsculas sin tildes. Así `3_variables.py` no se entera de qué motor limpió.
3. **Cada arreglo, una línea en la bitácora** (qué columna, qué valor raro, qué decisión). El jurado pregunta "¿qué hicieron con los nulos?".
4. **Conciliar montos:** suma de montos crudo vs limpio. Si cambia más que los duplicados, algo se convirtió mal.
5. **Si una columna da problemas y no es clave → fuera.** No vale 30 minutos.

## Comandos de emergencia (copiar y pegar)

```python
import pandas as pd
df = pd.read_csv("datos/archivo.csv", dtype=str, sep=None, engine="python", encoding="latin-1")
df.columns.tolist(); df.head()
df["col"].value_counts(dropna=False).head(20)                   # qué valores hay
df.loc[pd.to_numeric(df["col"], errors="coerce").isna() & df["col"].notna(), "col"].unique()[:20]  # los que no son número
```

```sql
-- DuckDB: leer lo que se pueda y saltar filas rotas
SELECT * FROM read_csv('datos/archivo.csv', all_varchar=true, ignore_errors=true) LIMIT 10;
```
