# Manual maestro de Hellen — Data Engineer 1 (DE1)

**DataFest BCP 2026 · Guía operativa, técnica, estadística y de negocio**  
**Preparado:** 13 de noviembre de 2026  
**Base:** [plantilla_2026](https://github.com/Lizzz7/plantilla_2026), especialmente `plantilla_avanzada`  
**Sistema de trabajo:** Windows / PowerShell  
**Alcance:** preparación previa, recepción de datos, Bronze, perfil, Silver, validaciones, entrega a DE2, riesgos, estadística, negocio y defensa.

> **Importante.** Se revisaron `README.md`, `config.py`, `run_pipeline.py`, `docs/ESCENARIOS.md`, `docs/GUIA_EJECUCION.md` y `docs/MODELADO.md` del repositorio, además de los textos de `evento/config_evento.py` y `docs/PASOS_EVENTO.md` que compartiste. Los módulos internos de `pipeline/` no se inspeccionaron línea por línea: sus responsabilidades se explican según la documentación y el orquestador. Los ejemplos financieros y estadísticos son **hipotéticos**. Las reglas oficiales del concurso prevalecen sobre este manual. **Durante el evento, no usar IA no autorizada ni compartir datos o el enunciado con servicios externos.**

---

# 1. Tu rol exacto

Tu misión como **Hellen, DE1**, es convertir fuentes heterogéneas entregadas por el banco en datos confiables, reproducibles y temporalmente válidos para que Kath (DE2) construya características y DS entrene modelos. No basta con que `run_pipeline.py` termine sin errores: debes demostrar que las filas, llaves, fechas, montos y relaciones tienen sentido.

| Trabajo | Tú ejecutas | Debes coordinar con |
|---|---|---|
| Recibir USB, inventariar, copiar archivos | Sí | Organización / Nat |
| Ingestar a Bronze | Sí | — |
| Perfilar columnas y detectar anomalías | Sí | Negocio si falta semántica |
| Limpiar y generar Silver | Sí | Nat si hay reglas destructivas |
| Validar llaves, duplicados y dinero | Sí | Kath |
| Auditar fuga temporal | Sí | DS / Nat |
| Definir objetivo, corte y capacidad | Ayudas a verificar | Nat / DS deciden |
| Uniones y features finales | Apoyas con grano y riesgos | Kath |
| Modelo, calibración y selección comercial | Debes comprender | DS / Negocio |
| `submission.csv` y presentación | Verificas consistencia si te piden | Integradora / DS |

**Definición de terminado:** inventario de fuentes, Bronze y Silver, controles de filas y tipos, conciliación de importes, llaves y cardinalidad comprobadas, riesgos temporales registrados, Markdown de auditoría y entrega a Kath. Una aprobación de negocio pendiente se documenta; no se inventa.

# 2. Mapa de carpetas del evento

```text
REPO_OFICIAL/
├── REGLAS.md, .github/, scripts/     # organización: no tocar
├── base_conocimiento/                # congelada después del cierre
│   ├── INVENTARIO.md
│   ├── notas/
│   └── plantilla/
│       ├── config.py                 # base; NO editar en evento
│       ├── run_pipeline.py
│       ├── run_modelo.py
│       ├── pipeline/
│       └── evento/
│           ├── config_evento.py      # archivo plantilla
│           └── exportar_submission.py
├── trabajo/
│   ├── config_evento.py              # copia que SÍ se configura
│   └── exportar_submission.py
├── data/                              # datos recibidos: NO subir a Git
├── entregas/submission.csv
├── presentacion/index.html
└── docs/BITACORA_FUENTES.md, docs/USO_DE_IA.md

C:\Users\TU_USUARIO\datafest_trabajo\
├── work/bronze/*.parquet
├── work/silver/*.parquet
├── tmp_duckdb/
└── salidas/*.csv, *.html, tabla_modelo.parquet
```

**Diferencia clave:** `plantilla_avanzada` es la versión de preparación. En el evento se trabaja en el repositorio oficial, ejecutando la plantilla congelada con **`--config trabajo/config_evento.py`**. La guía general del README habla de editar `config.py`; la guía específica del evento prohíbe hacerlo una vez cerrada la base.

# 3. Archivos: qué hace cada uno y cuándo intervenir

| Archivo | Función | Tu acción |
|---|---|---|
| `README.md` | Mapa, arquitectura y comandos | Leer |
| `docs/PASOS_EVENTO.md` | Horario, restricciones, estructura y entregas | Seguir, contrastar con reglas oficiales |
| `docs/GUIA_EJECUCION.md` | Instalación y errores Windows | Preparar laptop |
| `docs/ESCENARIOS.md` | Casos de datos distintos | Consultar antes de improvisar |
| `docs/MODELADO.md` | Modelos, métricas y validación | Estudiar para apoyar y defender |
| `config.py` | Configuración general y valores **de ejemplo** | No editar base congelada |
| `evento/config_evento.py` | Plantilla de configuración específica | Copiar a `trabajo/` |
| `trabajo/config_evento.py` | Rutas y definición del reto real | Revisar y editar con Nat/DS |
| `run_pipeline.py` | Orquesta siete etapas | Ejecutar |
| `pipeline/ingesta.py` | CSV/Excel/otros → Bronze | Revisar conteos; código solo si formato nuevo |
| `pipeline/perfil.py` | Tipos, roles, nulos, constantes, decisiones | Auditar perfil |
| `pipeline/db.py` | Normalización SQL de texto, ID, números, fechas | Verificar conversiones |
| `pipeline/limpieza.py` | Bronze → Silver y bitácora | Auditar transformaciones |
| `pipeline/llaves.py` | Grano, entidad, relaciones | Revisar cobertura/cardinalidad |
| `pipeline/features.py` | RFM, ventanas, montos, red, HHI | Verificar fecha y significado con Kath |
| `pipeline/seleccion.py` | Señal, PSI, Gini, IV, fugas | Revisar alertas con DS |
| `pipeline/monitor.py` | Reporte HTML | Leer y explicar hallazgos |
| `pipeline/regularizar.py` | Imputación/encoding aprendidos solo con train | Entender por qué evita fuga |
| `run_modelo.py` | Modelos, importancia, priorización | DS; comprender resultados |
| `exportar_submission.py` | Predicciones → entrega | DS/integradora |
| `INVENTARIO.md`, `BITACORA_FUENTES.md` | Procedencia y uso | Documentar según destino permitido |
| `DECISIONES_MANUAL` | Overrides al perfil | Proponer con evidencia |

# 4. `config.py`: línea por línea funcional

## 4.1 Rutas y recursos

```python
from pathlib import Path                   # rutas multiplataforma
from pipeline import plataforma            # utilidades de sistema
plataforma.consola_utf8()                  # evitar error Unicode Windows
BASE = Path(__file__).resolve().parent     # carpeta del archivo
RAW_DIR = BASE / 'data' / 'raw'            # entrada genérica
WORK_DIR = BASE / 'data' / 'work'          # Bronze/Silver genéricos
OUT_DIR = BASE / 'salidas'                 # reportes genéricos
TMP_DIR = BASE / 'data' / 'tmp_duckdb'     # disco temporal DuckDB
RAM_GB, MEMORY_LIMIT, THREADS = plataforma.recursos()  # autodetección
MUESTRA_PERFIL = 1_000_000                 # muestra para inferir forma
```

En el **evento** `config_evento.py` sustituye las rutas. El perfil usa una muestra para inferir propiedades; no confundas esa muestra con los conteos totales de filas. No reduzcas memoria o muestra arbitrariamente.

## 4.2 Tiempo y moneda

```python
FECHA_CORTE = '2025-07-01'  # EJEMPLO: instante de decisión
HORIZONTE_MESES = 6        # meses futuros para observar target
VENTANAS_MESES = [3,6,12] # historia para features
TIPO_CAMBIO = 3.75         # EJEMPLO USD→PEN
```

Si el corte es 01/07/2025 y horizonte seis meses, la etiqueta mira `[01/07/2025, 01/01/2026)`; las variables deben estar disponibles **antes del corte**. El tipo de cambio debe corresponder a la fecha y definición del caso; no asumir que 3.75 es válido.

## 4.3 Centinelas y formatos

```python
SENTINELAS_TXT = ['', 'NA', 'N/A', 'NULL', '-', 'S/D', ...]
SENTINELAS_NUM = [-1, -9, -99, ..., 999999, ...]
FECHAS_CENTINELA = ['1900-01-01', '1899-12-30', ...]
FORMATOS_FECHA = ['%Y-%m-%d', '%d/%m/%Y', ...]
```

Un centinela es un **código** que representa ausencia; `999999` también podría ser un monto legítimo. La plantilla combina reglas de frecuencia/extremos para decidir. Comprueba semántica y dinero perdido. El parser de fecha interpreta `05/03/2024` como 5 de marzo (Perú); si el archivo es de EE. UU., confirmar formato con ejemplos inequívocos y adaptar la macro de fechas mediante un cambio autorizado.

## 4.4 Roles semánticos

`PATRONES_ROL` contiene expresiones regulares para detectar `target`, `id`, `fecha`, `moneda`, `monto`, `rubro`, `zona`, `estado`, `contraparte`. El **orden importa**: gana el primer patrón compatible. El nombre ayuda, pero no demuestra el significado: `x17` puede ser un monto y `total_hist` puede contener datos posteriores al corte.

## 4.5 Entidad, eventos y target

```python
ENTIDAD = None       # autodetecta entidad/llave del modelo
EVENTOS = None       # autodetecta tablas de transacciones
TARGET = dict(tabla='operaciones_factoring', id='ruc',
              fecha='fecha_operacion',
              filtro="estado <> 'ANULADA' AND banco = 'BCP'",
              monto='monto_financiado')  # EJEMPLO, NO caso real
```

- **Entidad:** qué representa una fila de la tabla modelo (normalmente empresa).
- **Eventos:** movimientos con fecha, monto, contraparte.
- **Target:** resultado a predecir, **siempre lo define el enunciado**.

Ejemplos ficticios de sintaxis:

```python
# Evento futuro:
TARGET = dict(tabla='ventas', id='id_empresa', fecha='fecha_venta',
              filtro="estado = 'CONFIRMADA'")
# Target ya entregado:
TARGET = dict(tabla='empresas_train', id='id_empresa', columna='flag_compra')
# Evento futuro y monto:
TARGET = dict(tabla='ventas', id='id_empresa', fecha='fecha_venta',
              filtro="estado = 'CONFIRMADA'", monto='monto_neto')
```

No copies filtros ficticios: inspecciona los valores reales (`estado`, `banco`, etc.).

## 4.6 Duplicados, tablas largas, test y cupos

```python
QUITAR_DUPLICADOS_EXACTOS = True  # filas completamente iguales
DEDUP_EVENTOS = None             # mismo evento en distintas fuentes
PIVOTAR = {'saldos_productos_largo': dict(id='cod_cliente',
            fecha='periodo', variable='producto', valor='saldo_prom')} # ejemplo
SEGMENTO = 'maestrocli__flag_lead_factoring' # ejemplo
EVALUAR = None                   # empresas a puntuar
UNIR_TABLAS = None               # train y test de misma entidad
CAPACIDAD = 0.025                # ejemplo: 2.5% de base
CUPOS_ZONA = {'LIMA':50,'NORTE':18,'SUR':17,'CENTRO':10,'ORIENTE':5}
COLUMNA_ZONA = 'maestrocli__zona'
```

`QUITAR_DUPLICADOS_EXACTOS` **no** equivale a `DEDUP_EVENTOS`: una operación puede aparecer en dos fuentes con campos distintos. `PIVOTAR` convierte empresa×mes×producto en columnas. `CAPACIDAD` puede ser fracción o número; los cupos zonales requieren interpretar si son porcentajes, máximos o mínimos. Todo valor del ejemplo debe reemplazarse o desactivarse según el caso.

## 4.7 Umbrales `U`: no son leyes universales

| Parámetro | Valor base | Interpretación |
|---|---:|---|
| `nulos_drop` | 0.98 | >98% nulos, candidato a DROP |
| `nulos_indicador` | 0.70 | >70% nulos, considerar indicador de presencia |
| `top_constante` | 0.995 | >99.5% mismo valor, casi constante |
| `parse_ok` | 0.95 | ≥95% parsea como fecha/número |
| `id_ratio` | 0.90 | Alta unicidad, parece ID |
| `card_alta` | 50 | Categoría con alta cardinalidad |
| `texto_largo` | 40 | Longitud indicativa de texto libre |
| `sentinela_min_share` | 0.005 | 0.5% para sospechar centinela numérico |
| `psi_alerta`, `psi_drop` | 0.10, 0.25 | Cambios de distribución |
| `gini_fuga`, `iv_fuga` | 0.50, 0.50 | Señales de posible fuga, **no prueba** |
| `gini_min` | 0.02 | Señal univariada muy baja |
| `spearman_max` | 0.90 | Correlación alta entre variables |

No bajes umbrales para mejorar métricas sin prueba fuera de tiempo. Una variable con 99% nulos puede ser útil si **la presencia del dato** es informativa; una variable con Gini alto puede ser legítima o una fuga.

# 5. `config_evento.py`: qué hace cada bloque

```python
import importlib.util, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent   # trabajo/
REPO = AQUI.parent                       # raíz repo oficial
PLANTILLA = REPO / 'base_conocimiento' / 'plantilla' / 'config.py'
```

**Si ejecutas el archivo original desde `evento/` sin copiarlo, `REPO` no apunta al repo oficial y fallan las rutas.**

```python
if str(PLANTILLA.parent) not in sys.path:
    sys.path.insert(0, str(PLANTILLA.parent))
_s = importlib.util.spec_from_file_location('config_plantilla', PLANTILLA)
_b = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_b)
globals().update({k:v for k,v in vars(_b).items() if not k.startswith('__')})
```

Carga la configuración base y copia sus parámetros. Las asignaciones posteriores **sobrescriben** los heredados. No modificar este mecanismo sin una prueba.

```python
BASE = AQUI
RAW_DIR = REPO / 'data'
TRABAJO = Path.home() / 'datafest_trabajo'
WORK_DIR = TRABAJO / 'work'
TMP_DIR = TRABAJO / 'tmp_duckdb'
OUT_DIR = TRABAJO / 'salidas'
```

Los archivos del USB van a `data/` del repo **solo si está autorizado**; los Parquet y reportes pesados quedan **fuera** del repo. `Path.home()` en Windows suele ser `C:\Users\...`.

```python
if os.environ.get('DATAFEST_PRUEBA') != '1':
    PIVOTAR = None
    DEDUP_EVENTOS = None
    SEGMENTO = None
    CUPOS_ZONA = None
    COLUMNA_ZONA = None
    EVALUAR = None
    UNIR_TABLAS = None
```

Apaga configuraciones especiales de **ejemplo** en el evento. Pero **no apaga** automáticamente `TARGET`, `FECHA_CORTE`, `HORIZONTE_MESES` ni `CAPACIDAD`. Las líneas comentadas de la sección 3 deben descomentarse y completarse **con Nat/DS**:

```python
FECHA_CORTE = 'AAAA-MM-DD' # sustituir por fecha REAL
HORIZONTE_MESES = 6       # sustituir si el caso indica otra ventana
TARGET = dict(...)        # tabla, id, fecha, filtro o columna reales
CAPACIDAD = 1000          # ejemplo, no asumir
```

`DECISIONES_MANUAL = [dict(tabla='...', columna='...', decision='DROP', rol='')]` permite corregir la decisión automática sin editar la base. Para `KEEP`, usar la misma estructura y rol válido. Cada override requiere **evidencia, impacto y aprobación**. La advertencia final de que `TARGET` sigue siendo el ejemplo **no detiene necesariamente** el pipeline: detente tú antes de procesar el caso real.

**Responsabilidad:** el plan dice que integradora o DS crea la copia a las 15:30. Hellen comprueba rutas y campos, propone overrides y usa **la única configuración oficial**. No crear versiones paralelas.

# 6. `run_pipeline.py`: el orquestador por bloques

El archivo inspeccionado contiene:

```python
PASOS = ['ingesta','perfil','limpieza','llaves','features','seleccion','monitor']
```

| Bloque | Qué hace | Qué compruebas |
|---|---|---|
| `sys.dont_write_bytecode=True` | Evita archivos `__pycache__` | No ensuciar base |
| Detecta `--config` antes de `import config` | Inyecta config del evento | Ruta correcta |
| `--raw` | Origen alternativo | Autorización y ubicación |
| `--desde` | Ejecuta desde una etapa | Etapas anteriores ya generadas |
| `--solo` | Solo una etapa | Puede requerir artefactos previos |
| `--corte` | Sustituye corte temporal | Fecha acordada |
| `--sufijo` | Guarda tabla de otro corte | No sobrescribir actual |
| `OUT_DIR.mkdir` | Crea reportes | Permisos y espacio |
| `ingesta.ejecutar` | Bronze | Conteos/hojas |
| `perfil.ejecutar` | Perfil | Tipos, nulos, roles |
| `perfil.aplicar_manual` | Overrides | Cambios justificados |
| `limpieza.ejecutar` | Silver | Filas, sumas, conversiones |
| `llaves.ejecutar` | Grano/relaciones | Cardinalidad |
| `features.ejecutar` | Variables | Tiempo y agregación |
| `seleccion.ejecutar` | Embudo y alertas | Fugas y drift |
| `monitor.generar` | HTML | Interpretación |

**Error conocido de práctica:** `--solo ingesta` puede completar Bronze y después fallar si falta `perfil_columnas.csv`, porque el orquestador intenta leer ese reporte. Primera corrida: **pipeline completo**. Si falló después de ingesta, usar `--desde perfil` cuando Bronze esté íntegro.

# 7. Antes del concurso: preparación de laptop

1. Revisar reglamento y **autorización escrita** para código preparado previamente con asistencia de IA. Hacer privado un repo **no sustituye autorización**.
2. Instalar Git y Python recomendado por la guía (ideal 3.11 o 3.12; Python 3.14 puede dar problemas con algunas librerías).
3. Crear `.venv`, activar y ejecutar `preparar_offline.py` **desde la carpeta donde exista**; todas las dependencias deben indicar `OK`.
4. Mantener el repo fuera de OneDrive; espacio suficiente para raw, Parquet y temporales.
5. Conectar laptop a corriente; evitar suspensión durante corridas.
6. Aceptar invitación al repo oficial, configurar Git y rama.
7. Hacer simulacro **con datos sintéticos**, no con datos confidenciales en herramientas no autorizadas.
8. Confirmar horarios oficiales: el documento del equipo habla de cierre de `base_conocimiento/` a las 14:00 del viernes, caso 14:30, inicio 15:30 y cierre de entregas sábado 10:30. **Verificar cambios oficiales.**

# 8. Día del concurso: protocolo USB → Silver

## Paso 1. Recibir el USB e inventariar

```powershell
Get-Volume | Select-Object DriveLetter, FileSystemLabel, SizeRemaining
Get-ChildItem E:\ -Recurse -File | Select-Object FullName, Length, Extension
```

`E:` es un ejemplo; puede ser `F:`. No ejecutar `.exe` ni macros desconocidas. Revisar carpetas, ZIP, Excel con varias hojas, archivos por mes y diccionarios. Registrar nombre, formato, tamaño, hojas, llave probable, fechas y dudas.

## Paso 2. Copiar **solo si está permitido**

```powershell
# Desde la raíz del repo oficial
New-Item -ItemType Directory -Force .\data | Out-Null
Copy-Item 'E:\carpeta_del_reto\*' '.\data\' -Recurse -Force
Get-ChildItem .\data -Recurse -File | Select-Object FullName, Length
```

No copiar archivos ajenos al reto. No mover ni modificar el USB original. Si el USB trae una carpeta `caso/`, confirma si `RAW_DIR` recorre subcarpetas; si no, copiar el contenido a la ubicación esperada. Si hay poco espacio, avisar antes de empezar.

Para verificar copia exacta de un archivo:

```powershell
Get-FileHash 'E:\carpeta_del_reto\empresas.csv' -Algorithm SHA256
Get-FileHash '.\data\empresas.csv' -Algorithm SHA256
```

Hashes iguales implican mismos bytes. No publicar hashes o nombres sensibles si las reglas lo prohíben.

## Paso 3. Evitar subir datos

```powershell
git status --short --untracked-files=all
git check-ignore -v .\data\empresas.csv
```

Si los datos aparecen como archivos nuevos rastreables, **no hacer `git add .`**. Pedir revisión de `.gitignore` a integradora.

## Paso 4. Preparar configuración oficial

```powershell
# Solo si integradora/DS todavía no lo hizo:
New-Item -ItemType Directory -Force .\trabajo | Out-Null
Copy-Item .\base_conocimiento\plantilla\evento\config_evento.py .\trabajo\
Copy-Item .\base_conocimiento\plantilla\evento\exportar_submission.py .\trabajo\

Remove-Item Env:DATAFEST_PRUEBA -ErrorAction SilentlyContinue
notepad .\trabajo\config_evento.py
```

**Antes de ejecutar:** comprobar `RAW_DIR`, nombres reales de tabla/columna, `FECHA_CORTE`, `HORIZONTE_MESES`, `TARGET`, `CAPACIDAD`, y que el target de ejemplo no siga activo.

## Paso 5. Ejecutar pipeline

```powershell
python .\base_conocimiento\plantilla\run_pipeline.py --config .\trabajo\config_evento.py
```

No asumir que terminó bien porque mostró «Listo»: comprobar archivos, filas y reportes.

## Paso 6. Leer reportes

```powershell
Get-ChildItem "$HOME\datafest_trabajo\salidas"
Invoke-Item "$HOME\datafest_trabajo\salidas\monitor.html"
Import-Csv "$HOME\datafest_trabajo\salidas\perfil_columnas.csv" |
  Select-Object -First 15
```

Si cambias decisiones humanas:

```powershell
python .\base_conocimiento\plantilla\run_pipeline.py --config .\trabajo\config_evento.py --desde perfil
```

Segundo corte **solo si DS define una fecha histórica válida y existe horizonte observado**:

```powershell
python .\base_conocimiento\plantilla\run_pipeline.py --config .\trabajo\config_evento.py --desde features --corte 2025-01-01 --sufijo _t1
```

La fecha es **ilustrativa**. No inventar cortes.

## Paso 7. Entregar a Kath

Rutas Silver, grano por tabla, llaves, cardinalidad, nulos, duplicados, montos, fechas, variables bloqueadas y cambios manuales. **No unir 1:N o N:M sin agregar**.

# 9. Checklist de calidad: qué revisar siempre

| Dimensión | Prueba | Si falla |
|---|---|---|
| Completitud | Raw vs Bronze vs Silver | Revisar hojas, separadores, filtros |
| Unicidad | Filas, `COUNT DISTINCT`, duplicados | Determinar grano antes de borrar |
| Validez | Fechas y números parseados | Revisar formato y centinelas |
| Consistencia | Moneda, estado, códigos | Normalizar con diccionario |
| Integridad | Anti-join y cobertura | Investigar huérfanos |
| Temporalidad | Corte y disponibilidad real | Excluir/reconstruir fuga |
| Dinero | Conciliación de sumas | Separar causas y residual |
| Estabilidad | PSI por corte/segmento | Investigar drift |
| Trazabilidad | Bitácora y cambios | Documentar versión y responsable |

## 9.1 Consultas DuckDB útiles

**Conteo y llaves:**

```python
import duckdb
con = duckdb.connect()
ruta = r'C:\Users\TU_USUARIO\datafest_trabajo\work\silver\maestro_clientes.parquet'
print(con.execute('''
SELECT COUNT(*) AS filas,
       COUNT(*) FILTER (WHERE ruc_cliente IS NULL) AS nulos,
       COUNT(DISTINCT ruc_cliente) AS distintos
FROM read_parquet(?)
''', [ruta]).fetchdf().to_string(index=False))
```

**Duplicados exactos** (consulta conceptual con ruta real):

```sql
SELECT COUNT(*) - (SELECT COUNT(*) FROM
  (SELECT DISTINCT * FROM read_parquet('BRONZE.parquet')))
FROM read_parquet('BRONZE.parquet');
```

**Duplicados de negocio**:

```sql
SELECT ruc_emisor, nro_factura, COUNT(*) AS n
FROM read_parquet('BRONZE.parquet')
GROUP BY 1,2 HAVING COUNT(*) > 1;
```

**Cobertura de unión:**

```sql
SELECT COUNT(*) AS sin_perfil
FROM read_parquet('maestro.parquet') m
LEFT JOIN read_parquet('perfil.parquet') p
  ON m.ruc_cliente = p.cod_cliente
WHERE p.cod_cliente IS NULL;
```

**Fechas posteriores al corte:**

```sql
SELECT MIN(fecha_ultimo_contacto), MAX(fecha_ultimo_contacto),
       COUNT(*) FILTER (WHERE fecha_ultimo_contacto >= DATE '2025-07-01')
FROM read_parquet('perfil.parquet');
```

**Precaución:** fecha máxima anterior al corte **no prueba** que `total_operaciones_hist` fuera calculada antes. Hay que comprobar linaje, snapshot y fecha de disponibilidad.

## 9.2 Conciliación monetaria

Definir A = suma Bronze parseada; B = suma tras quitar duplicados exactos; C = suma de centinelas **entre filas únicas**; D = suma Silver. Calcular:

- `A-B`: importe eliminado por duplicados.
- `C`: importe anulado por centinelas después de deduplicar.
- `B-C-D`: **residual** a explicar.

Usar la **misma función de parseo** que el pipeline y valores completos, no notación científica. `DISTINCT` después de transformar columnas puede no equivaler a `DISTINCT` raw. No contar dos veces centinelas duplicados.

# 10. Estadística descriptiva para entender los datos

| Concepto | Ejemplo | Interpretación |
|---|---|---|
| Población | Todas las empresas elegibles | Universo de decisión |
| Muestra | 20,000 empresas observadas | ¿Representativa? |
| Media | 10,10,100 → 40 | Sensible a grandes montos |
| Mediana | 10,10,100 → 10 | Empresa típica |
| Percentil 90 | 90% tiene plazo ≤ P90 | Cola de pagos tardíos |
| Desviación estándar | Dispersión de montos | Volatilidad |
| IQR | Q3-Q1 | Dispersión robusta |
| Tasa de nulos | 300/1000=30% | Cobertura y posible señal |
| Tasa de duplicados | 80/1000=8% | Depende del grano |
| HHI | Suma de cuotas² | Concentración de pagadores |

**Ejemplo:** si la media de facturación es S/100,000 y mediana S/15,000, pocas empresas grandes dominan la suma. No concluir que «la empresa promedio vende S/100,000» sin aclarar asimetría.

# 11. Probabilidad y Bayes para banca

**Probabilidad condicional:** `P(A|B)=P(A∩B)/P(B)`.

Ejemplo: de 1,000 empresas, 100 compran factoring. De 200 con actividad alta, 60 compran:

- `P(compra)=100/1000=10%`.
- `P(compra|actividad alta)=60/200=30%`.
- **Lift** = 30%/10%=**3 veces**.

No demuestra que la actividad alta **cause** compra; puede estar asociada al tamaño de empresa.

**Bayes:** `P(B|A)=P(A|B)P(B)/P(A)`.

Ejemplo de alertas: fraude real 1%, sensibilidad 90%, especificidad 95%, 10,000 operaciones. Hay 100 fraudes: 90 alertas correctas; 9,900 operaciones legítimas: 495 falsas alertas. Precisión de alerta = 90/(90+495)=**15.4%**. Un detector «90% sensible» **no** significa que 90% de sus alertas sean fraude.

**Incertidumbre:** si 60/200 convierten (30%), error estándar binomial aproximado `sqrt(0.3×0.7/200)=3.24 puntos porcentuales`; intervalo normal 95% aproximado ≈ 23.6%–36.4%. No usar sin más si hay dependencia entre filas, selección sesgada o muy pocos casos.

**Sesgos:** selección (faltan ciertos clientes), supervivencia (solo activos), temporal (datos futuros), cobertura (fuente no incluye todo), confusión (una tercera variable explica la asociación). Correlación **no implica causalidad**.

# 12. Métricas de clasificación y su interpretación

| Métrica | Fórmula/idea | Pregunta de negocio |
|---|---|---|
| Precisión | TP/(TP+FP) | ¿Cuántos contactados convierten? |
| Recall | TP/(TP+FN) | ¿Qué porcentaje de compradores capturamos? |
| Especificidad | TN/(TN+FP) | ¿Cuántos negativos descartamos bien? |
| FPR | FP/(FP+TN) | ¿Cuántos negativos reciben alerta? |
| F1 | 2PR/(P+R) | ¿Equilibrio entre precisión y recall? |
| Accuracy | (TP+TN)/total | ¿Cuántas clases acertamos? Puede engañar |
| ROC-AUC | Ordenamiento positivo vs negativo | ¿Distingue mejor que azar? |
| Gini | `2×AUC−1` | Capacidad de separación |
| PR-AUC / AP | Resumen precisión-recall | Importante si positivos raros |
| Lift@k | Precisión@k / tasa base | ¿Mejora el top sobre azar? |
| Captura@k | Positivos en top k / positivos totales | ¿Qué parte de oportunidad capturo? |
| Brier | Media de `(p−y)²` | ¿Probabilidades calibradas? |
| Log loss | Penaliza probabilidades seguras erróneas | ¿Confianza adecuada? |

**Ejemplo con capacidad:** 1,000 empresas, 100 compradoras, solo 100 llamadas. Si el top 100 contiene 35 compradoras: tasa base 10%; precisión@100 35%; captura@100 35%; lift@100 **3.5x**. Un top aleatorio tendría 10 conversiones **esperadas**, frente a 35 observadas en el ejemplo. **Esto no demuestra incremento causal** por llamar; es evaluación predictiva.

**Desbalance:** si 100 de 10,000 compran (1%), predecir «nadie compra» da 99% accuracy y **0 recall**. Reportar PR-AUC y captura a capacidad.

**Gini vs calibración:** un score puede ordenar bien pero asignar 80% de probabilidad a clientes cuya tasa real es 20%. No multiplicar score sin calibrar por monto para calcular valor esperado.

# 13. PSI, IV, WOE, Spearman y fugas

**PSI:** `Σ (p_actual−p_referencia)×ln(p_actual/p_referencia)` por intervalos. En la plantilla >0.10 alerta y >0.25 revisión fuerte. **No prueba fuga ni obliga a DROP**. Ejemplo: proporción de saldos altos pasa de 10% a 35%: revisar cambio de cartera, moneda o fuente.

**WOE:** logaritmo del cociente de proporciones de no-eventos y eventos por intervalo (convención de signo debe mantenerse consistente). **IV:** suma de diferencias de proporciones multiplicadas por WOE; mide separación univariada. IV alto puede significar buena variable o fuga.

**Spearman:** correlación de rangos. `rho=0.95` entre saldo promedio y saldo máximo sugiere redundancia, pero no elimina automáticamente valor incremental.

**Gini individual muy alto:** revisar si columna incluye resultados posteriores. Ejemplo real del simulacro: `ops_ultimo_semestre` y `total_operaciones_hist` se copiaban «tal cual» y no había prueba de su ventana temporal. El Gini alto **solo activó la revisión**.

**Fuga temporal:** una variable debe existir en el momento de decidir, no solo tener una fecha nominal anterior. Una columna `fecha_pago_real` puede revelar el futuro; una fecha de vencimiento contractual conocida al corte puede ser legítima. Los encoders e imputadores se ajustan **solo con train**, nunca con validación/test.

**Validación temporal:** entrenar con corte anterior y evaluar con corte posterior, asegurando horizonte futuro completo y evitando que una misma entidad o su resultado filtre información entre particiones.

# 14. Banca y factoring: fundamentos

**Factoring:** el proveedor/emisor tiene una cuenta por cobrar de un pagador/deudor y puede obtener adelanto del factor/banco bajo condiciones contractuales. El banco analiza la factura, el pagador, el proveedor, la cesión y los riesgos.

- **Proveedor/emisor:** vende y emite factura.
- **Pagador/deudor:** debe pagar.
- **Factor:** financia/adquiere derechos según contrato.
- **Con recurso:** proveedor conserva determinadas responsabilidades por impago.
- **Sin recurso:** factor asume determinados riesgos contractuales; no significa «sin riesgo».
- **Monto nominal:** valor de factura.
- **Monto financiado:** adelanto, no necesariamente igual al nominal.
- **Plazo:** días hasta vencimiento o pago, especificar cuál.
- **Tasa de anticipo:** financiado / nominal elegible.
- **DSO:** días de cobro, requiere definición y datos apropiados.
- **Mora 30/60/90:** días de atraso respecto al vencimiento.
- **NPL:** cartera improductiva bajo definición bancaria/regulatoria.
- **HHI de pagadores:** concentración de exposición en pocos deudores.

## 14.1 Riesgos y señales

| Riesgo | Ejemplo | Señal posible | Qué harías |
|---|---|---|---|
| Crédito pagador | No paga factura | Mora, atrasos | Alertar y verificar límites |
| Crédito proveedor | Incumple obligaciones | Historial y estabilidad | Revisar elegibilidad |
| Fraude | Factura inexistente/duplicada | Claves y patrones anómalos | Verificación, no acusar |
| Operacional | Error de carga | Montos imposibles | Conciliar |
| Liquidez | No hay fondos para adelantar | Volumen/plazos | Coordinar tesorería |
| Concentración | 80% en un pagador | HHI alto | Diversificar/límites |
| FX | USD/PEN mezclados | Moneda y fechas | Tipo de cambio consistente |
| Legal/compliance | Cesión no válida | Estado/documentación | Revisión legal |
| Modelo | Drift o mala calibración | PSI/backtest/Brier | Monitorizar |

## 14.2 PD, LGD, EAD y pérdida esperada

`EL = PD × LGD × EAD` como modelo simplificado:

- **PD:** probabilidad de default en un horizonte.
- **LGD:** proporción perdida dado default.
- **EAD:** exposición cuando ocurre default.

Ejemplo: PD=4%, LGD=45%, EAD=S/100,000 → pérdida esperada **S/1,800**. No equivale automáticamente a provisión regulatoria. **Propensión a comprar factoring ≠ riesgo de impago**. Una empresa puede tener alta intención comercial y ser inelegible por riesgo.

# 15. Métricas y decisiones de negocio

No elegir clientes solo por Gini. Para una campaña, el valor esperado por contacto podría aproximarse como:

`EV ≈ P(convertir) × margen_neto_si_convierte − costo_contacto − costo_operativo − costo_riesgo`.

La definición exacta depende del caso. Un modelo puede maximizar conversiones y no maximizar margen. Los cupos por zona, capacidad total, exclusiones de riesgo y elegibilidad se aplican **después de entender qué optimiza el negocio**.

**Ejemplo:** rubro A: 1,000 empresas, conversión 20%, ticket S/40,000 → volumen potencial hipotético S/8 millones. Rubro B: 100 empresas, conversión 40%, ticket S/5,000 → S/200 mil. B tiene mejor **tasa**, A más **volumen**. Si A tiene concentración o mora elevada, la decisión puede cambiar. No mezclar tasa de adopción con rentabilidad ni con pérdida esperada.

**Métricas bancarias a diferenciar:** tasa de conversión (por contactados o elegibles), penetración (clientes con producto / elegibles), ticket (por operación o cliente), tasa de mora por clientes, tasa de mora ponderada por saldo, volumen nominal, monto financiado, margen, costo de fondeo, pérdida esperada, concentración por rubro/pagador/zona, cobertura de fuentes.

# 16. Escenarios: desde simples a complejos

| Si entregan... | Qué hacer | Archivo/configuración | Riesgo |
|---|---|---|---|
| 4 CSV o varios Excel | Ingestar y revisar conteos | Automático | Hojas omitidas |
| Excel con varias hojas | Confirmar tablas vs particiones | Ingesta | Doble conteo |
| CSV con `;`, tab o latin-1 | Verificar detección | Ingesta | 0 filas o texto corrupto |
| ZIP | Revisar extracción | Ingesta | Archivos faltantes |
| Una sola tabla | Confirmar grano/target | `ENTIDAD`, `TARGET` | Entidad equivocada |
| Encabezado en fila 3 | Adaptador autorizado | `ingesta.py` nuevo/derivado | Columnas falsas |
| Train y test separados | Unir de forma controlada | `UNIR_TABLAS`, `EVALUAR` | Fuga de test |
| Lista de clientes a puntuar | Definir evaluación | `EVALUAR` | IDs perdidos |
| Tabla empresa×mes×producto×saldo | Pivotar | `PIVOTAR` | Duplicados en pivote |
| Misma operación en 2 fuentes | Dedup de negocio | `DEDUP_EVENTOS` | Borrar eventos legítimos |
| Entidad autodetectada mal | Fijar entidad | `ENTIDAD` | Join multiplica |
| Eventos no detectados | Definir fechas/montos | `EVENTOS` | Features incompletas |
| Target ya como 0/1 | Usar columna | `TARGET` | Usar etiqueta como predictor |
| Target por evento futuro | Fecha y filtro | `TARGET` | Ventana incorrecta |
| USD y PEN | FX según caso | `TIPO_CAMBIO` | Suma sin convertir |
| No hay lead | Desactivar segmento | `SEGMENTO=None` | Inventar segmento |
| 2 fechas, emisión y pago | Distinguir contractual vs real | Features/validación | Fecha de pago futura |
| Snapshots actuales | Revisar fecha de disponibilidad | Auditoría temporal | Fuga |
| Datos por empresa y factura | Agregar antes de unir | Kath / `llaves` | N:M artificial |
| 0.4% de positivos | PR-AUC y captura@k | DS | Accuracy engañosa |
| Cupos por zona | Confirmar si % o absolutos | `CUPOS_ZONA` | Ranking inelegible |
| Se pide monto, no conversión | Modelo/target de monto | `TARGET`/DS | Optimizar métrica errónea |
| No hay fecha de corte | Preguntar y documentar | Nat/mentor | Backtest inventado |
| SQLite/DB | Adaptador y exportación permitida | Código nuevo | No soportado directamente |
| 8 GB y poca RAM | DuckDB/Parquet, temporales | Recursos | OOM/disco lleno |

**Regla de escalada:** primero observar → cambiar config → `DECISIONES_MANUAL` → SQL read-only → código nuevo autorizado fuera de base congelada → cambios profundos solo con pruebas y aprobación. Nunca modificar el pipeline base congelado para salir del paso.

# 17. Árbol general de decisión

```text
¿Los archivos están completos y está permitido copiarlos?
  NO → preguntar / inventariar / no improvisar
  SÍ
    ¿Target, corte y horizonte confirmados?
      NO → Nat/DS/mentor; no correr con ejemplo
      SÍ
        ¿Formato soportado?
          NO → adaptador nuevo probado y autorizado
          SÍ → ingesta → Bronze → perfil → Silver
              ¿Cambian filas/montos inesperadamente?
                SÍ → reconciliar antes de avanzar
                NO → validar llaves, joins y fechas
                    ¿Hay riesgo de fuga o N:M?
                      SÍ → bloquear feature y documentar
                      NO → entregar a Kath
                          → features → validación → modelo
                          → priorización bajo restricciones
```

# 18. Errores comunes y arreglos

| Error | Causa | Acción segura |
|---|---|---|
| `FileNotFoundError` | Ruta incorrecta | `pwd`, `RAW_DIR`, carpeta oficial |
| `config_evento` no encuentra `config.py` | No se copió a `trabajo/` | Copiar, no ejecutar desde `evento/` |
| Aviso `TARGET` de ejemplo | Config incompleta | Detener y definir target real |
| `DATAFEST_PRUEBA=1` | Simulacro activado | Quitar variable de entorno |
| `--solo ingesta` falla por perfil | Faltan reportes previos | Pipeline completo o `--desde perfil` |
| `UnicodeEncodeError` | Codificación consola | UTF-8 y `plataforma.consola_utf8()` |
| `PermissionError` | Excel abierto/OneDrive | Cerrar Excel, sacar repo de sincronización |
| `MemoryError` | pandas carga todo | DuckDB/Parquet, limitar memoria |
| Disco lleno | Temporales | Revisar `TMP_DIR`, liberar seguro |
| CSV con 0 filas | Encoding/separador | Verificar latin-1, bitácora |
| Fecha día/mes invertida | Formato distinto | Muestras inequívocas y parser probado |
| Montos 1000× | Unidades/decimal/FX | Comparar fuente y diccionario |
| Gran caída de suma | Duplicados/centinelas | Conciliación por etapas |
| JOIN multiplica filas | N:M | Agregar por entidad antes de unir |
| JOIN pierde empresas | Claves incompatibles | Normalizar IDs, anti-join |
| Gini demasiado alto | Fuga posible | Linaje, corte, backtest |
| PSI alto | Cambio de población | Comparar rubros, fechas y fuentes |
| `git status` muestra data | Exclusión incorrecta | No stage, avisar integradora |
| PR en conflicto | Config editada por varias | Responsable único, revisión |

# 19. Qué preguntar a la organización

1. ¿La unidad de predicción es empresa, factura, operación o cliente?
2. ¿Qué es un positivo y cuál es el horizonte exacto?
3. ¿Cuál es la fecha de corte y la fecha real de disponibilidad de cada fuente?
4. ¿Cuál es la métrica oficial de evaluación?
5. ¿Formato exacto del `submission.csv` (IDs, columnas, orden, tipos)?
6. ¿Se entregan train/test separados o lista de evaluación?
7. ¿Qué llaves unen fuentes y hay diccionario de variables?
8. ¿Qué representan los montos: nominal, financiado, saldo, margen o pérdida?
9. ¿Qué significan `999999`, `-1`, `ANULADA` y otros códigos?
10. ¿Los acumulados históricos están calculados al corte o a fecha actual?
11. ¿Qué restricciones comerciales, de riesgo, cupos o elegibilidad aplican?
12. ¿Se optimiza conversión, monto, beneficio o pérdida?
13. ¿Pueden copiar datos del USB y dónde deben almacenarlos?
14. ¿Qué reglas de IA, publicación, código previo y confidencialidad aplican?

**Si no hay respuesta:** registrar supuesto, responsable, fecha y riesgo. No presentarlo como hecho oficial.

# 20. Qué preguntar a Nat y Kath

**Nat:** ¿quién mantiene `trabajo/config_evento.py`?, ¿qué target/corte/capacidad están aprobados?, ¿qué hallazgos bloquean?, ¿dónde van notas y PR?, ¿cuándo entregamos Silver?, ¿qué restricciones oficiales cambiaron?

**Kath:** ¿cuál es el grano final?, ¿qué tabla maestra usarás?, ¿qué llaves y agregaciones necesitas?, ¿cómo evitarás multiplicar filas?, ¿qué columnas deben quedar por trazabilidad?, ¿qué variables temporales excluirás?, ¿cómo validarás sumas después de joins?

# 21. Prompts de estudio para Copilot **si está permitido**

> Durante el evento usar únicamente el asistente autorizado. No pegar datos, enunciados, secretos ni contenidos sensibles en servicios no autorizados. Estos prompts pueden utilizar **esquemas ficticios** durante la preparación.

- **USB:** «Enséñame a inventariar archivos CSV/XLSX con PowerShell sin modificarlos; incluye tamaños y hashes».
- **Perfil:** «Para columnas ficticias `ruc`, `fecha`, `monto`, ¿qué pruebas de nulos, tipos y centinelas aplicarías?».
- **Duplicados:** «Diferencia duplicados exactos, de clave comercial y versiones; dame SQL DuckDB read-only».
- **Dinero:** «Diseña una conciliación Bronze→dedup→centinelas→Silver con residual exacto y sin doble conteo».
- **Llaves:** «Explica 1:1, 1:N y N:M con empresas, facturas y saldos, y cómo evitar multiplicar montos».
- **Fuga:** «Dame preguntas de linaje para verificar si una variable histórica existía al corte».
- **Métricas:** «Con datos hipotéticos calcula Gini, precisión@k, captura@k, lift y calibración; interpreta diferencias».
- **Negocio:** «Convierte este hallazgo abstracto en evidencia, impacto, acción y limitación, sin inventar dinero».
- **Errores:** «Explica este traceback y propón diagnóstico mínimo sin modificar archivos».
- **Defensa:** «Hazme preguntas difíciles de DE1 y corrige mis respuestas con criterios de evidencia».

# 22. Preguntas del jurado y respuestas defendibles

**¿Por qué no borrar RUC repetidos?** Porque RUC identifica empresa, no factura; múltiples operaciones son legítimas. Primero determinamos el grano.

**¿Cómo garantizan que no hay fuga?** Definimos corte, verificamos disponibilidad de variables, filtramos eventos y evaluamos fuera de tiempo. No afirmamos garantía absoluta sin linaje.

**¿Por qué Gini alto no basta?** Ordena, pero no mide calibración, utilidad, capacidad comercial ni causalidad.

**¿Qué significa cobertura 100%?** Todas las entidades maestras encuentran contraparte. Con llaves únicas, el join es 1:1; no prueba que todos los valores sean correctos.

**¿Qué harías si el monto cae 55%?** Separar duplicados, centinelas, parseo y filtros; reconciliar con importes completos y documentar residual.

**¿Qué pasa si `999999` es legítimo?** No eliminarlo por su apariencia: contrastar documentación, distribución, fuente y efecto económico.

**¿Por qué DuckDB y Parquet?** Procesamiento eficiente, columnar, menor relectura de Excel y posibilidad de trabajar con archivos mayores que RAM.

**¿Y si el cliente más propenso es muy riesgoso?** Propensión comercial y riesgo crediticio son distintos; priorizar solo entre elegibles y bajo límites.

**¿Cómo demuestran más ventas?** Backtest muestra concentración de positivos, no causalidad. Para efecto incremental se requiere experimento controlado.

**¿Qué hizo Hellen?** Inventarié, ingestado, perfilé, limpié, validé llaves, montos y fechas, documenté riesgos y entregué Silver reproducible.

# 23. Cómo contar hallazgos al jurado

Usa cuatro frases:

1. **Evidencia:** «Encontramos X en tabla Y, período Z, sobre N registros».
2. **Interpretación:** «Esto puede inflar montos / perder empresas / filtrar el futuro».
3. **Acción:** «Verificamos con consulta A y corregimos o bloqueamos B».
4. **Límite:** «Queda pendiente validar semántica o disponibilidad; no afirmamos más de lo demostrado».

**Ejemplo del simulacro anterior:** «Identificamos 8,000 duplicados exactos en facturas. Su eliminación evita inflar operaciones y montos. Comparamos Bronze con Silver y comprobamos llaves. Los códigos de importe especial requieren confirmación de negocio».

# 24. Archivos que Hellen crea y entrega

## `AUDITORIA_DE1.md`

```markdown
# Auditoría DE1 — Hellen
## Caso, objetivo, corte y horizonte
## Inventario de fuentes
| Fuente | Formato | Filas Bronze | Filas Silver | Grano | Llave |
## Controles de calidad
| Prueba | Resultado | Evidencia | Estado |
## Conciliación monetaria
A=... B=... C=... D=... residual=...
## Fugas temporales y riesgos
| Variable | Evidencia | Riesgo | Acción | Responsable |
## Decisiones manuales
| Tabla | Columna | Antes | Después | Motivo | Aprobación |
## Handoff a Kath
- Rutas Silver, llaves, cardinalidad, ventanas, advertencias
```

## `INVENTARIO_FUENTES.md` / `BITACORA_FUENTES.md`

```markdown
| Archivo | Tamaño | Formato/hojas | Entidad | Fecha recepción | Observaciones |
```

## `HANDOFF_DE1_DE2.md`

```markdown
# Entrega DE1 → DE2
- Fecha de corte y target:
- Tabla maestra y llave:
- Rutas locales de Silver:
- Relaciones 1:1, 1:N, N:M:
- Campos monetarios y monedas:
- Variables bloqueadas por fuga:
- Reglas de limpieza aplicadas:
- Controles aprobados y pendientes:
```

**Destino:** acordar carpeta permitida con integradora. Antes del cierre puede haber `base_conocimiento/notas/` autorizado; después del cierre **no modificar la base**. Los Parquet Silver del concurso no se suben a Git; se entregan por mecanismo local autorizado.

## Git seguro

```powershell
git status
git switch -c hellen228/auditoria-de1  # solo si rama no existe
git add .\docs\AUDITORIA_DE1.md          # solo ruta permitida
git diff --cached --stat
git diff --cached
git commit -m 'docs: auditoria DE1'
git push -u origin hellen228/auditoria-de1
```

No usar `git add .` sin revisar. PR pequeño, revisión y fusión por integradora.

# 25. Entrenamiento progresivo

**Nivel 1 (básico):** identificar USB, explicar Raw/Bronze/Silver, leer config, ejecutar pipeline, contar filas y nulos, reconocer grano y crear informe.

**Nivel 2 (intermedio):** deduplicar con criterio, conciliar montos, anti-joins, fechas, `DECISIONES_MANUAL`, reportar riesgo y explicar Gini/lift.

**Nivel 3 (avanzado):** backtest temporal, drift por segmento, sesgo de cobertura, calibración, valor esperado, riesgo de crédito, cupos, robustez y defensa ante jurado.

**Ejercicio 1:** 20,000 filas maestro, 19,500 RUC distintos, 200 nulos. ¿Puedes decir que hay exactamente 500 duplicados? No: `COUNT DISTINCT` ignora nulos; hay que estudiar los grupos y el grano.

**Ejercicio 2:** 100 empresas, cinco facturas y tres saldos por empresa. Join directo produce hasta 1,500 filas artificiales. Solución: agregar cada tabla al grano empresa antes de unir.

**Ejercicio 3:** dos segmentos tienen igual Gini, pero prevalencias 1% y 30%. ¿Mismo umbral y misma conversión? No: precisión, calibración, costos y capacidad cambian.

**Ejercicio 4:** variable histórica tiene Gini 0.91 y fecha auxiliar máxima antes del corte. ¿Es segura? No necesariamente: falta fecha de cálculo del acumulado y disponibilidad real.

# 26. Glosario rápido

| Término | Significado |
|---|---|
| Raw | Datos recibidos intactos |
| Bronze | Copia estructurada fiel |
| Silver | Datos tipados y limpios |
| Tabla modelo | Una fila por entidad con features y target |
| Grano | Qué representa una fila |
| PK/FK | Llave única / referencia a otra tabla |
| Cardinalidad | 1:1, 1:N, N:M |
| Anti-join | Filas sin correspondencia |
| Null | Dato ausente, no equivale a cero |
| Centinela | Código especial que representa ausencia u otro estado |
| Linaje | Origen y transformaciones del dato |
| Snapshot | Foto de datos en un momento |
| Corte | Instante de decisión |
| Horizonte | Período futuro del objetivo |
| Leakage | Información que no existía al decidir |
| RFM | Recencia, frecuencia y monto |
| HHI | Concentración de contrapartes |
| PSI | Cambio de distribución |
| WOE / IV | Separación por intervalos entre clases |
| Spearman | Correlación de rangos |
| Gini | `2×ROC-AUC−1` |
| PR-AUC | Calidad de ranking precisión-recall |
| Lift | Tasa del top / tasa base |
| Captura@k | Positivos encontrados en top k / positivos totales |
| Calibración | Probabilidad predicha vs frecuencia real |
| PD / LGD / EAD | Probabilidad default / severidad / exposición |
| EL | Pérdida esperada |
| DSO | Días promedio de cobro |
| NPL | Cartera improductiva |
| Factoring | Financiamiento de cuentas por cobrar |
| FX | Tipo de cambio |
| PR | Pull request |
| `--config` | Config alternativa |
| `--desde` | Retomar desde etapa |
| `--solo` | Ejecutar etapa, puede necesitar artefactos |
| `--corte` | Otro corte temporal |
| `--sufijo` | Separar salidas de otro corte |

# 27. Checklist final de Hellen

- [ ] Plantilla y uso de IA autorizados por organización.
- [ ] `base_conocimiento/` integrada en `main` antes del cierre.
- [ ] USB recibido, inventariado y copiado donde esté permitido.
- [ ] Datos fuera de Git y originales intactos.
- [ ] `trabajo/config_evento.py` único y aprobado.
- [ ] `TARGET`, corte, horizonte y capacidad reales; sin ejemplos.
- [ ] Pipeline completo ejecutado y bitácora revisada.
- [ ] Bronze/Silver reconciliados en filas y dinero.
- [ ] Llaves nulas, duplicados y joins auditados.
- [ ] Variables posteriores al corte excluidas o bloqueadas.
- [ ] Overrides manuales justificados y registrados.
- [ ] Kath recibió rutas, grano, llaves y riesgos.
- [ ] Markdown entregado y PR revisado.
- [ ] Nada confidencial subido a Git ni IA externa.

**Guion de 40 segundos:** «Mi rol fue ingeniería de datos. Recibimos fuentes heterogéneas, las inventariamos y procesamos a Bronze y Silver con un pipeline reproducible. Auditamos duplicados, llaves, relaciones, sumas monetarias y disponibilidad temporal para evitar fuga. Registramos las decisiones dudosas y entregamos a modelado tablas al grano correcto y una bitácora de calidad. Así, el desempeño del modelo descansa sobre datos confiables y explicables».

---

# 28. Fuentes y límites

**Repositorio:** https://github.com/Lizzz7/plantilla_2026

**Archivos examinados:**

- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/README.md
- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/config.py
- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/run_pipeline.py
- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/docs/ESCENARIOS.md
- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/docs/GUIA_EJECUCION.md
- https://raw.githubusercontent.com/Lizzz7/plantilla_2026/main/plantilla_avanzada/docs/MODELADO.md

**Compartidos por Hellen en conversación:** `plantilla_avanzada/evento/config_evento.py` y `plantilla_avanzada/docs/PASOS_EVENTO.md`, además de resultados de auditoría del simulacro anterior.

**Limitaciones:** la explicación de módulos internos es funcional, no comentario literal de cada línea de sus fuentes. Las cifras educativas son hipotéticas; los valores de ejemplo de `config.py` no son parámetros oficiales. El reglamento, el enunciado y la documentación del banco prevalecen. Durante el concurso, seguir la prohibición de IA externa y de compartir datos/enunciados fuera de canales autorizados.
