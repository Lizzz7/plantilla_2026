# Eficiencia · datos grandes, memoria y qué hacer primero si falta tiempo

## 1. Datos grandes (8 GB)

| Haz | No hagas | Por qué |
| --- | --- | --- |
| Leer CSV con DuckDB (`read_csv`) | `pd.read_csv` de 8 GB | pandas carga todo en RAM (3–4 veces el tamaño del archivo) |
| Leer el Excel **una vez** y guardar Parquet | leer el Excel en cada corrida | el Excel es el paso más lento; Parquet se lee en segundos |
| Resumir eventos en SQL (`GROUP BY id`) y recién pasar a pandas | pasar millones de filas a pandas | después del resumen queda 1 fila por empresa |
| Probar con una muestra: `USING SAMPLE 10%` | correr todo en cada prueba | iterar en segundos, no en minutos |
| Seleccionar solo las columnas necesarias | `SELECT *` en tablas anchas | menos memoria |
| Cerrar Excel y otros programas | — | la RAM se comparte |

Si sale `Out of Memory` en DuckDB: `con.execute("SET memory_limit='3GB'; SET threads=2")`.

En los scripts cortos, `1_leer_limpiar.py` pasa por pandas para simplificar. Con archivos de varios GB, cambien
`.df()` por crear la tabla directo en DuckDB:
```python
con.execute(f"CREATE TABLE crudo AS SELECT * FROM read_csv('{archivo}', all_varchar=true)")
```
y no usen `register`.

## 2. Tiempos de referencia (5 000 empresas, laptop común)

| Paso | Tiempo |
| --- | --- |
| 1 leer y limpiar | ~20 s (el Excel de 80 columnas es lo lento) |
| 2 revisar | ~2 s |
| 3 variables | ~3 s |
| 4 modelo | ~5 s |
| 5 entregar | ~2 s |

Con datos 20–100 veces más grandes, cuenten 10–25 minutos para el paso 1 y minutos para el resto.

## 3. Si falta tiempo: el orden de prioridad

1. **Un submission válido** (aunque sea con la regla simple). Sin entrega, no hay puntaje.
2. **Target y corte bien definidos** (validados con el mentor). Es lo que más pesa en el resultado.
3. **Sin fugas** (prueba de fuga + Q1–Q3 de `05_fugas_y_validacion.md`).
4. **Logística con las variables básicas** (frecuencia, monto, recencia, historia de factoring).
5. **Hallazgos de negocio** para la presentación.
6. Variables extra (plazo, pagadores, HHI).
7. LightGBM y comparación.
8. Ajuste fino (Optuna). **Solo si sobra tiempo.**

## 4. Hábitos que ahorran horas

- Un cambio a la vez, y anotarlo: "agregué plazo_prom → Gini 0.292 → 0.298".
- `git push` cada hora; PR a `main` cada 2 horas.
- Cada script lee lo que dejó el anterior: si el paso 4 falla, no se repiten 1–3.
- Antes de "mejorar el modelo", miren el gráfico de importancia y los hallazgos: a veces la mejora está en una
  variable de negocio, no en un parámetro.
