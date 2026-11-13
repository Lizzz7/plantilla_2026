# Guía operativa de Hellen — DE1 · kit_datafest 3

**Objetivo:** recibir datos autorizados, limpiarlos, auditarlos y entregar resultados confiables a DE2 (Kath). Esta guía corresponde al nuevo kit y **reemplaza las instrucciones de ejecución de la plantilla avanzada anterior** para los scripts aquí tratados.

> **Reglas del evento:** el equipo indicó que enviará `base_conocimiento/` para revisión. Confirmar con organización qué se aprueba, qué se congela y cuáles son los entregables finales. No se deduce de esto que los datos, las salidas o `.gitignore` deban incluirse en la entrega. El `.gitignore` sí debe versionarse en la raíz del repositorio para proteger las carpetas locales.

## Inicio rápido — nuevo flujo de Hellen (PowerShell)

**Ejecuta un comando a la vez** y verifica que el paso terminó correctamente antes del siguiente. Este es el orden para tu kit nuevo; no necesitas correr `run_pipeline.py` de la plantilla anterior.

**1. Ubícate en el kit.** Abre PowerShell en la raíz del repositorio oficial:

```powershell
Set-Location '.\base_conocimiento\kit_datafest 3'
```

**2. Confirma los archivos y las rutas.**

```powershell
Get-ChildItem .\scripts; Get-Content .\ajustes.py
```

Debes ver `1_leer_limpiar.py`, `2_auditar.py`, `extra/limpieza_pandas.py`, y en `ajustes.py` las carpetas `data` y `salidas`. **Nat valida los parámetros del caso**; los valores actuales pueden ser solo ejemplos.

**3. Activa tu entorno** si ya lo tienes; si lo creaste dentro del kit:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si no existe, consulta la **Fase 1** más abajo para crearlo e instalar dependencias. Antes de ejecutar el script principal, prepara la importación de `ajustes.py`:

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

**4. Coloca los datos autorizados directamente en `data/`.** No dentro de otra subcarpeta: el script principal no busca recursivamente. Verifica:

```powershell
Get-ChildItem .\data -File
```

**5. Ejecuta limpieza principal:**

```powershell
python .\scripts\1_leer_limpiar.py
```

**6. Comprueba que se generaron Parquet:**

```powershell
Get-ChildItem .\salidas\limpio -Filter '*.parquet'
```

**7. Ejecuta tu auditoría:**

```powershell
python .\scripts\2_auditar.py
```

**8. Lee las alertas y el resumen:**

```powershell
Get-Content .\salidas\auditoria\RESUMEN_DE1.md -Encoding UTF8
```

**9. Entrega a Kath** las rutas de `salidas/limpio/` y `salidas/auditoria/`, junto con alertas relevantes, llaves, fechas y decisiones pendientes. No hagas commit de los Parquet ni de datos del USB.

**10. Si falla la limpieza**, primero diagnostica sin reemplazar nada:

```powershell
python .\scripts\extra\limpieza_pandas.py solo_diagnostico
```

Después consulta la **Fase 6** para comparar salidas y decidir si usar el plan B. **No ejecutes `reemplazar` de inmediato**.

### Comprobación de `.gitignore` (desde la raíz del repositorio)

Regresa a la raíz:

```powershell
Set-Location '..\..'
```

Confirma que `.gitignore` está **aquí** y que ignora las carpetas `base_conocimiento/kit_datafest 3/data/` y `base_conocimiento/kit_datafest 3/salidas/`:

```powershell
git check-ignore -v 'base_conocimiento/kit_datafest 3/data/ejemplo.csv'
```

```powershell
git status --short --untracked-files=all
```

Si `git status` muestra archivos sensibles o resultados, **no hagas `git add`** hasta corregirlo. El `.gitignore` debe versionarse; los datos y salidas no. Si los datos ya fueron rastreados, `.gitignore` por sí solo no los retira del índice ni del historial.

### Mapa de decisiones

