# Priorización y entrega · de probabilidades a una lista (apunte de Liz)

## 1. Tres maneras de ordenar (y cuándo)

| Si el enunciado dice… | Ordenar por | Por qué |
| --- | --- | --- |
| "maximizar conversiones / clientes" | probabilidad | cada conversión vale lo mismo |
| "maximizar el monto / valor / ingresos" | **valor esperado** = prob × monto | una conversión grande vale más |
| "maximizar rentabilidad" | prob × monto × margen − costo de contactar | si dan margen o costo |

Ejemplo: A tiene 60% y S/ 20 000 (valor 12 000); B tiene 30% y S/ 100 000 (valor 30 000). Por probabilidad
va A primero; por valor, B.

## 2. Monto si convierte (de lo simple a lo mejor)

| Opción | Cómo | Cuándo |
| --- | --- | --- |
| Mediana global | `positivos.target_monto.median()` | sin tiempo |
| **Mediana por rubro** (la del script) | `positivos.groupby(rubro).target_monto.median()` | por defecto: simple y explicable |
| Lo que ya financió antes | `ops_monto_prom` si > 0, si no la mediana | si hay historia de factoring |
| Regresor | `LGBMRegressor` entrenado solo con los que convirtieron | si el monto pesa en la evaluación |

## 3. Capacidad y cupos por zona

- Capacidad: 2.5% de 5 000 = **125** empresas.
- Cupos con **resto mayor** para que sumen exacto: exactos LIMA 62.5, NORTE 22.5, SUR 21.25, CENTRO 12.5,
  ORIENTE 6.25 → enteros 62+22+21+12+6 = 123 → las 2 que faltan van a los decimales mayores → LIMA 63, NORTE 23.
- Dentro de cada zona: `nlargest(cupo, "valor")`. Es la solución óptima cuando la única restricción es el cupo
  por zona (no hace falta optimización matemática).
- Zona vacía o escrita distinto (`Lima` vs `LIMA`): no ocupa cupo. Revisar con `d.zona.value_counts()`.

## 4. Variantes

```python
d = d[d.flag_lead_factoring == 1]               # solo con lead ("convertir más")
d = d[d.flag_lead_factoring == 0]               # solo sin lead ("habilitar más")
d.loc[d.nlargest(k, "prob").index, "priorizado"] = 1   # sin cupos, por probabilidad
```

## 5. El CSV final: controles antes de entregar

- [ ] Nombres y orden de columnas EXACTOS del enunciado (`ajustes.ENTREGA`).
- [ ] 1 fila por empresa y todas las empresas pedidas (`len(sub) == n esperado`).
- [ ] Probabilidades entre 0 y 1, sin vacíos.
- [ ] `priorizado` solo 0/1 y su suma = capacidad.
- [ ] Ids como texto (sin `.0`, con ceros a la izquierda).
- [ ] Separador y decimales que pide el enunciado (`,` vs `;`, `.` vs `,`).
- [ ] Validador oficial del evento en OK.

```python
s = pd.read_csv("salidas/submission.csv", dtype={"id_empresa": str})
print(s.shape, s.id_empresa.is_unique, s.prob_factoring.between(0, 1).all(), s.priorizado.sum())
```

## 6. Hallazgos de negocio (la parte que gana presentaciones)

Formato: **dato + comparación + acción**.
- "COMERCIO convierte 25% vs 18.4% del promedio: priorizar ejecutivos con cartera comercial."
- "Las 125 priorizadas convierten 52% vs 19.9% de la base: 2.6 veces más con las mismas llamadas."
- "Quien ya hizo factoring es la 2.ª señal más fuerte: campañas de recompra."

```python
tr.groupby("rubro_economico").target.mean().sort_values(ascending=False)   # conversión por rubro
tr.groupby(pd.qcut(tr.ventas_anuales, 5)).target.mean()                    # por tamaño (quintiles)
```
