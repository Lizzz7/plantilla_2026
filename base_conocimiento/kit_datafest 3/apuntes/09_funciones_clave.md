# Funciones clave · chuleta (lo que usan los scripts y lo que más se necesita)

## DuckDB (SQL sobre archivos)

```python
import duckdb
con = duckdb.connect()
con.sql("SELECT * FROM read_csv('x.csv', all_varchar=true)").df()      # leer CSV como texto -> pandas
con.sql("SELECT * FROM 'salidas/limpio/t.parquet' LIMIT 5").df()          # leer parquet
con.execute("COPY t TO 'salida.parquet' (FORMAT parquet)")                # guardar
con.register("df", mi_dataframe)                                           # usar un DataFrame en SQL
```

| SQL | Para qué |
| --- | --- |
| `count(*) FILTER (WHERE f >= corte - INTERVAL 3 MONTH)` | contar solo una parte (ventanas) |
| `date_diff('day', max(f), DATE '2025-07-01')` | días entre fechas (recencia) |
| `date_trunc('month', f)` | agrupar por mes |
| `TRY_CAST(x AS DOUBLE)` | convertir sin romper (vacío si no se puede) |
| `try_strptime(x, ['%d/%m/%Y', '%Y-%m-%d'])` | fechas con varios formatos |
| `regexp_replace(x, '\.0+$', '')` | quitar patrones |
| `upper(strip_accents(trim(x)))` | normalizar texto |
| `SELECT DISTINCT ...` | quitar filas repetidas |
| `LEFT JOIN ... USING (id)` | unir sin perder filas de la izquierda |
| `x / sum(x) OVER (PARTITION BY id)` | participación dentro de cada empresa |
| `QUALIFY row_number() OVER (PARTITION BY id ORDER BY f DESC) = 1` | la última fila de cada empresa |
| `DESCRIBE SELECT * FROM 't.parquet'` | columnas y tipos |

## pandas

| Código | Para qué |
| --- | --- |
| `pd.read_parquet(p)`, `df.to_parquet(p, index=False)` | leer / guardar |
| `pd.read_excel(p, sheet_name=None, dtype=str, skiprows=0)` | Excel: todas las hojas como texto |
| `df.merge(otro, on="id", how="left")` | unir |
| `df.groupby("rubro").target.mean()` | tasa por grupo |
| `df.isna().mean()` | % vacíos por columna |
| `df.describe()` | min/max/promedio |
| `df[c].value_counts()` | categorías y frecuencia |
| `pd.qcut(df.x, 5)` | quintiles |
| `df.nlargest(n, "valor")` | top n |
| `df.id.is_unique` | ¿1 fila por empresa? |
| `pd.api.types.is_numeric_dtype(df[c])` | ¿es número? |

## scikit-learn y LightGBM

```python
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, r2_score
cv = StratifiedKFold(5, shuffle=True, random_state=42)
oof = cross_val_predict(modelo, X, y, cv=cv, method="predict_proba")[:, 1]   # predicción honesta
gini = 2 * roc_auc_score(y, oof) - 1

modelo.fit(X, y); prob = modelo.predict_proba(X_nuevo)[:, 1]

from sklearn.inspection import permutation_importance
pi = permutation_importance(modelo, X, y, scoring="roc_auc", n_repeats=3)   # importancia honesta
```

| Pieza | Qué hace |
| --- | --- |
| `SimpleImputer(strategy="median")` | vacíos → mediana |
| `StandardScaler()` | misma escala |
| `OneHotEncoder(handle_unknown="ignore", min_frequency=0.01)` | categorías → columnas 0/1 (las raras juntas) |
| `make_pipeline(...)`, `make_column_transformer(...)` | encadenar pasos sin fugas en la validación |
| `LogisticRegression(C=0.1, max_iter=3000)` | logística regularizada |
| `lgb.LGBMClassifier(num_leaves=15, min_child_samples=50, ...)` | boosting |
| `X.astype({c: "category" for c in CAT})` | categorías para LightGBM |

## matplotlib

```python
import matplotlib; matplotlib.use("Agg")      # sin ventana: guarda archivos
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4))        # SIEMPRE figura nueva por gráfico
serie.plot.barh(ax=ax, color="#2a78d6")
ax.axvline(0.5, color="#e34948", linestyle="--")
ax.set_title("Título que dice la conclusión", loc="left")
plt.tight_layout(); plt.savefig("salidas/x.png", dpi=120)
```

## Errores frecuentes y su arreglo

| Error | Causa | Arreglo |
| --- | --- | --- |
| `No module named duckdb` | entorno no activado | activar `.venv` |
| `Cannot perform reduction 'median' with string dtype` | columna de texto tratada como número | separar NUM y CAT con `is_numeric_dtype` |
| `Binder Error: ... column not found` | nombre mal escrito | `DESCRIBE` la tabla |
| `aggregate function calls cannot contain window function calls` | `sum(... OVER ...)` dentro de `sum()` | hacerlo en dos CTE |
| Gráficos encimados | no se creó figura nueva | `fig, ax = plt.subplots()` |
| `ValueError: Input contains NaN` | vacíos en un modelo de sklearn | `SimpleImputer` en el pipeline |
