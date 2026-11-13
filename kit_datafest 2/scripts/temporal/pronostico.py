# TEMPORAL · cuando el reto es PRONOSTICAR un número en el tiempo (demanda, saldos, transacciones, efectivo).
# Compara 6 métodos, de tonto a sofisticado, con validación HACIA ADELANTE (backtest) y entrega el mejor.
#   python temporal/datos_temporales.py     (solo para practicar: crea temporal/datos_serie.csv)
#   python temporal/pronostico.py
# Lo único que se cambia es el bloque AJUSTES. Funciona con 1 serie o con muchas (una por agencia, producto...).
import sys
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")                  # statsmodels avisa mucho sobre convergencia; lo medimos igual
AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

# ===================== AJUSTES =====================
ARCHIVO = AQUI / "datos_serie.csv"
COL_FECHA = "fecha"
COL_SERIE = "agencia"            # None si es una sola serie
COL_VALOR = "retiros_miles"
FORMATO_FECHA = "%d/%m/%Y"       # None = que pandas adivine
FRECUENCIA = "D"                 # "D" diario, "W-MON" semanal, "MS" mensual
HORIZONTE = 28                   # cuántos periodos hacia adelante piden
ESTACION = 7                     # largo del ciclo: 7 en diario (semana), 52 en semanal, 12 en mensual
N_VENTANAS = 3                   # cuántas veces se repite el backtest (más = más confiable, más lento)
METODOS = ["naive", "naive_estacional", "promedio_estacional", "holt_winters", "sarima", "lightgbm_rezagos"]
METRICA = "wape"                 # "wape" | "mae" | "rmse"  (wape = error total / total real)
# ===================================================


# ---------------- 1) leer y dejar UNA fila por (serie, fecha), sin huecos ----------------
df = pd.read_csv(ARCHIVO, dtype={COL_SERIE: str} if COL_SERIE else None)
df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], format=FORMATO_FECHA, errors="coerce")
df[COL_VALOR] = pd.to_numeric(df[COL_VALOR], errors="coerce")
if COL_SERIE is None:
    df["serie"], COL_SERIE = "total", "serie"
df = df.dropna(subset=[COL_FECHA]).groupby([COL_SERIE, COL_FECHA], as_index=False)[COL_VALOR].sum()


# todas las series con el MISMO calendario (de la primera a la última fecha común): las fechas que faltan = NaN
fin = df.groupby(COL_SERIE)[COL_FECHA].max().min()
CALENDARIO = pd.date_range(df[COL_FECHA].min(), fin, freq=FRECUENCIA)


def completar(g):
    g = g.set_index(COL_FECHA)[COL_VALOR].reindex(CALENDARIO)
    # outliers: más de 5 veces la mediana móvil = error de carga -> se tratan como faltantes
    med = g.rolling(5 * ESTACION, center=True, min_periods=ESTACION).median()
    g = g.where(~(g > 5 * med))
    # faltantes: el valor del mismo día del ciclo anterior (respeta la estacionalidad); si no hay, interpolar
    return g.fillna(g.shift(ESTACION)).interpolate(limit_direction="both")


Y = {s: completar(g) for s, g in df.groupby(COL_SERIE)}
print(f"{len(Y)} series, {len(next(iter(Y.values())))} periodos cada una, hasta {fin.date()}")


# ---------------- 2) los métodos. Todos reciben la historia y devuelven HORIZONTE valores ----------------
def naive(y, h):                                 # mañana = hoy
    return np.repeat(y.iloc[-1], h)


def naive_estacional(y, h):                      # el lunes que viene = el lunes pasado
    ult = y.iloc[-ESTACION:].values
    return np.array([ult[i % ESTACION] for i in range(h)])


def promedio_estacional(y, h, k=4):              # promedio de los últimos k lunes, k martes...
    ult = y.iloc[-k * ESTACION:].values.reshape(k, ESTACION).mean(axis=0)
    return np.array([ult[i % ESTACION] for i in range(h)])


def holt_winters(y, h):                          # suavizado exponencial: nivel + tendencia + estacionalidad
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = ExponentialSmoothing(y.values, trend="add", damped_trend=True,
                                 seasonal="mul" if (y > 0).all() else "add", seasonal_periods=ESTACION).fit()
    return m.forecast(h)


