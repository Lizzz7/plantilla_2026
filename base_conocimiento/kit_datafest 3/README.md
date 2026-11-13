# Kit DataFest · factoring

- `scripts/`: 5 scripts cortos (uno por persona) + `ajustes.py`. ~430 líneas en total, con 7 gráficos.
- `scripts/extra/`, `scripts/temporal/`, `scripts/optimizacion/`: plan B y ampliaciones (métricas, más modelos,
  limpieza alternativa, series de tiempo con ARIMA, priorización con restricciones).
- `GLOBAL_EQUIPO.md`: quién hace qué, con qué script, qué entrega a quién y el horario del evento.
- `apuntes/`: 21 apuntes. Empiecen por `apuntes/00_LEEME_plan_3h.md`.
- `papers/`: referencias con enlace y resumen para fundamentar decisiones.

```bash
pip install duckdb pandas pyarrow numpy scikit-learn lightgbm matplotlib openpyxl
cd scripts            # los datos del reto van en scripts/datos/
python 1_leer_limpiar.py && python 2_revisar.py && python 3_variables.py && python 4_modelo.py && python 5_entregar.py
```

Extras (opcionales):

```bash
pip install statsmodels xgboost catboost "pulp<3"
python extra/metricas.py                 # todas las métricas sobre el modelo
python extra/mas_modelos.py auc_pr       # 7 modelos con la métrica que pidan
python extra/uno_o_varios.py             # ¿un modelo global o uno por zona?
python extra/limpieza_pandas.py          # plan B de limpieza (escribe en salidas/limpio_pandas/)
python temporal/datos_temporales.py && python temporal/pronostico.py && python temporal/arima_paso_a_paso.py
python temporal/varios_cortes.py
python optimizacion/priorizar_restricciones.py demo
```

Preparado con asistencia de IA (Claude) como material de estudio. Cada integrante reescribe y entiende su script;
declaren la ayuda de IA según las reglas del evento.
