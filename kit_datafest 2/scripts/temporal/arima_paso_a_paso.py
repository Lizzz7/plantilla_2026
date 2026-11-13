# TEMPORAL · ARIMA paso a paso, con UNA serie, para entender (y explicar al jurado) qué hace cada parte.
#   python temporal/arima_paso_a_paso.py            (usa temporal/datos_serie.csv, la agencia más grande)
#   python temporal/arima_paso_a_paso.py AG03       (otra serie)
# ARIMA(p, d, q) x (P, D, Q, s):
#   p  = cuántos valores pasados usa (parte AR, "autorregresiva")
#   d  = cuántas veces se diferencia para quitar la tendencia (y_t - y_{t-1})
#   q  = cuántos errores pasados usa (parte MA, "media móvil")
#   P, D, Q, s = lo mismo pero mirando 1 ciclo atrás (s = 7 en diario: el mismo día de la semana pasada)
import itertools
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI.parent / "salidas"
ESTACION, HORIZONTE = 7, 28

# ---- 0) una serie diaria limpia ----
df = pd.read_csv(AQUI / "datos_serie.csv", dtype={"agencia": str})
df["fecha"] = pd.to_datetime(df.fecha, format="%d/%m/%Y")
serie = sys.argv[1] if len(sys.argv) > 1 else df.groupby("agencia").retiros_miles.mean().idxmax()
y = df[df.agencia == serie].set_index("fecha").retiros_miles.asfreq("D")
y = y.where(~(y > 5 * y.rolling(35, center=True, min_periods=7).median()))        # outliers -> faltante
y = y.fillna(y.shift(ESTACION)).interpolate()
z = np.log1p(y)                                     # log: un pico de +60% pesa igual en agencias grandes y chicas
entrena, prueba = z.iloc[:-HORIZONTE], z.iloc[-HORIZONTE:]
print(f"Serie {serie}: {len(y)} días. Entreno hasta {entrena.index[-1].date()}, pruebo {HORIZONTE} días.")

# ---- 1) ¿es estacionaria? (media y varianza estables). ARIMA lo necesita ----
# Prueba ADF: H0 = "NO es estacionaria". p < 0.05 -> rechazo -> sí es estacionaria.
for nombre, s in [("original (log)", entrena), ("diferencia estacional (y_t - y_t-7)", entrena.diff(ESTACION))]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = adfuller(s.dropna(), autolag="AIC")[1]
    print(f"  ADF {nombre:38s} p = {p:.4f} -> {'estacionaria' if p < 0.05 else 'NO estacionaria: diferenciar'}")
print("  Lectura: si la original ya es estacionaria, d = 0; la diferencia estacional (D = 1) quita el patrón semanal.")

# ---- 2) ACF / PACF: pistas de p y q ----
# PACF que se corta en el rezago k -> p ~ k.   ACF que se corta en el rezago k -> q ~ k.
# Picos en 7, 14, 21 -> estacionalidad semanal (P, Q).
fig, ax = plt.subplots(2, 1, figsize=(9, 5))
d = entrena.diff(ESTACION).dropna()
plot_acf(d, lags=35, ax=ax[0], title="ACF de la serie con diferencia estacional")
plot_pacf(d, lags=35, ax=ax[1], title="PACF de la serie con diferencia estacional", method="ywm")
plt.tight_layout()
plt.savefig(SALIDAS / "arima_acf_pacf.png", dpi=120)
print("  Gráfico: salidas/arima_acf_pacf.png")

# ---- 3) elegir el orden por AIC (menor = mejor balance ajuste/complejidad), grilla CHICA ----
# En competencia no hay tiempo para grillas grandes: 8 a 16 combinaciones bastan.
grilla = []
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for p, q, P, Q in itertools.product([0, 1, 2], [0, 1], [0, 1], [1]):
        try:
            m = SARIMAX(entrena, order=(p, 0, q), seasonal_order=(P, 1, Q, ESTACION), trend="c").fit(disp=False)
            grilla.append(((p, 0, q), (P, 1, Q, ESTACION), m.aic))
        except Exception:
            continue
grilla = sorted(grilla, key=lambda g: g[2])
print("\n  Top 5 por AIC:")
for o, so, aic in grilla[:5]:
    print(f"    ARIMA{o}x{so}  AIC {aic:,.1f}")
orden, orden_est, _ = grilla[0]

# ---- 4) ajustar y revisar residuos: deberían ser ruido (sin patrón) ----
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    modelo = SARIMAX(entrena, order=orden, seasonal_order=orden_est, trend="c").fit(disp=False)
lb = acorr_ljungbox(modelo.resid.iloc[ESTACION + 1:], lags=[ESTACION, 2 * ESTACION])
print(f"\n  Ljung-Box (H0 = residuos sin patrón): p = {lb.lb_pvalue.round(3).tolist()}"
      " -> si p < 0.05 queda patrón sin capturar (probar otro orden o agregar variables exógenas)")
print("  Coeficientes:\n", modelo.params.round(3).to_string())

# ---- 5) pronóstico con intervalo y comparación contra el naive estacional ----
f = modelo.get_forecast(HORIZONTE)
pred = np.expm1(f.predicted_mean)
ic = np.expm1(f.conf_int(alpha=0.2))                # intervalo 80%: útil para "cuánto efectivo como mínimo/máximo"
real = np.expm1(prueba)
naive = np.tile(np.expm1(entrena.iloc[-ESTACION:]).values, HORIZONTE // ESTACION + 1)[:HORIZONTE]


def wape(a, b):
    return np.abs(np.asarray(a) - np.asarray(b)).sum() / np.abs(np.asarray(a)).sum()


cobertura = ((real >= ic.iloc[:, 0].values) & (real <= ic.iloc[:, 1].values)).mean()
print(f"\n  WAPE ARIMA{orden}x{orden_est}: {wape(real, pred):.3f}   |   naive estacional: {wape(real, naive):.3f}")
print(f"  El intervalo 80% contuvo el valor real el {cobertura:.0%} de los días (ideal ~80%)")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(y.index[-4 * HORIZONTE:], y.iloc[-4 * HORIZONTE:], color="#9a9993", label="real")
ax.plot(pred.index, pred, color="#2a78d6", lw=2, label=f"SARIMA{orden}x{orden_est}")
ax.fill_between(pred.index, ic.iloc[:, 0], ic.iloc[:, 1], color="#2a78d6", alpha=0.15, label="intervalo 80%")
ax.plot(pred.index, naive, color="#eb6834", lw=1.5, ls="--", label="naive estacional")
ax.set_title(f"ARIMA en la serie {serie}: pronóstico de {HORIZONTE} días", loc="left")
ax.legend(frameon=False, loc="upper left")
plt.tight_layout()
plt.savefig(SALIDAS / "arima_pronostico.png", dpi=120)
print("  Gráfico: salidas/arima_pronostico.png")
