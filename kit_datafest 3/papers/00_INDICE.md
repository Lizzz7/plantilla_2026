# papers/ · Referencias para fundamentar (con enlaces verificados)

Desde el entorno donde se armó el kit no se pueden descargar PDFs, así que cada archivo tiene **un resumen en nuestras palabras, por qué nos sirve y el enlace** al documento original. Descárguenlos antes del evento si quieren tenerlos offline.

**Cómo usarlos en la exposición:** una referencia por decisión, no más. Ejemplo: *"validamos fuera de tiempo porque la fuga temporal es uno de los errores más documentados en minería de datos (Kaufman et al., 2012)"*. Una cita bien puesta demuestra criterio; diez citas parecen relleno.

| Archivo | Tema | Para defender… |
|---|---|---|
| `01_factoring.md` | Factoring: qué es, por qué existe, marco legal en Perú | el entendimiento del negocio |
| `02_modelos.md` | XGBoost, LightGBM, CatBoost, benchmark de scoring | la elección de modelos |
| `03_fugas_y_validacion.md` | Fugas de información y validación | por qué el corte y el examen fuera de tiempo |
| `04_series_de_tiempo.md` | Libro de Hyndman, competencia M5, statsmodels | ARIMA/ETS/boosting en pronóstico |

## Lista corta (si solo leen 4 cosas)

1. **Klapper (2005/2006)** — por qué el factoring funciona: el riesgo se traslada al comprador. → `01_factoring.md`
2. **Kaufman, Rosset y Perlich (2011/2012)** — qué es una fuga y cómo evitarla. → `03_fugas_y_validacion.md`
3. **Lessmann et al. (2015)** — 41 clasificadores comparados en scoring de crédito. → `02_modelos.md`
4. **Hyndman y Athanasopoulos, *Forecasting: Principles and Practice*** (gratis online). → `04_series_de_tiempo.md`