| Situación | Qué haces | Resultado esperado |
|---|---|---|
| Primer día con CSV/XLSX | Paso 1 → Paso 2 | `salidas/limpio/` y auditoría |
| `ModuleNotFoundError: ajustes` | Ejecutar desde el kit y definir `PYTHONPATH` | Import correcto |
| No existe `data/` | Confirmar carpeta del USB y permisos | Archivos visibles |
| No aparece Parquet | Revisar error de ingesta, formato y extensión | No auditar salida vacía |
| Fechas o montos mal tipados | Diagnóstico pandas, revisar valores | Corrección justificada |
| Excel con varias hojas distintas | No apilar sin confirmar semántica | Tablas no mezcladas |
| Alertas en `relaciones.csv` | Confirmar llaves y cobertura con Kath | Handoff documentado |
| Fechas posteriores al corte | Distinguir target futuro de features | Sin fuga temporal |
| Quieres subir a Git | Comprobar `.gitignore` y `git status` | Solo código/documentación permitidos |

---

## 1. Estructura acordada

```text
REPOSITORIO_OFICIAL/
├── .gitignore                            # versionar en Git, no contiene datos
└── base_conocimiento/
    └── kit_datafest 3/
        ├── ajustes.py                    # Nat; valores de ejemplo hasta conocer caso
        ├── data/                         # datos USB, NO versionar
        ├── salidas/                      # resultados, NO versionar
        │   ├── limpio/                   # parquet para Kath
        │   ├── limpio_pandas/            # alternativa que no reemplaza
        │   └── auditoria/                # reportes DE1
        ├── scripts/
        │   ├── 1_leer_limpiar.py         # Hellen; script original
        │   ├── 2_auditar.py              # Hellen; nuevo script de control
        │   └── extra/
        │       └── limpieza_pandas.py    # Hellen; alternativa
        └── GUIA_HELLEN_DE1.md            # este documento
```

**Cuidado con rutas:** el script original `1_leer_limpiar.py` define `DATOS = Path(A.CARPETA_DATOS)` y `LIMPIO = Path(A.CARPETA_SALIDAS)/"limpio"`: depende del **directorio de ejecución**. Para no cambiar su código, ejecútalo desde `kit_datafest 3/`. En cambio `limpieza_pandas.py` y el nuevo `2_auditar.py` calculan las rutas desde su propia ubicación.

## 2. Qué hace cada archivo y qué puedes cambiar

| Archivo | Acción | ¿Cambiar durante el caso? |
|---|---|---|
| `ajustes.py` | Configura `data`, `salidas`, `CORTE`, `HORIZONTE`, `EMPRESAS`, `ID`, `EVENTOS`, `TARGET_TABLA`, `TARGET_FILTRO`, `FUERA`, `CAPACIDAD`, `CUPOS`, `ENTREGA` | **Nat** coordina cambios. Hellen verifica nombres y significado. |
| `1_leer_limpiar.py` | Lee CSV/XLSX, normaliza nombres, infiere tipos, convierte, aplica `DISTINCT`, guarda Parquet y gráfico | Sí, si una entrada no es soportada, pero con prueba y autorización. |
| `extra/limpieza_pandas.py` | Plan B, lectura de más formatos, diagnóstico y `FORZAR_TIPO` | Sí: override por columna y validación; no sobrescribir sin comparar. |
| `2_auditar.py` | Solo lee Parquet, opcionalmente cuenta filas raw, revisa calidad y genera reportes | Sí: agregar comprobaciones read-only justificadas. |
| `.gitignore` | Excluye datos/salidas y archivos temporales de nuevos commits | Sí, en la **raíz del repo**, revisar con integradora. |

### Variables de `ajustes.py` que debes entender

