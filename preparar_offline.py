"""
CORRER ESTO EN CASA, CON INTERNET, ANTES DEL CONCURSO (en las 5 laptops).

El día del concurso puede no haber internet (o ser lento). Este script:
  1. instala las librerías,
  2. descarga la extensión 'excel' de DuckDB (lectura de .xlsx en streaming, poca RAM),
  3. corre el pipeline con datos de prueba para confirmar que todo funciona.
Si la extensión no se descarga, el pipeline igual funciona con fastexcel (usa más RAM).
"""
import subprocess
import sys

PAQUETES = ["duckdb", "polars", "pyarrow", "pandas", "numpy", "plotly", "fastexcel", "openpyxl",
            "xlsxwriter", "scikit-learn", "lightgbm", "optuna", "pulp", "highspy", "scipy"]

print("1/3 instalando librerías…")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", *PAQUETES], check=False)

print("2/3 descargando extensión excel de DuckDB…")
try:
    import duckdb
    duckdb.sql("INSTALL excel; LOAD excel;")
    print("   ok: read_xlsx disponible")
except Exception as e:
    print("   no se pudo (se usará fastexcel):", str(e)[:120])

print("3/3 prueba completa con datos sintéticos…")
subprocess.run([sys.executable, "generar_datos_prueba.py"], check=True)
subprocess.run([sys.executable, "run_pipeline.py"], check=True)
subprocess.run([sys.executable, "run_pipeline.py", "--desde", "features", "--corte", "2025-01-01", "--sufijo", "_t1"], check=True)
subprocess.run([sys.executable, "run_modelo.py", "--rapido"], check=True)
print("\nTodo listo. Abrir salidas/monitor.html")
