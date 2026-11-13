# Limpieza · cada tipo de dato sucio y su arreglo (apunte de Hellen)

Principio: **leer todo como texto, decidir el tipo midiendo, limpiar con una función por tipo, y conciliar.**

## 1. Casos y soluciones

| Caso | Ejemplo | Problema si no se arregla | Solución |
| --- | --- | --- | --- |
| RUC con `.0` | `20123456789.0` | las tablas no se unen | `idn()`: quitar `\.0+$` |
| RUC con ceros a la izquierda | `0012345` leído como número → `12345` | no se unen | leer como texto (nunca como número) |
| Monto con símbolo | `S/ 1,234.50`, `USD 2,500` | queda texto, no suma | `num()`: quitar `S/`, `USD`, comas de miles |
| Formato europeo | `1.234,50` | 1.23450 o error | detectar `\d{1,3}(\.\d{3})+,\d+` y cambiar separadores |
| Decimal normal | `0.751` | confundirlo con europeo → 751 | solo tratar como europeo si no hay duda |
| Negativo contable | `(500)` | texto | `(x)` → −x |
| Porcentaje | `12%` | texto | quitar `%` (decidir si 12 o 0.12) |
| Centinela numérico | `999999`, `-999`, `-1` | infla promedios y sumas | convertir a vacío (`numero()`) |
| Centinela de texto | `S/D`, `#N/A`, `-`, `SIN DATO` | categoría falsa | `txt()` → vacío |
| Tildes y mayúsculas | `Comércio`, `comercio ` | 2 categorías iguales | `upper(strip_accents(trim()))` |
| Fecha día/mes | `05/03/2024` | 3 de mayo | formato `%d/%m/%Y` primero |
| Fecha AAAAMMDD | `20240305` | número | `strptime(x, '%Y%m%d')` |
| Serial de Excel | `45356` | número | `1899-12-30 + 45356 días` |
| Fecha centinela | `1900-01-01` | antigüedad de 125 años | vacío si < 1901 |
| Filas duplicadas exactas | 1 600 facturas repetidas | montos duplicados | `SELECT DISTINCT` (si no hay id por fila, confirmar) |
| Excel con varias hojas | `Hoja1`, `Hoja2` | se lee solo una | `sheet_name=None` y unir |
| Título arriba del encabezado | 2 filas de título | columnas `Unnamed: 0` | `skiprows=2` |
| CSV con `;` o `\|` | todo en una columna | 1 columna | `delim=';'` |
| Caracteres raros (`Ã±`) | encoding latin-1 | nombres rotos | `encoding='latin-1'` |
| Moneda mezclada | PEN y USD en la misma columna | sumas sin sentido | `CASE WHEN moneda='USD' THEN monto*TC ELSE monto END` |

## 2. Conciliación (la prueba de que no se perdió nada)

Para cada monto: suma antes (texto leído como número) vs después (limpio). Toda diferencia se explica.

Práctica: `imp_factura` 1 555 millones → 708 millones = 834 valores `999999` (834 millones, eran "sin dato") +
1 600 filas duplicadas (13 millones). Cuadra al sol.

```sql
SELECT sum(num(imp_factura))                                         AS antes,
       count(*) FILTER (WHERE num(imp_factura) = 999999)             AS centinelas
FROM read_csv('datos/facturas_electronicas.csv', all_varchar=true);
```

## 3. Qué revisar después de limpiar

- [ ] Ninguna tabla con 0 filas ni con 1 sola columna (otro separador).
- [ ] Cada llave como texto; cada fecha como fecha; cada monto como número (lo imprime el paso 1).
- [ ] % de valores que quedaron vacíos al convertir: más de 5% = formato no contemplado.
- [ ] `min` y `max` de cada monto y fecha con sentido (sin `-1`, sin año 1900, sin montos 999999).

```python
t = pd.read_parquet("salidas/limpio/maestro_clientes.parquet")
t.describe()               # min/max/promedio de números
t.isna().mean().sort_values(ascending=False).head(10)   # % vacíos por columna
t["zona"].value_counts()   # categorías reales (¿hay 'Lima' y 'LIMA'?)
```

Trampa de los datos de práctica: `num_trabajadores` tiene `-1` en ~5% de las filas. ¿Es "sin dato"? Si lo es,
agréguenlo a los centinelas (ojo: el −1 aplicaría a todas las columnas numéricas).

## 4. Frases para el jurado

- "Leemos todo como texto: así ningún formato raro rompe la carga, y decidimos el tipo midiendo."
- "Conciliamos los montos: la diferencia son 834 valores 999999 que significaban 'sin dato' y 1 600 duplicados."