- `CARPETA_DATOS="data"`, `CARPETA_SALIDAS="salidas"`: rutas relativas al kit.
- `CORTE`: fecha de decisión. Variables históricas deben estar disponibles antes de esta fecha.
- `CORTE_ANTERIOR`: corte para construir un ejemplo histórico, si hay historia suficiente.
- `HORIZONTE`: meses futuros en que se observa el target.
- `HISTORIA`: meses pasados de eventos para variables.
- `EMPRESAS` y `ID`: tabla maestra y llave. Debe haber una fila por entidad si así lo define el caso.
- `EVENTOS`: tuplas `(alias, tabla, id, fecha, monto)`. Cada tabla puede tener varias filas por empresa.
- `TARGET_TABLA` y `TARGET_FILTRO`: definición de evento objetivo; **no se infiere de un nombre**.
- `FUERA`: columnas excluidas del modelado, **no borrarlas automáticamente de Silver**.
- `CAPACIDAD`, `CUPOS`, `ENTREGA`: restricciones y formato de salida, normalmente coordinados con Nat/DS.

**Todos los nombres de tablas y fechas actuales son ejemplos**; no ejecutar el caso real sin que Nat los adapte.

## 3. Recepción de USB: paso a paso

1. Confirmar autorización para copiar y procesar datos y qué unidad es el USB. No ejecutar programas ni macros del USB.
2. Desde la **raíz del repo oficial**, identificar la unidad: `Get-Volume | Select-Object DriveLetter,FileSystemLabel,SizeRemaining`.
3. Ver archivos: `Get-ChildItem E:\ -Recurse -File | Select-Object FullName,Length` (cambiar `E:` por la unidad real).
4. Copiar **solo la carpeta autorizada del reto** a `base_conocimiento/kit_datafest 3/data/`. Conservar originales; no sobrescribir sin registrar.
5. Revisar nombres, hojas Excel, formatos, tamaños, unidades monetarias y diccionario. Comparar hashes SHA256 si es posible.
6. Verificar `.gitignore` **antes de `git add`**.

Ejemplo desde la raíz del repositorio (solo si la organización autoriza la copia y el USB contiene exclusivamente datos del reto):

```powershell
New-Item -ItemType Directory -Force "./base_conocimiento/kit_datafest 3/data" | Out-Null
Copy-Item "E:\caso\*" "./base_conocimiento/kit_datafest 3/data/" -Recurse -Force
Get-ChildItem "./base_conocimiento/kit_datafest 3/data" -Recurse -File
```

## 4. Ejecutar tus tres scripts

Desde la raíz del repositorio oficial:

```powershell
cd "./base_conocimiento/kit_datafest 3"
python "./scripts/1_leer_limpiar.py"
python "./scripts/2_auditar.py"
```

**Si hay errores de tipos o formatos**, usar primero diagnóstico pandas (sin modificar los Parquet principales):

```powershell
python "./scripts/extra/limpieza_pandas.py" solo_diagnostico
python "./scripts/extra/limpieza_pandas.py"
```

El segundo escribe en `salidas/limpio_pandas/`; comparar con `salidas/limpio/`. **Solo si el equipo aprueba el reemplazo**:

```powershell
python "./scripts/extra/limpieza_pandas.py" reemplazar
python "./scripts/2_auditar.py"
```

Si `python` no encuentra dependencias: instalar según requirements autorizados, p. ej. `duckdb`, `pandas`, `matplotlib`, `openpyxl`, `pyarrow`; no instalar indiscriminadamente desde Internet si está restringido.

### Opción rápida si solo quieres auditar Parquet

```powershell
python "./scripts/2_auditar.py" --sin-crudos
```

Esto omite el conteo de filas de CSV/Excel originales (más rápido); los reportes mostrarán `N/D` para esas cifras.

## 4A. Tutorial de ejecución COMPLETO (Windows / PowerShell)

**Trabaja con un comando por vez y revisa su salida antes de continuar.** Las rutas siguientes asumen que el repositorio oficial está clonado y que el kit existe en `base_conocimiento/kit_datafest 3/`. Las fechas y tablas de `ajustes.py` son de ejemplo: Nat debe confirmarlas para el caso real. Este tutorial no sustituye las reglas oficiales de aprobación de la base, protección de datos ni herramientas autorizadas.

