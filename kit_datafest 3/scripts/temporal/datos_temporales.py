# TEMPORAL · datos de práctica para series de tiempo (NO son del BCP; son inventados con patrones reales).
# Caso: retiros diarios de efectivo (miles de S/) por agencia. Un reto típico de banca:
# "pronostiquen la demanda de efectivo de las próximas 4 semanas para abastecer cada agencia".
# Patrones que trae (los mismos que verán en datos reales):
#   - semana: domingo bajo, viernes/sábado alto      - quincena y fin de mes: picos de pago de sueldos
#   - diciembre alto (gratificación + fiestas)        - feriados de Perú: casi cerrado
#   - tendencia distinta por agencia                  - ruido, días faltantes y algún outlier (para limpiar)
#   python temporal/datos_temporales.py   -> temporal/datos_serie.csv
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
AQUI = Path(__file__).resolve().parent
fechas = pd.date_range("2023-01-01", "2025-06-30", freq="D")
FERIADOS = {(1, 1), (5, 1), (6, 29), (7, 28), (7, 29), (8, 30), (10, 8), (11, 1), (12, 8), (12, 25)}
SEMANA = np.array([1.00, 0.95, 0.95, 1.00, 1.25, 1.15, 0.45])        # lunes ... domingo

filas = []
for k in range(15):
    agencia = f"AG{k:02d}"
    nivel = rng.uniform(80, 400)
    tendencia = rng.uniform(-0.10, 0.35)                              # crecimiento anual
    t = np.arange(len(fechas)) / 365
    y = nivel * (1 + tendencia * t)
    y = y * SEMANA[fechas.day_of_week]
    dia, fin = fechas.day, fechas.is_month_end
    y = y * np.where((dia == 15) | (dia == 16) | fin | (dia == 1), 1.6, 1.0)        # quincena / fin de mes
    y = y * np.where(fechas.month == 12, 1.25, 1.0) * np.where((fechas.month == 7) & (dia >= 14), 1.15, 1.0)
    y = y * np.array([0.15 if (m, d) in FERIADOS else 1.0 for m, d in zip(fechas.month, dia)])
    y = y * rng.lognormal(0, 0.12, len(fechas))
    serie = pd.DataFrame({"fecha": fechas, "agencia": agencia, "retiros_miles": y.round(2)})
    serie = serie.drop(index=rng.choice(len(serie), 12, replace=False))       # días sin registro
    raros = rng.choice(serie.index, 2, replace=False)
    serie.loc[raros, "retiros_miles"] *= 8                                     # error de carga
    filas.append(serie)

df = pd.concat(filas, ignore_index=True)
df["fecha"] = df.fecha.dt.strftime("%d/%m/%Y")                                # formato "peruano", para limpiar
df.to_csv(AQUI / "datos_serie.csv", index=False)
print(f"temporal/datos_serie.csv: {len(df):,} filas, {df.agencia.nunique()} agencias, "
      f"{fechas.min().date()} a {fechas.max().date()}")
