# Los 5 scripts, bloque por bloque

Lean su script al lado de esta página. Cada bloque dice **qué hace**, **por qué** y **qué cambiarían** si el reto
viene distinto.

---

## ajustes.py (Nat)

Todo lo que depende del reto en un solo lugar. Si cada persona "arregla" nombres dentro de su script, a la
tercera hora nadie sabe qué versión es la buena. Regla: solo Nat lo edita.

| Variable | Qué es | Se saca de |
| --- | --- | --- |
| `CORTE` | día de decidir | enunciado |
| `CORTE_ANTERIOR` | corte − horizonte; con él se entrena | cálculo |
| `HORIZONTE` | meses que mira el target | enunciado |
| `HISTORIA` | meses hacia atrás de las variables | que los datos los cubran para el corte anterior |
| `EMPRESAS`, `ID` | tabla de 1 fila por empresa y su llave | salida del paso 1 |
| `EVENTOS` | tablas con fecha: `(alias, tabla, id, fecha, monto)` | salida del paso 1 |
| `TARGET_TABLA`, `TARGET_FILTRO` | qué cuenta como conversión | enunciado |
| `FUERA` | columnas que no entran (fugas, nombres) | revisión del equipo |
| `CAPACIDAD`, `CUPOS`, `ENTREGA` | lista y formato final | enunciado |

---

## 1_leer_limpiar.py (Hellen)

**Bloque "Funciones de limpieza en SQL"** — 6 macros de DuckDB:
- `txt(x)`: quita espacios y tildes, pasa a MAYÚSCULAS, y "S/D", "#N/A", "-"... → vacío.
- `idn(x)`: llave como texto sin el `.0` que pega Excel (`20123456789.0` → `20123456789`). Si no se hace, las
  tablas no se unen.
- `limpio(x)` + `europeo(s)` + `num(x)`: quitan `S/`, `USD`, `%`, espacios y entienden `1.234,50` (europeo)
  sin confundir `0.751` (decimal normal).
- `numero(x)`: además convierte los centinelas (`999999`, `-999`) en vacío.
- `fecha(x)`: prueba `2024-03-05`, `05/03/2024`, `05-03-2024`, `20240305` y el número de serie de Excel (`45356`).

*Por qué SQL y no pandas:* DuckDB lee archivos más grandes que la RAM y es muy rápido. El SQL se lee casi como
una frase.

**Bloque `nombre_limpio()`** — `'Fecha Operación '` → `fecha_operacion`. Así nadie escribe tildes ni espacios.

**Bucle por archivo**
1. *Leer como texto*: CSV con `all_varchar=true`, Excel con `dtype=str` y todas las hojas juntas. Leer como
   texto nunca falla; si se deja adivinar, un RUC pierde ceros o un "S/D" rompe la carga.
2. *Decidir el tipo midiendo* (sobre 20 000 filas): llave si el nombre empieza con `ruc`/`id_`/`cod_`; fecha si el
   nombre tiene `fec`/`periodo` y el 95% se lee como fecha; número si el 95% se lee como número; si no, texto.
3. *Limpiar y guardar*: `SELECT DISTINCT` aplica la función de cada columna y quita filas idénticas. Se guarda en
   Parquet (columnar, comprimido, rápido).

**Gráfico** `1_filas.png`: filas antes y después; la diferencia son duplicados.

**Si el reto viene distinto:** CSV con `;` → `read_csv(..., delim=';', all_varchar=true)`. Excel con título
arriba → `pd.read_excel(..., skiprows=2)`. Otro centinela → agregarlo en `numero()`. Fechas mes/día → poner
`'%m/%d/%Y'` primero en `fecha()`.

---

## 2_revisar.py (Nat)

1. **¿Existen las tablas y columnas de ajustes.py?** Si no, imprime qué hay y se detiene. Ahorra 30 minutos de
   errores raros en los pasos siguientes.
2. **Tasa base en cada corte**: `LEFT JOIN` de todas las empresas con los eventos del target en la ventana.
   `count(DISTINCT t.id)` cuenta solo las que tuvieron evento (las demás quedan vacías).
3. **Capacidad**: cuántas empresas se pueden priorizar.
4. **Gráfico** `2_linea_tiempo.png`: eventos del target por mes, la franja naranja (target con el que se entrena) y
   la azul (target a predecir). Es la mejor diapositiva para explicar la validación.

**Si el reto viene distinto:** si el target ya viene como columna 0/1, aquí basta con `avg(columna)`.

---

## 3_variables.py (Kath)

**`gini(y, x)`**: qué tan bien ordena una variable sola (2·AUC − 1).