### Fase 0 — Preparación de carpetas y archivos

Estructura mínima:

```text
REPO/
├── .gitignore
└── base_conocimiento/
    └── kit_datafest 3/
        ├── ajustes.py
        ├── data/                      # entradas locales, ignoradas por Git
        ├── salidas/                   # resultados locales, ignorados por Git
        ├── scripts/
        │   ├── 1_leer_limpiar.py
        │   ├── 2_auditar.py
        │   └── extra/limpieza_pandas.py
        └── GUIA_HELLEN_DE1.md
```

En PowerShell, desde la **raíz del repositorio**, primero verifica:

```powershell
Get-Location
Get-ChildItem '.\base_conocimiento\kit_datafest 3\scripts'
```

Confirma que aparecen `1_leer_limpiar.py` y `2_auditar.py`. Si falta el segundo, cópialo a esa carpeta. Después entra al kit:

```powershell
Set-Location '.\base_conocimiento\kit_datafest 3'
Get-Location
Get-Content '.\ajustes.py' -Encoding UTF8
```

Comprueba `CARPETA_DATOS='data'`, `CARPETA_SALIDAS='salidas'`, tabla maestra, llave, eventos, corte y target. **No modifiques por tu cuenta las decisiones de negocio de Nat.**

### Fase 1 — Entorno y dependencias

Si el equipo ya creó un entorno virtual, actívalo desde su ruta real. Si aún no existe, un ejemplo **desde la raíz del kit** es:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Instala preferentemente el `requirements.txt` autorizado del equipo. Si no existe, estos son los paquetes que importan los tres scripts (solo instalar si las reglas permiten hacerlo):

```powershell
python -m pip install duckdb pandas matplotlib openpyxl pyarrow numpy
```

Comprueba imports:

```powershell
python -c "import duckdb,pandas,matplotlib,openpyxl,pyarrow,numpy; print('Dependencias OK')"
```

**Detalle importante descubierto al revisar el código:** `1_leer_limpiar.py` hace `import ajustes as A`, pero no agrega la carpeta padre de `scripts/` al `sys.path`. Ejecutarlo directamente como archivo puede dar `ModuleNotFoundError: No module named 'ajustes'`. Sin editar el script, desde la raíz del kit, añade el kit al `PYTHONPATH` **solo en esta sesión de PowerShell**:

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

Luego ejecuta los scripts desde el kit. Otra solución permanente, **solo si el equipo autoriza cambiar el código**, es añadir antes de `import ajustes as A`:

