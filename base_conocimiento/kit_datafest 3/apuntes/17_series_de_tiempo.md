# 17 · Problemas temporales: series de tiempo, ARIMA y cortes múltiples

**Quién:** Kath (arma los datos en el tiempo) + Sophia (modelos). **Código:** `scripts/temporal/`.

```
python temporal/datos_temporales.py      # datos de práctica (retiros diarios por agencia)
python temporal/pronostico.py            # 6 métodos + backtest + pronóstico final
python temporal/arima_paso_a_paso.py     # ARIMA explicado, una serie
python temporal/varios_cortes.py         # clasificación con varios cortes apilados
```

## Primero: ¿qué tipo de "temporal" es?

| El enunciado dice… | Tipo | Script |
|---|---|---|
| "¿qué **clientes** harán X en los próximos 6 meses?" | clasificación con corte (lo que ya hacemos) | flujo normal; `varios_cortes.py` si hay pocos positivos |
| "¿**cuánto** se va a demandar/retirar/vender por día/semana/mes?" | **serie de tiempo** (pronóstico) | `pronostico.py` |
| "¿**cuánto** tendrá el cliente en su cuenta el próximo mes?" | regresión con corte (por cliente) | flujo normal con target numérico |
| "¿**cuándo** va a pasar X?" | tiempo hasta el evento | clasificación con varios horizontes (¿en 1, 3, 6 meses?) |

## La regla que no se rompe

> **En el tiempo nunca se mezcla al azar.** Se entrena con el pasado y se mide en el futuro.

Un KFold aleatorio en una serie es una fuga: usa el martes para predecir el lunes. El modelo se ve brillante en validación y falla en el examen.

## Validación hacia adelante (backtest)

```
historia ...............|== 28 días ==|                          ventana 1
historia ............................|== 28 días ==|             ventana 2
historia ...........................................|== 28 días ==|   ventana 3 (termina en el último dato)
```

Cada ventana finge que "hoy" es el inicio de la ventana: entrena con lo anterior, pronostica `HORIZONTE` periodos y mide. Se reportan el promedio y la **peor** ventana (el jurado pregunta "¿y si toca un mes malo?").

## Los métodos, de tonto a sofisticado

| Método | Idea | Cuándo usarlo | Debilidad |
|---|---|---|---|
| **Naive** | mañana = hoy | series sin patrón; baseline | no ve la semana |
| **Naive estacional** | el lunes que viene = el lunes pasado | **el baseline obligatorio**: si no le ganas, no tienes modelo | un día raro se copia |
| **Promedio estacional** | promedio de los últimos 4 lunes | series ruidosas; muy robusto | lento para cambios de nivel |
| **Holt-Winters (ETS)** | suavizado exponencial: nivel + tendencia + estacionalidad, más peso a lo reciente | una serie con tendencia y ciclo claros | no usa variables externas (feriados, quincena) |
| **ARIMA / SARIMA** | modela cómo cada valor depende de los anteriores y de los errores anteriores | una serie, patrones de autocorrelación, quieren **intervalos** | una serie a la vez; lento con muchas series; ciclos múltiples |
| **SARIMAX** | SARIMA + variables externas (feriado, quincena, promoción) | sabes qué eventos mueven la serie | hay que conocer esas variables también en el futuro |
| **LightGBM con rezagos** | un solo modelo para todas las series, con rezagos y calendario como variables | **muchas series** (agencias, productos), eventos de calendario | necesita bastante historia; cuidado con la fuga de rezagos |
| **Prophet** (no incluido) | tendencia + estacionalidades + feriados, automático | prototipo rápido con feriados | suele perder contra los de arriba en backtest; otra librería más |

### Resultado en la práctica (15 agencias, pronóstico de 28 días, 3 ventanas)

| Método | WAPE | Sesgo | Seg. |
|---|---|---|---|
| **LightGBM con rezagos** | **0.124** | −3.4% | 2 |
| SARIMA | 0.165 | −0.1% | 25 |
| Holt-Winters | 0.172 | +1.1% | 8 |
| Promedio estacional | 0.205 | +0.3% | 0 |
| Naive estacional | 0.276 | −0.3% | 0 |
| Naive | 0.280 | −4.0% | 0 |

Gana LightGBM porque **ve la quincena, el fin de mes y los feriados** como variables; ARIMA y Holt-Winters solo ven "el ciclo de 7 días". Eso coincide con lo que reportó la competencia M5 (ventas de Walmart): los métodos ganadores usaron boosting global entre series y variables de calendario (ver `papers/04_series_de_tiempo.md`).

