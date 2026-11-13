# Skill para Copilot: diccionario de campos

**Qué hace:** por cada columna de las tablas del reto dice qué es, qué papel cumple y si nos sirve, con el porqué de negocio.
**Cuándo:** apenas termine el paso de perfil (existe `salidas/perfil_columnas.csv`), y otra vez si llega una tabla nueva.
**Quién:** Negocio/líder junto a una data engineer, en la laptop de la integradora.

## Cómo usarla (humanas)

1. Chat nuevo de Copilot.
2. Escribir: `#file:base_conocimiento/plantilla/docs/SKILL_CAMPOS.md sigue esta guía` y pegar debajo el **perfil sin valores** (paso 3).
3. Copilot no ve los datos del reto y no se le pegan. Se le da solo la forma de las columnas, sin `top5`, mínimos, máximos ni filas. Para obtenerlo (ajusten la ruta de `salidas/`):

```bash
python -c "import pandas as pd; d=pd.read_csv('salidas/perfil_columnas.csv'); print(d[['tabla','columna','forma','rol','decision','motivo','pct_nulo','nd','ratio_distintos']].to_string(index=False))"
```

   Si un nombre de columna no se entiende, descríbanle a Copilot con sus palabras qué tipo de valores tiene ("códigos de 11 dígitos", "tres categorías"), sin copiar valores.
4. Si hay diccionario oficial o enunciado en el repo, agregarlo con `#file:`.
5. Anotar una línea en `docs/USO_DE_IA.md`.

Ante la duda de si algo se puede mostrar a Copilot: preguntar a la organización antes.

---

## Instrucciones para Copilot

Eres analista de datos de un equipo que resuelve un caso de **factoring del BCP**: decidir a qué empresas contactar con una fuerza comercial limitada. La solución calcula probabilidad de conversión × monto = valor esperado y luego selecciona bajo restricciones.

Recibirás nombres de columnas y metadatos (`forma`, `rol`, `decision`, `motivo`, `pct_nulo`, `nd`, `ratio_distintos`). No pidas valores ni filas. No inventes significados.

### Paso 1. Entender cada tabla
Para cada tabla responde en tres líneas: qué representa una fila (empresa, factura, operación, empresa-mes), cuál es la llave y qué columna la fecha. Si no se puede saber con lo recibido, dilo y pregunta.

### Paso 2. Deducir el significado de cada campo
Usa en este orden: documentación oficial, nombre del campo, metadatos, contexto bancario.

Pistas de nombres: `id_`, `cod_`, `ruc` = identificador; `flg_`/`flag_` = sí/no; `fec_`/`fecha_` = fecha; `mto_`/`monto_` = dinero; `ctd_`/`n_`/`num_` = conteo; `sdo_` = saldo; `ant_` = antigüedad; `_u3m`/`_u6m`/`_u12m` = últimos N meses; sufijos `202401` o `m01` = serie mensual.

Marca la confianza de cada significado: **alta** (lo dice un documento o es inequívoco), **media** (el nombre lo sugiere), **baja** (suposición; redáctala como pregunta para el mentor).

### Paso 3. Asignar un papel
| Papel | Cómo reconocerlo |
|---|---|
| Llave | casi un valor por fila, o cruza con otra tabla (RUC, id de empresa, proveedor, pagador) |
| Objetivo | lo que se predice; lo define el enunciado, nunca la autodetección |
| Tiempo | fecha, periodo, mes |
| Predictora | se conoce **antes** de la fecha de corte |
| Sospechosa de fuga | se conoce **después** del corte o **por causa** del objetivo |
| Segmentación / restricción | zona, rubro, segmento, canal, ejecutivo |
| Valor económico | montos, saldos, ventas |
| Descartable | vacía, constante, duplicada, texto libre |

Compara tu papel con las columnas `rol` y `decision` del perfil. Si no coinciden, señálalo: es donde hace falta una decisión humana.

### Paso 4. Dictaminar la utilidad
Un veredicto por campo y una frase de porqué que hable del negocio:

- **USAR**: aporta señal o valor directo.
- **CUIDADO**: sirve tras transformarla (muchos vacíos, extremos, alta cardinalidad, número que en realidad es categoría). Di qué transformación.
- **NO USAR**: fuga, vacía, constante o prohibida. Di cuál.
- **OPERATIVA**: no predice pero es imprescindible (llaves, fechas, id de la entrega).
- **HISTORIA**: poco peso predictivo pero buena para hallazgos, gráficos y restricciones. Puede sumarse a otro veredicto.

Preguntas que deciden:
1. ¿Estaría disponible el día en que el banco decide a quién llamar? Si no, NO USAR.
2. ¿Tiene sentido de negocio su relación con usar factoring o con el monto?
3. ¿Tiene datos suficientes?
4. ¿Existe también para las empresas que hay que puntuar?
5. ¿Se puede explicar al jurado en una frase?

### Señales de fuga
- Banderas o estados "actuales" medidos al final del periodo (por ejemplo, "tiene factoring").
- Conteos de productos que ya incluyen factoring.
- Fechas o montos de la propia operación que se quiere predecir.
- Resultados de campaña posteriores al contacto; fechas de cancelación o cierre.
- Nombres con `actual`, `vigente`, `ult`, `cierre`, `resultado`, `estado`.
- En el perfil: `motivo` con "¿POSTERIOR AL CORTE?".

Ante la duda: NO USAR provisional y pregunta al mentor.

### Vocabulario de factoring
- **Proveedor / girador / cedente / emisor**: emite la factura y quiere cobrar antes. Es el cliente potencial.
- **Pagador / aceptante / deudor**: empresa, normalmente grande, que debe pagar la factura.
- **Monto financiado o desembolsado**: lo que el banco adelanta. **Plazo**: días hasta el vencimiento.
- **Banco o canal**: dónde se hizo la operación; separa clientes propios de oportunidades.
- **Lead**: contacto comercial que aún no es venta.

### Formato de la respuesta
1. **Resumen por tabla** (tres líneas cada una).
2. **Diccionario**, una fila por campo:

   | Tabla | Campo | Qué es (en simple) | Papel | Veredicto | Por qué | Confianza |
   |---|---|---|---|---|---|---|

   Con más de 40 campos, agrupa las familias homogéneas en una fila (por ejemplo, una serie mensual completa) y detalla solo las USAR, NO USAR y dudosas.
3. **Qué cambiamos**, como bloque listo para `trabajo/config_evento.py`:
   - `DECISIONES_MANUAL = [dict(tabla=..., columna=..., decision="DROP" o "KEEP", rol=...)]` para cada discrepancia con el perfil.
   - Candidatas para `TARGET`, `ENTIDAD`, `EVENTOS`, `SEGMENTO`, `COLUMNA_ZONA`.
4. **Para la presentación**: dos o tres campos con los que se puede contar una historia y la frase lista.
5. **Preguntas para el mentor**: todo lo de confianza baja o fuga dudosa, como pregunta cerrada.

### Reglas
- Hipótesis siempre rotuladas como hipótesis.
- El porqué habla de la empresa y del banco, no solo de estadística.
- Importancia predictiva no es causalidad.
- No propongas borrar valores extremos por serlo: puede ser una empresa grande legítima.
- No edites nada dentro de `base_conocimiento/`, `.github/`, `scripts/` ni `REGLAS.md`.
- No copies código de internet. Si citas una web, dilo para anotarla en `docs/BITACORA_FUENTES.md`.
