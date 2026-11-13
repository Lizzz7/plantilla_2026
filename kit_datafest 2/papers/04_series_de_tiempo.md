# 04 · Series de tiempo: libro, competencia y librería

## Hyndman, R. J. y Athanasopoulos, G. — *Forecasting: Principles and Practice* (3.ª ed., 2021)

- **Enlace (gratis, online):** https://otexts.com/fpp3/
- **En nuestras palabras:** es el libro de referencia para pronóstico. Recorre desde los métodos simples (que siempre son el baseline) hasta suavizado exponencial (ETS / Holt-Winters), ARIMA y SARIMA, regresión dinámica (ARIMA con variables externas) y cómo evaluar pronósticos con validación hacia adelante. Los ejemplos están en R, pero los conceptos son los mismos que usamos en Python.
- **Capítulos que nos importan:** *The forecaster's toolbox* (métodos simples, métricas y validación con series), *Exponential smoothing*, *ARIMA models* (estacionariedad, diferenciación, ACF/PACF, selección por AIC, SARIMA), *Dynamic regression models*.
- **Para qué lo citamos:** el procedimiento de `arima_paso_a_paso.py` (ADF → ACF/PACF → AIC → residuos → pronóstico) es el que enseña este libro.

## Makridakis, S., Spiliotis, E. y Assimakopoulos, V. (2022) — "M5 accuracy competition: Results, findings, and conclusions"

- **Dónde:** *International Journal of Forecasting* 38(4), 1346–1364. DOI 10.1016/j.ijforecast.2021.11.013
- **Enlace (ficha):** https://econpapers.repec.org/RePEc:eee:intfor:v:38:y:2022:i:4:p:1346-1364
- **En nuestras palabras:** la M5 pidió pronosticar 42,840 series jerárquicas de ventas de Walmart. Los métodos de *machine learning* —sobre todo LightGBM entrenado **globalmente** sobre muchas series a la vez— superaron a los métodos estadísticos clásicos aplicados serie por serie. Los organizadores también destacan prácticas de siempre: combinar pronósticos, usar variables explicativas y modelar bien la estacionalidad y los días especiales.
- **Para qué lo citamos:** por qué nuestro `lightgbm_rezagos` es **un solo modelo para todas las agencias** con variables de calendario (quincena, fin de mes, feriados), y por qué le ganó a ARIMA en el backtest.

## statsmodels (librería de Python)

- **Holt-Winters / ETS:** https://www.statsmodels.org/dev/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html
- **SARIMAX:** https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html
- **Para qué:** si el jurado pregunta "¿qué implementación usaron?", es la estándar en Python.

## Mensaje para la exposición

*"Probamos de lo más simple (naive estacional) a lo más complejo con validación hacia adelante en 3 ventanas. Ganó un modelo global de boosting con variables de calendario, en línea con lo que encontró la competencia M5; ARIMA quedó segundo y lo usamos para dar intervalos de confianza."*