## ARIMA explicado para el jurado (`arima_paso_a_paso.py`)

**ARIMA(p, d, q) × (P, D, Q, s)**

- **p (AR):** cuántos valores pasados usa. "El retiro de hoy se parece al de ayer."
- **d (I):** cuántas veces se diferencia para quitar la tendencia (`y_t − y_{t−1}`).
- **q (MA):** cuántos errores pasados usa. "Si ayer me equivoqué hacia arriba, corrijo."
- **P, D, Q, s:** lo mismo, pero mirando un ciclo atrás (s = 7 en diario: el mismo día de la semana pasada).

**Los 5 pasos del script (y qué decir en cada uno):**

1. **¿Es estacionaria?** Prueba ADF. H0 = "no es estacionaria". p < 0.05 → sí lo es. En la práctica: original p = 0.20 (no), con diferencia estacional p ≈ 0 (sí) → D = 1.
2. **ACF / PACF** (`salidas/arima_acf_pacf.png`): la PACF que se corta en k sugiere p ≈ k; la ACF que se corta en k sugiere q ≈ k; picos en 7, 14, 21 = estacionalidad semanal.
3. **Elegir el orden por AIC** con una grilla chica (12 combinaciones). Menor AIC = mejor equilibrio ajuste/complejidad. Ganó ARIMA(2,0,1)×(0,1,1,7).
4. **Residuos = ruido.** Prueba Ljung-Box: p > 0.05 → no quedó patrón sin capturar (p = 0.99 ✓).
5. **Pronóstico con intervalo 80%** vs naive estacional: WAPE 0.151 vs 0.313. Cobertura del intervalo: 93% (algo ancho; ideal 80%).

Detalle: se modela `log(1 + y)` para que un pico de +60% pese igual en una agencia grande que en una chica, y se vuelve con `expm1`.

## LightGBM con rezagos: la fuga temporal más común

Para pronosticar **28 días adelante**, el valor de "ayer" (rezago 1) **no existe** dentro del horizonte: en el día 20 del pronóstico, "ayer" es el día 19, que también es futuro. Por eso:

```python
REZAGOS = [HORIZONTE + ESTACION * k for k in range(0, 4)]   # 28, 35, 42, 49: todos >= horizonte
base = y.shift(HORIZONTE)                                     # medias móviles que terminan 28 días atrás
```

Si ven un modelo con rezago 1 dando WAPE 0.03 en backtest: es fuga. El examen lo va a destruir.

Variables de calendario que casi siempre sirven en banca peruana: día de la semana, día del mes, **quincena (15–16)**, **fin de mes**, mes, **gratificación (julio y diciembre)**, feriados (28–29 jul, 8 dic, 25 dic, 1 ene, 1 may, 29 jun, 30 ago, 8 oct, 1 nov).

## Varios cortes para clasificación (`varios_cortes.py`)

Cuando el problema es "qué cliente hará X" pero hay pocos positivos, se puede armar la tabla en **varios cortes pasados** y apilarlas (3 cortes = 3 veces más filas). Dos reglas anti-fuga, verificadas en el código:

1. Un corte de entrenamiento `c` solo vale si `c + HORIZONTE ≤ corte de examen` (su target ya pasó).
2. La misma empresa aparece en varios cortes → la validación cruzada **agrupa por empresa** (`StratifiedGroupKFold`).

Y una tercera de calidad: **misma HISTORIA en todos los cortes**. Si el corte viejo tiene 6 meses de historia y el nuevo 12, el modelo aprende "cuánta historia hay" en vez de comportamiento. El script descarta cortes sin historia completa.

En la práctica: apilar 3 cortes dio 0.283 vs 0.282 con uno solo (empate) y 0.29 con 12 meses de historia y un corte. **Lección honesta:** apilar ayuda cuando hay pocos positivos; con 900+ positivos por corte, más historia por empresa vale más que más cortes. Pruébenlo, no lo asuman.

## Checklist temporal (Kath)

- [ ] ¿Hay huecos en las fechas? (`reindex` al calendario completo; `pronostico.py` lo hace)
- [ ] ¿Outliers por error de carga? (>5x la mediana móvil → faltante)
- [ ] ¿Todas las series terminan el mismo día? (se corta en la última fecha común)
- [ ] ¿El horizonte y la frecuencia son los del enunciado? (`HORIZONTE`, `FRECUENCIA`)
- [ ] ¿Algún rezago < horizonte? (fuga)
- [ ] ¿El ganador le gana al naive estacional en **todas** las ventanas?
- [ ] ¿El sesgo es aceptable? (en efectivo, quedarse corto es más caro que sobrar)