```python
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

La segunda solución no cambia la ubicación de `data/` del script principal; **sigue siendo obligatorio ejecutarlo desde la raíz del kit**.

### Fase 2 — Recepción del USB y verificación de fuentes

Con permiso de la organización, identifica la letra real del USB (por ejemplo `E:`):

```powershell
Get-Volume | Select-Object DriveLetter,FileSystemLabel,SizeRemaining
Get-ChildItem 'E:\' -Recurse -File | Select-Object FullName,Length,Extension
```

Si el reto está en `E:\caso\` y solo esa carpeta contiene los datos autorizados:

```powershell
New-Item -ItemType Directory -Force '.\data' | Out-Null
Copy-Item 'E:\caso\*' '.\data\' -Recurse -Force
Get-ChildItem '.\data' -Recurse -File | Select-Object FullName,Length
```

**No ejecutar programas ni macros del USB.** Si hay subcarpetas, recuerda que `1_leer_limpiar.py` utiliza `DATOS.iterdir()` y solo procesa **archivos directamente dentro de `data/`**; no recorre subcarpetas. Además, solo admite extensiones exactas `.csv` y `.xlsx` (en minúscula). No mezcles hojas Excel de entidades diferentes: el script las concatena.

Para verificar una copia concreta:

```powershell
Get-FileHash 'E:\caso\empresas.csv' -Algorithm SHA256
Get-FileHash '.\data\empresas.csv' -Algorithm SHA256
```

Si los hashes coinciden, la copia es idéntica. Los nombres son ilustrativos: reemplázalos por los reales.

### Fase 3 — Proteger datos con Git antes de cualquier commit

Desde el kit, vuelve a la **raíz del repositorio** con:

```powershell
Set-Location '..\..'
Get-Location
```

Comprueba que `.gitignore` está aquí, no dentro del kit, y contiene:

```gitignore
/base_conocimiento/kit_datafest 3/data/
/base_conocimiento/kit_datafest 3/salidas/
**/__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ipynb_checkpoints/
*.tmp
```

Verifica reglas **con un archivo existente** o una ruta de prueba:

```powershell
git check-ignore -v 'base_conocimiento/kit_datafest 3/data/empresas.csv'
git check-ignore -v 'base_conocimiento/kit_datafest 3/salidas/limpio/empresas.parquet'
git status --short --untracked-files=all
```

Si `git check-ignore` no muestra una regla, revisa la ubicación de `.gitignore`. Si datos ya estaban rastreados, ignorarlos no los elimina del índice ni del historial: informa a Nat. **No hagas `git add .` sin inspeccionar lo que se agregará.**

### Fase 4 — Limpieza principal

Regresa al kit:

```powershell
Set-Location '.\base_conocimiento\kit_datafest 3'
$env:PYTHONPATH = (Get-Location).Path
python '.\scripts\1_leer_limpiar.py'
```

Qué debe pasar: por cada archivo `.csv`/`.xlsx` directamente en `data/`, el script imprime `filas originales -> filas limpias`, tipos detectados y guarda `salidas/limpio/<nombre>.parquet`; además crea `salidas/1_filas.png`.

Comprueba salidas:

```powershell
Get-ChildItem '.\salidas\limpio' -Filter '*.parquet' | Select-Object Name,Length
Test-Path '.\salidas\1_filas.png'
```

**No concluyas que la diferencia de filas son duplicados originales**: el `SELECT DISTINCT` se aplica después de normalizar y convertir tipos. Las diferencias pueden incluir colapsos creados por transformación.

### Fase 5 — Auditoría DE1 (tu segundo paso obligatorio)

```powershell
python '.\scripts\2_auditar.py'
```

Si los crudos son enormes y quieres un control rápido sin volver a contarlos:

```powershell
python '.\scripts\2_auditar.py' --sin-crudos
```

La auditoría crea `salidas/auditoria/` con `tablas.csv`, `columnas.csv`, `llaves.csv`, `fechas.csv`, `montos.csv`, `relaciones.csv`, `alertas.csv` y `RESUMEN_DE1.md`. Comprueba:

```powershell
Get-ChildItem '.\salidas\auditoria'
Get-Content '.\salidas\auditoria\RESUMEN_DE1.md' -Encoding UTF8
Import-Csv '.\salidas\auditoria\alertas.csv' | Format-Table -AutoSize
```

**Prioridad de interpretación:** 1) tabla maestra presente; 2) llave maestra no nula y única; 3) tipos de fechas/montos; 4) diferencias de filas; 5) cobertura de eventos; 6) alertas temporales. Los eventos posteriores al corte pueden servir de **target**, pero no como features históricas.

### Fase 6 — Si la limpieza principal falla o interpreta mal una columna

Primero ejecuta **solo diagnóstico** (no reemplaza los Parquet):

```powershell
python '.\scripts\extra\limpieza_pandas.py' solo_diagnostico
```

Lee `salidas/diagnostico_columnas.csv`. Si identificas un tipo incorrecto, puedes proponer un `FORZAR_TIPO` **en el script de pandas** después de confirmar el significado real de la columna. Por ejemplo:

```python
FORZAR_TIPO = {
    'maestro_clientes.ventas_anuales': 'num',
    'facturas_electronicas.fecha_pago': 'fecha',
}
```

Para generar una salida alternativa **sin sobrescribir la principal**:

```powershell
python '.\scripts\extra\limpieza_pandas.py'
Get-ChildItem '.\salidas\limpio_pandas' -Filter '*.parquet'
```

Compara conteos, nulos, llaves y montos antes de aprobar cambios. **Solo si Kath/Nat confirman** que la salida alternativa debe sustituir a la principal:

```powershell
python '.\scripts\extra\limpieza_pandas.py' reemplazar
python '.\scripts\2_auditar.py'
```

**Advertencia:** `limpieza_pandas.py` puede saltarse líneas CSV defectuosas con `on_bad_lines='warn'`; revisa avisos y reconcilia conteos. Tampoco es idéntica a DuckDB: difieren reglas de fechas, centinelas y normalización.

### Fase 7 — Entrega a Kath y cierre

Entrega **por el canal local autorizado**: ubicación de `salidas/limpio/*.parquet`, reporte `RESUMEN_DE1.md`, `alertas.csv`, llaves y relaciones, decisiones de limpieza y problemas abiertos. No subir datos ni reportes confidenciales al repositorio si están excluidos.

Mensaje modelo:

> Kath, terminé la limpieza y auditoría. Los Parquet están en `kit_datafest 3/salidas/limpio/`. Revisé llaves, fechas, montos, nulos y relaciones. Las alertas y limitaciones están en `salidas/auditoria/RESUMEN_DE1.md`. Antes de hacer joins, confirma el grano por tabla y revisa las alertas críticas.

Desde la **raíz del repositorio**, antes de cualquier commit autorizado:

```powershell
git status --short --untracked-files=all
git add '.gitignore' 'base_conocimiento/kit_datafest 3/scripts/2_auditar.py' 'base_conocimiento/kit_datafest 3/GUIA_HELLEN_DE1.md'
git diff --cached --stat
git diff --cached
```

No ejecutes `git commit` ni `git push` hasta que Nat confirme reglas, permisos, rama y cierre de la base. Si ya pasó el plazo de congelación, no modifiques ni subas `base_conocimiento/` sin autorización expresa.

### Resumen del flujo normal (sin incidencias)

```powershell
# Estando en la raíz del repositorio:
Set-Location '.\base_conocimiento\kit_datafest 3'
$env:PYTHONPATH = (Get-Location).Path
Get-ChildItem '.\data' -File
python '.\scripts\1_leer_limpiar.py'
python '.\scripts\2_auditar.py'
Get-Content '.\salidas\auditoria\RESUMEN_DE1.md' -Encoding UTF8
```

**No ejecutes todo a ciegas:** revisa cada salida, especialmente si el USB contiene tablas nuevas o el caso cambió.

---

## 5. Qué genera `2_auditar.py`

Todo se escribe bajo `salidas/auditoria/`:

| Archivo | Para qué sirve | Qué decir a Kath |
|---|---|---|
| `tablas.csv` | Filas raw vs limpias, diferencia y columnas | «La diferencia necesita explicación; no son necesariamente duplicados exactos». |
| `columnas.csv` | Tipo, nulos, porcentaje de nulos, valores distintos | «Estas columnas necesitan revisión de tipo/ausencia». |
| `llaves.csv` | Nulos, distintos, repeticiones no nulas por llave | «La llave maestra debe ser única; en eventos puede repetirse». |
| `fechas.csv` | Fechas mínimas/máximas y eventos desde el corte | «Los eventos futuros pueden ser target, pero no features». |
| `montos.csv` | Suma Silver, nulos, negativos y ceros | «Falta conciliar contra crudo antes de afirmar impacto monetario». |
| `relaciones.csv` | Cobertura de IDs de eventos en la maestra | «Esta fuente tiene X% de cobertura; cuidado con los huérfanos». |
| `alertas.csv` | Avisos, revisiones y errores críticos | «Priorizamos lo crítico antes del modelado». |
| `RESUMEN_DE1.md` | Informe legible de resultados y limitaciones | «Aquí están los hallazgos y pendientes». |

**No se modifica ningún Parquet**; los CSV y el resumen se regeneran cada vez que corres la auditoría. Si necesitas conservar comparaciones, copia los reportes a una ubicación local autorizada con una etiqueta de corrida.

## 6. Interpretación correcta de alertas

- **CRITICO:** falta tabla o llave esperada, llave maestra no única, tabla sin filas, corte inválido. Investigar antes de entregar.
- **REVISAR:** filas reducidas, llaves nulas, montos negativos, IDs sin maestro, columnas nulas. Requiere explicación; no necesariamente error.
- **AVISO:** constante o eventos posteriores al corte. Puede ser normal según el caso.
- **Conteo raw vs Silver:** no prueba duplicados exactos, porque `1_leer_limpiar.py` transforma antes de aplicar `DISTINCT`.
- **Suma Silver:** no es conciliación monetaria con Raw. Para conciliación completa, comparar sumas raw parseadas, deduplicación, centinelas, moneda y residual por etapa.
- **Cobertura:** compara IDs de eventos contra la maestra; no prueba que el join de varias tablas sea 1:1.
- **Fechas:** solo revisa las columnas de fecha definidas en `EVENTOS`. No audita automáticamente toda posible fuga de columnas derivadas.

## 7. Escenarios y cambios posibles

| Situación | Qué haces | Qué no haces |
|---|---|---|
| Llegan nuevos CSV/XLSX | Copias a `data/`, verificas tablas y ajustas `EVENTOS` con Nat | No asumir que toda hoja Excel es la misma tabla |
| Archivo JSON/Parquet | Pruebas plan B pandas; documentas si hay que adaptar el principal | No afirmar que DuckDB principal lo soporta: solo lee `.csv`/`.xlsx` |
| Una columna numérica queda como texto | Diagnóstico y `FORZAR_TIPO` en pandas | No forzar sin revisar valores no convertibles |
| `999999` aparece en montos | Confirmar si es centinela o monto legítimo | No eliminarlo por intuición |
| `fecha_pago` queda como texto | Revisar parser y tipo; probar en muestra | No asumir que el detector DuckDB reconoce `fecha_` |
| RUC se repite en eventos | Esperado para relaciones 1:N | No borrar todas las repeticiones por RUC |
| Hay operaciones después de `CORTE` | Distinguir target futuro de feature histórica | No etiquetar toda fecha futura como error |
| Caen muchas filas | Comparar raw/limpio y transformaciones | No decir «eran duplicados exactos» sin evidencia |
| Hay cupos o capacidad | Informar a Nat/DS; validar que `ajustes.py` refleje el caso | No cambiar la selección final desde DE1 |
| Faltan recursos | Ejecutar auditoría `--sin-crudos`, considerar optimizaciones | No cargar archivos enormes en pandas sin medir RAM |

## 8. `.gitignore`: archivo y procedimiento

Colocar el archivo `.gitignore` proporcionado **en la raíz del repositorio**, al mismo nivel que `base_conocimiento/`. Contiene:

```gitignore
/base_conocimiento/kit_datafest 3/data/
/base_conocimiento/kit_datafest 3/salidas/
**/__pycache__/
*.py[cod]
.venv/
venv/
.pytest_cache/
.ipynb_checkpoints/
*.tmp
```

Desde la raíz del repositorio, probar con una ruta real (sin necesidad de subir datos):

```powershell
git check-ignore -v "base_conocimiento/kit_datafest 3/data/archivo.csv"
git check-ignore -v "base_conocimiento/kit_datafest 3/salidas/limpio/tabla.parquet"
git status --short --untracked-files=all
```

**Lo esperado:** Git ignora `data/` y `salidas/`; sí permite versionar `.gitignore`, `ajustes.py`, scripts y `GUIA_HELLEN_DE1.md` si la organización lo autoriza. Si los datos ya estaban rastreados, `.gitignore` **no los desrastrea**: avisar a integradora para `git rm --cached` y revisar el historial por posible exposición. No usar `git add .` sin revisar. No subir archivos sensibles, reportes con información del reto o datos del USB.

## 9. Qué entregas tú a Kath

- **Parquet limpios:** ubicación local `salidas/limpio/` (no subirlos a Git si están prohibidos).
- **`RESUMEN_DE1.md` y `alertas.csv`:** revisar localmente; si contienen información confidencial, no versionarlos.
- **Lista de tablas, llaves, fechas, montos y relaciones:** con resultados concretos.
- **Pendientes y decisiones:** tabla/columna, evidencia, impacto, acción propuesta, aprobación y responsable.

Ejemplo de comunicación: «Kath, ya tienes `salidas/limpio/`. La tabla maestra tiene X filas, la llave presenta Y problemas y la cobertura de eventos es Z%. Hay W alertas de fechas que deben separarse entre target y features. No hice un JOIN de eventos porque puede multiplicar filas».

## 10. Preguntas para Nat, organizador y Copilot autorizado

**A Nat:** ¿Confirmamos `CORTE`, `HORIZONTE`, `EMPRESAS`, `ID`, `EVENTOS` y el significado de `TARGET_FILTRO`? ¿Quién aprueba cambios de tipos y centinelas? ¿Dónde entregamos los reportes sin subir datos?

**Al organizador:** ¿Solo se aprueba `base_conocimiento/` o también hay entregas posteriores? ¿Podemos añadir scripts de auditoría? ¿Se permite copiar USB a disco local? ¿Hay diccionario de códigos, fechas de disponibilidad y moneda? ¿Qué IA está autorizada?

**A Copilot, si está autorizado:** «Revisa este error de lectura usando solo esquema ficticio; sugiere prueba read-only». «Explícame cómo detectar llaves N:M sin multiplicar montos». «Propón pruebas de conciliación para centinelas y duplicados sin borrar registros». «Ayúdame a traducir una alerta de calidad a evidencia, impacto, acción y limitación». No compartir datos reales ni enunciado con herramientas no autorizadas.

## 11. Errores frecuentes

| Síntoma | Posible causa | Acción |
|---|---|---|
| `FileNotFoundError: data` | Corriste `1_leer_limpiar.py` desde otra carpeta | `cd` a `kit_datafest 3/` |
| `ModuleNotFoundError: ajustes` | Script fuera de estructura esperada | Mantener scripts dentro de `scripts/` y `ajustes.py` en raíz del kit; para principal, ejecutar desde kit |
| `No hay Parquet` | Limpieza no ejecutada o ruta errónea | Revisar `salidas/limpio/` |
| Excel mezcla hojas | Hojas de distintas entidades apiladas | Separarlas antes de limpiar, según esquema |
| Gráfico no se genera | Sin tablas compatibles o carpeta salida | Revisar CSV/XLSX y permisos |
| `--sin-crudos` deja `N/D` | Se omitió el conteo raw | Es esperado |
| Tabla maestra ausente | `EMPRESAS` desactualizado | Nat corrige `ajustes.py` |
| Cobertura baja | IDs inconsistentes o maestro incompleto | Revisar normalización y universo |
| `git status` muestra datos | Regla `.gitignore` incorrecta o ya rastreados | Detener commit y revisar |

## 12. Guion de defensa ante jurado

«Mi responsabilidad como DE1 fue recibir los archivos autorizados, verificar su estructura y producir tablas limpias en Parquet. Luego ejecuté controles independientes de nulos, tipos, llaves, relaciones, fechas y montos. Separé alertas críticas de situaciones normales —por ejemplo, múltiples facturas por empresa— y comuniqué las limitaciones antes de que DE2 construyera variables. Evitamos subir datos a Git y documentamos las transformaciones para que el análisis sea reproducible».

**Nota:** este guion describe lo que **deberías ejecutar y verificar**; adáptalo a las tareas efectivamente realizadas y no atribuyas controles que no corriste.