def sarima(y, h, orden=(1, 0, 1), orden_est=(0, 1, 1)):   # ARIMA con parte estacional. Ver arima_paso_a_paso.py
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    m = SARIMAX(np.log1p(y.values), order=orden, seasonal_order=(*orden_est, ESTACION), trend="c")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ajuste = m.fit(disp=False)
    return np.expm1(ajuste.forecast(h))                    # log: estabiliza la varianza; expm1 vuelve a la escala


# --- LightGBM GLOBAL: un solo modelo para todas las series, con rezagos y calendario ---
# REGLA ANTI-FUGA: para predecir h periodos adelante, solo valen rezagos >= HORIZONTE.
# (un rezago de 1 día usaría el valor de "ayer", que dentro del horizonte todavía no existe)
REZAGOS = [HORIZONTE + ESTACION * k for k in range(0, 4)]          # 28, 35, 42, 49 en diario


def tabla_lgb(Yd):
    filas = []
    for s, y in Yd.items():
        d = pd.DataFrame({"y": y})
        for r in REZAGOS:
            d[f"rez_{r}"] = y.shift(r)
        base = y.shift(HORIZONTE)
        d["media_7"] = base.rolling(ESTACION).mean()                 # medias que terminan HORIZONTE atrás
        d["media_28"] = base.rolling(4 * ESTACION).mean()
        d["mismo_dia_4"] = sum(y.shift(HORIZONTE + ESTACION * k) for k in range(4)) / 4
        i = d.index
        d["dia_semana"], d["dia_mes"], d["mes"] = i.day_of_week, i.day, i.month
        d["fin_mes"] = i.is_month_end.astype(int)
        d["quincena"] = ((i.day == 15) | (i.day == 16)).astype(int)
        d["serie"] = s
        filas.append(d)
    t = pd.concat(filas)
    t["serie"] = t.serie.astype("category")
    return t


def lightgbm_rezagos(Yhist, h):                  # recibe TODAS las series (es global) y devuelve dict serie->pred
    import lightgbm as lgb
    futuro = {s: pd.concat([y, pd.Series(np.nan, index=pd.date_range(y.index[-1], periods=h + 1,
                                                                        freq=FRECUENCIA)[1:])])
              for s, y in Yhist.items()}
    t = tabla_lgb(futuro)
    X = [c for c in t.columns if c != "y"]
    ent = t[t.y.notna()].dropna(subset=[f"rez_{REZAGOS[-1]}"])
    # objetivo en log: las agencias grandes no dominan; el modelo aprende patrones relativos
    m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=20,
                          subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=42)
    m.fit(ent[X], np.log1p(ent.y))
    pred = t[t.y.isna()]
    out = pd.Series(np.expm1(m.predict(pred[X])), index=pred.index)
    return {s: out[pred.serie == s].values for s in Yhist}, m, X


LOCALES = {"naive": naive, "naive_estacional": naive_estacional, "promedio_estacional": promedio_estacional,
           "holt_winters": holt_winters, "sarima": sarima}


def pronosticar(metodo, Yhist, h):
    if metodo == "lightgbm_rezagos":
        return lightgbm_rezagos(Yhist, h)[0]
    return {s: np.asarray(LOCALES[metodo](y, h)) for s, y in Yhist.items()}


# ---------------- 3) métricas ----------------
def metrica(real, pred, cual=METRICA):
    real, pred = np.asarray(real), np.asarray(pred)
    if cual == "wape":
        return np.abs(real - pred).sum() / np.abs(real).sum()
    if cual == "mae":
        return np.abs(real - pred).mean()
    return np.sqrt(((real - pred) ** 2).mean())


# ---------------- 4) BACKTEST: cortar la serie en el pasado y fingir que es hoy ----------------
#   historia ................|=== H ===|                 ventana 1 (la más vieja)
#   historia ...........................|=== H ===|      ventana 2
#   historia ......................................|=== H ===|   ventana 3 (termina en el último dato)
# Nunca se mezcla al azar: en series de tiempo un KFold aleatorio es una FUGA (usa el futuro para predecir el pasado).
largo = len(next(iter(Y.values())))
origenes = [largo - HORIZONTE * (N_VENTANAS - k) for k in range(N_VENTANAS)]
res, tiempos, guardado = [], {}, {}
for metodo in METODOS:
    t0 = time.time()
    for v, o in enumerate(origenes):
        hist = {s: y.iloc[:o] for s, y in Y.items()}
        try:
            p = pronosticar(metodo, hist, HORIZONTE)
        except Exception as e:                                       # un método que falla no tumba a los demás
            print(f"  {metodo} falló en la ventana {v + 1}: {type(e).__name__}: {e}")
            break
        for s, y in Y.items():
            real = y.iloc[o:o + HORIZONTE].values
            res.append({"metodo": metodo, "ventana": v + 1, "serie": s, "real": real.sum(),
                        "abs_err": np.abs(real - p[s]).sum(), "err": (p[s] - real).sum(),
                        "mae": metrica(real, p[s], "mae"), "rmse": metrica(real, p[s], "rmse")})
        guardado[(metodo, v)] = p
    tiempos[metodo] = time.time() - t0
    print(f"  {metodo:20s} listo ({tiempos[metodo]:.0f}s)")

