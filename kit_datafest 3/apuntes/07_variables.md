# Variables · recetas que funcionan (apunte de Kath)

Una buena variable cumple tres cosas: **existe el día del corte**, **tiene sentido de negocio** y **separa**
(Gini sola > 0.02). Todas se calculan con `WHERE fecha < corte`.

## 1. Las familias

| Familia | Qué responde | SQL (dentro del `GROUP BY id`) | Por qué ayuda en factoring |
| --- | --- | --- | --- |
| Frecuencia | ¿cuánto opera? | `count(*)` | más facturas = más necesidad de caja |
| Monto | ¿cuánto mueve? | `sum(m)`, `avg(m)`, `max(m)` | tamaño del negocio |
| Recencia | ¿hace cuánto fue lo último? | `date_diff('day', max(f), corte)` | activo vs dormido |
| Ventanas | ¿qué hizo últimamente? | `count(*) FILTER (WHERE f >= corte - INTERVAL 3 MONTH)` | lo reciente pesa más |
| Tendencia | ¿crece o cae? | `sum(m) FILTER (3m) / (sum(m) FILTER (12m) / 4)` | > 1 = crece |
| Antigüedad | ¿desde cuándo? | `date_diff('day', min(f), corte)` | relación madura |
| Regularidad | ¿opera seguido? | `count(DISTINCT date_trunc('month', f))` | meses activos |
| Diversificación | ¿a cuántos les vende? | `count(DISTINCT pagador)` | pocos pagadores = riesgo/necesidad |
| Concentración (HHI) | ¿depende de uno? | suma de (participación de cada pagador)² | 1 = un solo pagador |
| Plazo | ¿cuánto tarda en cobrar? | `avg(dias_plazo)` | plazos largos = más necesidad de factoring |
| Historia del producto | ¿ya hizo factoring? | `count(*)` en operaciones antes del corte | la 2.ª más importante en la práctica |
| Ratios | relaciones | `ops_monto / ventas_anuales` | compara empresas de distinto tamaño |
| Atributos | quién es | rubro, zona, segmento, antigüedad (`fec_alta` → días) | contexto |

## 2. Cómo agregar una variable (3 pasos)

1. Escriban la línea en el SQL de `3_variables.py` (bloque b):
   ```sql
   count(DISTINCT ruc_pagador) AS fact_n_pagadores,
   avg(dias_plazo)             AS fact_plazo_prom,
   ```
2. Corran `python 3_variables.py` y miren su Gini en `3_fugas.png` (¿> 0.02? ¿< 0.5?).
3. Corran `python 4_modelo.py`: ¿subió el Gini? ¿Aparece en la importancia? Si no aporta, sáquenla.

## 3. Concentración (HHI), paso a paso

```sql
WITH por_pagador AS (                      -- monto por empresa y pagador
  SELECT ruc_emisor id, ruc_pagador, sum(imp_factura) m
  FROM 'salidas/limpio/facturas_electronicas.parquet'
  WHERE fec_emision < DATE '2025-07-01' AND fec_emision >= DATE '2024-07-01'
  GROUP BY 1, 2),
participacion AS (                         -- qué parte de lo facturado va a cada pagador
  SELECT id, m / sum(m) OVER (PARTITION BY id) AS p FROM por_pagador)
SELECT id, sum(p * p) AS hhi FROM participacion GROUP BY id
```
HHI = 1 → le vende a un solo pagador. HHI = 0.1 → muy diversificada.

## 4. Errores típicos

| Error | Consecuencia | Prevención |
| --- | --- | --- |
| Unir la tabla de eventos sin resumir | montos multiplicados, empresas repetidas | `GROUP BY id` primero; `assert id.is_unique` |
| `<=` en vez de `<` en el corte | fuga de frontera | revisar siempre el `WHERE` |
| Llenar "sin eventos" con vacío | el modelo lo trata raro | 0 para conteos/sumas; "muy antiguo" para recencia |
| Acumulados con historia distinta entre cortes | el modelo no se sostiene en el tiempo | misma `HISTORIA` en ambos cortes; preferir ratios |
| Columnas mensuales posteriores al corte (`saldo_202507`) | fuga | usar solo meses < corte, renombrados "hace 1 mes", "hace 2"... |
| 200 variables "por si acaso" | ruido: el modelo empeora | pocas y con sentido; las sin señal fuera |

Lección medida: con 99 variables (40 de buró sin señal) la logística perdía contra la regla simple; con 19
variables con sentido, gana (0.292 vs 0.260).

## 5. Frase para el jurado

"Cada variable describe a la empresa el día del corte: cuánto factura, si crece, a cuántos pagadores les vende y si
ya usó factoring. Ninguna mira después del corte: lo comprobamos siguiendo empresas una por una."
