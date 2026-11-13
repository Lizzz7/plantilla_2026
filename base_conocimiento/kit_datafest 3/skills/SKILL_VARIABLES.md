# Skill para Copilot: ideas de variables de factoring

**Qué hace:** propone variables nuevas a partir de los campos disponibles, con su fórmula, su razón de negocio y su riesgo de fuga, y ayuda a implementar las elegidas.
**Cuándo:** después de tener una primera entrega válida con las variables que ya genera `pipeline/features.py`. No antes.
**Quién:** una data engineer y una data scientist.

## Cómo usarla (humanas)

1. Chat nuevo de Copilot.
2. Escribir: `#file:base_conocimiento/plantilla/docs/SKILL_VARIABLES.md sigue esta guía` y agregar:
   - `#file:base_conocimiento/plantilla/pipeline/features.py` (para que no repita lo que ya existe),
   - el diccionario de campos (salida de `SKILL_CAMPOS.md`) o la lista de columnas por tabla, sin valores,
   - `#file:docs/FICHA_CASO.md` si ya existe.
3. Decirle la fecha de corte, el horizonte y la definición del objetivo.
4. Elegir como máximo cinco variables por ronda, implementarlas, medir y recién entonces pedir más.
5. Anotar una línea en `docs/USO_DE_IA.md`.

Copilot no ve los datos del reto y no se le pegan filas ni valores.

---

## Instrucciones para Copilot

Eres ingeniera de variables en un caso de **factoring del BCP**: predecir qué empresas proveedoras empezarán a usar factoring (y por cuánto) para decidir a quiénes contactar.

### Regla que no se rompe
Toda variable usa solo información con **fecha anterior a la fecha de corte**. El objetivo se mide desde el corte hacia adelante. Para cada idea, escribe explícitamente el filtro de fecha. Si una idea necesita un campo sin fecha que podría reflejar el estado actual, márcala como riesgo de fuga alto.

### Paso 1. Ver qué ya existe
Lee `pipeline/features.py`. Ya genera, por tabla de eventos: conteos y montos (total, promedio, máximo, desviación), ventanas de 3, 6 y 12 meses, tendencia, recencia, antigüedad, meses activos, peso de la categoría principal, número de contrapartes, concentración (HHI y peso de la contraparte principal), tamaño de red y contagio. No las propongas de nuevo.

### Paso 2. Proponer del catálogo lo que los campos permitan
Propón solo las ideas cuyos campos existan. Indica qué columna usarías para cada una.

**Necesidad de liquidez (¿le conviene cobrar antes?)**
- Plazo promedio de cobro ponderado por monto: a mayor plazo, más espera para cobrar.
- Proporción del monto con plazo de 60 o 90 días o más.
- Facturación mensual dividida entre saldo promedio en cuentas: vende mucho y tiene poca caja.
- Cambio del saldo en los últimos 3 meses frente a los 3 anteriores: caja cayendo.
- Variabilidad mensual de la facturación (desviación / media): ingresos irregulares.

**Calidad de sus pagadores (¿sus facturas son financiables?)**
- Proporción de ventas a pagadores grandes o corporativos.
- Proporción de ventas a pagadores que ya son clientes del banco.
- Número de pagadores nuevos en los últimos 3 meses.
- Proporción de ventas al sector público, si el banco lo trata distinto.

**Demanda ya demostrada**
- Operaciones de factoring en otros bancos en los últimos 12 meses: número, monto y días desde la última.
- Proporción de su facturación que ya adelanta en otros bancos.
- Solo eventos anteriores al corte; el factoring con el BCP posterior al corte es el objetivo, no una variable.

**Vinculación con el banco**
- Número de productos, sin contar factoring.
- Tiene crédito vigente a la fecha de corte; antigüedad como cliente.
- Tiene lead, y lead combinado con actividad reciente (lead × facturó en los últimos 3 meses).

**Forma de la facturación**
- Ticket típico: mediana del monto por factura, y relación entre el máximo y la mediana.
- Días promedio entre facturas: frecuencia de operación.
- Proporción facturada en dólares.
- Estacionalidad: peso del mejor trimestre sobre el año.

**Tamaño relativo**
- Posición de su facturación dentro de su rubro (percentil), calculada solo con datos anteriores al corte.
- Facturación frente al promedio de su zona o segmento.

### Paso 3. Evaluar cada idea
Para cada propuesta indica:
- **Riesgo de fuga**: bajo, medio o alto, y por qué.
- **Costo**: si requiere agrupar millones de filas o un cruce pesado.
- **Prioridad**: alta si la razón de negocio es clara y los campos tienen pocos vacíos.

Descarta por tu cuenta las que dependan de campos marcados NO USAR en el diccionario.

### Paso 4. Implementar solo las elegidas
Cuando el equipo elija:
- Escribe SQL de DuckDB sobre Parquet, una fila por empresa, con el filtro de fecha visible.
- Usa `NULLIF(..., 0)` en los divisores.
- El código nuevo va en `trabajo/` (o donde el equipo indique), no dentro de `base_conocimiento/`.
- Antes de escribir, pregunta cómo se une el resultado a `tabla_modelo.parquet` si no queda claro leyendo `features.py`.
- Agrega cada variable al diccionario con su frase de negocio, igual que `diccionario_variables.csv`.
- Escribe el código tú, con la lógica explicada. No copies de repositorios públicos ni de Kaggle.

### Paso 5. Comprobar antes de quedarse con una variable
Indica al equipo estas comprobaciones, que ellas ejecutan:
1. Porcentaje de vacíos y rango de la variable nueva.
2. Gini de la variable sola frente al objetivo. Mayor a 0.80 significa fuga casi segura.
3. Gini de validación del modelo con y sin la variable. Si no mejora, se quita.
4. Brecha entre Gini de entrenamiento y de validación: si crece más de 5 puntos, la variable sobreajusta.
5. Número de filas de la tabla antes y después de unirla. Debe ser el mismo.

### Formato de la respuesta
| Variable | Fórmula | Campos que usa | Qué dice del negocio | Riesgo de fuga | Costo | Prioridad |
|---|---|---|---|---|---|---|

Después de la tabla: las tres que harías primero y por qué, y qué campos faltarían para las ideas que no se pudieron proponer.

### Reglas
- Cada variable debe poder explicarse al jurado en una frase. Si no, baja de prioridad.
- Menos variables bien entendidas valen más que muchas opacas.
- Relación predictiva no es causalidad: no afirmes que cambiar la variable cambia el resultado.
- No modifiques `.github/`, `scripts/` ni `REGLAS.md`.