r = pd.DataFrame(res)
g = r.groupby("metodo")
por_ventana = r.groupby(["metodo", "ventana"])[["abs_err", "real"]].sum()
tabla = pd.DataFrame({
    "wape": g.abs_err.sum() / g.real.sum(),          # error total / total real (todas las series y ventanas)
    "mae": g.mae.mean(), "rmse": g.rmse.mean(),
    "sesgo": g.err.sum() / g.real.sum(),             # + sobreestima, - subestima (importa: faltar efectivo es caro)
    "wape_peor_ventana": (por_ventana.abs_err / por_ventana.real).groupby("metodo").max()})
tabla["segundos"] = pd.Series(tiempos)
tabla = tabla.sort_values(METRICA)
print("\n== BACKTEST (", N_VENTANAS, "ventanas de", HORIZONTE, "periodos ) ==")
print(tabla.round(3).to_string())
mejor = tabla.index[0]
base = tabla.loc["naive_estacional", METRICA] if "naive_estacional" in tabla.index else np.nan
print(f"\nGanador: {mejor}  ({METRICA} {tabla.loc[mejor, METRICA]:.3f}"
      f" vs naive estacional {base:.3f}: {(1 - tabla.loc[mejor, METRICA] / base):.0%} mejor)")
print("Si nada le gana claramente al naive estacional, entreguen el naive estacional y díganlo: es honesto y robusto.")

# ---------------- 5) pronóstico final: reentrenar con TODA la historia ----------------
final = pronosticar(mejor, Y, HORIZONTE)
fechas_fut = pd.date_range(fin, periods=HORIZONTE + 1, freq=FRECUENCIA)[1:]
salida = pd.concat([pd.DataFrame({COL_SERIE: s, COL_FECHA: fechas_fut, "pronostico": np.round(p, 2)})
                    for s, p in final.items()], ignore_index=True)
salida.to_csv(SALIDAS / "pronostico.csv", index=False)
print(f"\nsalidas/pronostico.csv: {len(salida):,} filas ({len(Y)} series x {HORIZONTE} periodos)")

# ---------------- 6) gráficos ----------------
s0 = max(Y, key=lambda s: Y[s].mean())                  # la serie más grande, para mostrar
o = origenes[-1]
fig, ax = plt.subplots(figsize=(10, 4))
y = Y[s0]
ax.plot(y.index[o - 3 * HORIZONTE:o + HORIZONTE], y.iloc[o - 3 * HORIZONTE:o + HORIZONTE], color="#9a9993",
        lw=1.5, label="real")
for metodo, color in [(mejor, "#2a78d6"), ("naive_estacional", "#eb6834")]:
    if (metodo, N_VENTANAS - 1) in guardado:
        ax.plot(y.index[o:o + HORIZONTE], guardado[(metodo, N_VENTANAS - 1)][s0], color=color, lw=2, label=metodo)
ax.axvline(y.index[o], color="#555", ls="--", lw=1)
ax.set_title(f"Serie {s0}: último backtest ({mejor} vs naive estacional)", loc="left")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(SALIDAS / "temporal_backtest.png", dpi=120)

fig, ax = plt.subplots(figsize=(7, 3.5))
tabla[METRICA].sort_values(ascending=False).plot.barh(
    ax=ax, color=["#2a78d6" if m == mejor else "#9a9993" for m in tabla[METRICA].sort_values(ascending=False).index])
ax.set_title(f"{METRICA.upper()} del backtest (más bajo = mejor)", loc="left")
plt.tight_layout()
plt.savefig(SALIDAS / "temporal_metodos.png", dpi=120)
print("Gráficos: salidas/temporal_backtest.png, salidas/temporal_metodos.png")