**`armar_tabla(corte)`** — se llama dos veces (corte anterior y actual):
- *a) la empresa*: sus columnas menos `FUERA`. Las fechas se vuelven "días antes del corte"
  (`fec_alta` → `fec_alta_dias` = antigüedad). El modelo no entiende fechas, pero sí distancias.
- *b) eventos*: por cada tabla, un `GROUP BY id` con conteo, suma, promedio, eventos de los últimos 3 meses y
  recencia. **La línea clave**: `WHERE fecha < corte AND fecha >= corte - HISTORIA meses`. Si ese `<` fuera `<=` o
  la ventana se pasara del corte, sería una fuga (en una prueba, el Gini saltó de 0.31 a 0.62).
  Sin eventos = 0 eventos, y recencia = "muy antigua".
- *c) target*: 1 si hubo un evento con el filtro en `[corte, corte + horizonte)`; `target_monto` = suma.
- `assert base.id.is_unique`: si un JOIN duplicó empresas, se detiene. Mejor un error que un resultado falso.

**Prueba de fuga**: Gini de cada variable sola en las dos tablas. Más de 0.5, o un salto grande entre tablas, es
sospecha. Gráfico `3_fugas.png`.

**`if __name__ == "__main__":`**: lo que va debajo (armar las dos tablas, guardar, prueba de fuga) solo corre si
ejecutas `python 3_variables.py`. Si otro script importa el archivo (como `temporal/varios_cortes.py`), solo toma
la función `armar_tabla` sin correr todo.

**Si el reto viene distinto:** una tabla de atributos más (perfil) → `base = base.merge(perfil, on="id")` en el
bloque a). Una variable nueva → una línea más en el SQL (ej. `count(DISTINCT pagador) AS fact_n_pagadores`).
Facturas en dólares → `CASE WHEN moneda='USD' THEN monto*3.75 ELSE monto END` en vez de `monto`.

---

## 4_modelo.py (Sophia)

1. **Datos**: `X_cols` = todo menos id y target. `CAT` = columnas de texto; `NUM` = numéricas.
2. **Candidatos**:
   - *regla*: ordenar por la mejor variable sola. Es la línea base: lo que haría alguien sin modelo.
   - *logística*: vacíos → mediana; `log_signo` comprime montos con cola larga; `StandardScaler` pone todo en la
     misma escala; `OneHotEncoder` convierte cada categoría en columnas 0/1. `C=0.1` = regularización (pesos
     moderados, menos sobreajuste).
   - *LightGBM*: árboles con boosting. `num_leaves=15` y `min_child_samples=50` lo frenan para que no memorice.
3. **Validación**: `cross_val_predict` con 5 pliegues estratificados = cada empresa se predice con un modelo que no
   la vio (OOF). Luego se entrena con todo y se examina en el corte actual.
4. **Elegir**: el mejor OOF; si uno más simple queda a menos de 0.005, gana el simple. Más de 0.8 = sospecha de fuga.
5. **Gráficos**: `4_modelos.png` (Gini por modelo), `4_deciles.png` (conversión por décimo de la lista) y
   `4_importancia.png` (cuánto cae el Gini si se desordena cada variable).

Resultado de práctica: regla 0.260 · logística **0.292** · LightGBM 0.246 en el examen.

**Si el reto viene distinto:** la métrica es AUC-PR → `average_precision_score`. Piden un monto → `LGBMRegressor`
y `r2_score` (ver `11_que_hacer_si.md`).

---

## 5_entregar.py (Liz)

1. **Monto si convierte**: mediana de `target_monto` de las que convirtieron en su rubro (corte anterior).
2. **Valor esperado** = probabilidad × monto.
3. **Cupos que suman exactamente la capacidad** (resto mayor): 2.5% de 5 000 = 125. Exactos: LIMA 62.5, NORTE 22.5,
   SUR 21.25, CENTRO 12.5, ORIENTE 6.25. Redondeando hacia abajo suman 123; las 2 que faltan van a las zonas con el
   decimal más grande → LIMA 63, NORTE 23, SUR 21, CENTRO 12, ORIENTE 6 = 125.
4. **Dentro de cada zona, `nlargest(n, "valor")`**: las de mayor valor hasta llenar el cupo.
5. **CSV** con los nombres del enunciado + 4 controles (1 fila por empresa, prob en [0, 1], sin vacíos,
   priorizadas = capacidad).
6. **Gráfico** `5_rubros.png`: hallazgo de negocio (COMERCIO convierte 25% vs 18.4% del promedio).

**Si el reto viene distinto:** maximizar clientes y no soles → ordenar por `prob`. Solo los que tienen lead →
filtrar `d[d.flag_lead_factoring == 1]` antes del bucle.
