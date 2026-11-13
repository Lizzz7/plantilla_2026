# Guía del equipo · quién hace qué, qué debe dominar y qué edita

Esta guía acompaña a la plantilla simple. Cada integrante tiene su sección con:
**misión · qué entrega · su código · conceptos que debe dominar · qué edita según el reto · cómo verifica ·
cómo lee sus gráficos · errores típicos · preguntas del jurado · su día del evento · un ejercicio para hoy**.

Los números de ejemplo salen de los datos de práctica (5 000 empresas). Con los datos del evento serán otros:
lo que importa es saber **leerlos** y **explicarlos**.

---

## 0. Lo que TODAS deben saber (antes de su sección)

### 0.1 Las reglas del equipo

1. **Una dueña por paso.** Cada persona toca solo su script. `config.py` lo toca solo Nat.
2. **Se edita dentro de las zonas `# >>> EDITABLE`.** Fuera de ellas está el motor: se lee, no se cambia sin motivo.
3. **Ningún `[!!]` se ignora.** Un aviso es una decisión pendiente. Se resuelve (config, código) o se anota por qué se acepta.
4. **Todo cambio se prueba antes de compartir:** `python correr_todo.py --desde <mi paso>` y revisar el reporte.
5. **Relevo explícito:** al terminar su paso, cada una avisa en el chat "paso N listo, sin [!!]" (o cuáles quedan).

### 0.2 El flujo y los relevos

```
datos/ ─► 1 Hellen ─► 2 Nat ─► 3 Kath ─► 4 Sophia ─► 5 Liz ─► submission.csv
          limpiar     revisar   variables   modelos     priorizar
             ▲           │          │           │
             └─ config ◄─┴── fuga ──┴── fuga ───┘    (un problema DEVUELVE al paso que lo arregla)
```

### 0.3 Ocho conceptos que cualquiera debe poder explicar en 20 segundos

| Concepto | Explicación corta | Ejemplo con nuestros datos |
| --- | --- | --- |
| **Fecha de corte** | El "día de decidir". Las variables usan solo lo que pasó ANTES; el target mira DESPUÉS | corte 2025-07-01: las facturas hasta junio son variables; el factoring de jul–dic es el target |
| **Horizonte** | Cuánto tiempo después del corte se mira el target | 6 meses |
| **Fuga (leakage)** | Usar información que no existía el día de decidir. Infla el resultado en casa y lo hunde en la evaluación | `ops_ultimo_semestre`: Gini 0.16 en el corte anterior, 0.91 en el actual → fuga |
| **Grano / entidad** | Qué representa una fila. El modelo trabaja con 1 fila por empresa | facturas: 16 filas por empresa → se resumen antes de unirlas |
| **Validación fuera de tiempo** | Entrenar con un corte anterior (su target ya ocurrió) y examinar con el actual | entrena con 2025-01-01, examina con 2025-07-01 |
| **Gini** | Qué tan bien ORDENA el modelo: 0 = azar, 1 = perfecto. Gini = 2·AUC − 1. Estándar en banca | 0.268 en el examen; una regla simple da 0.260 |
| **Lift / captura** | Cuántas veces más convierte el top de la lista que el promedio | el 10% de arriba convierte 1.9× el promedio; las 125 priorizadas, 2.3× |
| **Valor esperado** | Probabilidad × monto si convierte: a quién llamar primero si importan los soles | 0.40 × S/ 50 000 = S/ 20 000 |

### 0.4 Las herramientas (y por qué son las que se usan en la industria)

| Herramienta | Para qué la usamos | Por qué esa y no otra |
| --- | --- | --- |
| **DuckDB** (SQL) | Leer y limpiar archivos grandes, resumir eventos | Procesa por bloques y usa disco si falta RAM: 8 GB no la tumban. Pandas cargaría todo en memoria |
| **Parquet** | Guardar tablas limpias | Columnar y comprimido; se lee en segundos. El Excel se lee una sola vez |
| **pandas** | Manipular tablas ya pequeñas (1 fila por empresa) | El estándar para tablas que entran en memoria |
| **scikit-learn** | Regresión logística, validación cruzada, importancia | La librería de referencia de ML clásico |
| **LightGBM** | Árboles con boosting | El modelo que más gana en datos tabulares; rápido |
| **matplotlib** | Gráficos que explican cada paso | Sin internet, PNG que se pega en la presentación |

---

## 1. NAT · Líder e integradora (config, revisión del caso, integración)

### Misión
Que el equipo resuelva **el problema correcto**: traducir el enunciado a `config.py`, verificar que todo apunta a
datos que existen, integrar los pasos y convertir los resultados en una historia.

### Qué entrega y a quién
- A todas: `config.py` correcto (después del paso 1) y el paso 2 sin `[!!]` sin resolver.
- Al final: `salidas/reporte.html` revisado, la entrega en `main` y la presentación.

### Su código
| Archivo | Qué hay dentro (en orden) |
| --- | --- |
| `config.py` | 0 tipo de reto · 1 lectura (OPCIONES_LECTURA, UNIR) · 2 fechas · 3 tablas · 4 TARGET y PREDECIR · 5 decisiones humanas · 6 negocio y entrega · 7 limpieza |
| `2_revisar_caso.py` | (1) ¿existen tablas y columnas? → se detiene si no · (2) llave de empresas · (3) target: línea de tiempo (forma A) o filas con/sin target (forma B) · (4) tasa base y lead · (5) capacidad y cupos |
| `correr_todo.py` | corre 1→5, se detiene en el que falla y dice `--desde N`; arma el reporte |

### Conceptos que debe dominar
- **Las dos formas de target.** *Forma A (evento)*: el target se construye contando eventos después del corte
  (ej. "tomó factoring BCP no anulado entre jul y dic"). *Forma B (columna)*: el target ya viene (ej. `compro = SI/NO`).
  La pregunta para decidir: **¿el enunciado me da la etiqueta o me da la historia?**
- **Corte, horizonte y corte anterior.** Corte anterior = corte − horizonte. Si el corte es 2025-07-01 y el horizonte
  6 meses → 2025-01-01. Con ese se entrena porque su target (ene–jun 2025) ya ocurrió.
- **HISTORIA_MESES.** Las variables miran N meses antes del corte. Los datos deben cubrir esos meses también para el
  corte anterior; si no, un "monto total" significa cosas distintas en cada tabla y el modelo falla. (Lo vimos: con
  historia desigual, la logística caía a ~0.21 de Gini en el examen.)
- **Tasa base.** El % que convierte. Todo se compara contra ella ("las priorizadas convierten 2.3× la base").
- **Forma A vs forma B del negocio (lead).** Con lead = convertir más a quienes ya tienen oportunidad; sin lead =
  elegir a quién "habilitar". Se controla con `ELEGIBLES`.

### Qué edita según el reto
| Situación | Cambio en `config.py` |
| --- | --- |
| Nombres reales de tablas/columnas | copiar de la salida del paso 1 a `EMPRESAS`, `ATRIBUTOS`, `EVENTOS` |
| El enunciado da la etiqueta hecha | `TARGET = dict(tipo="columna", tabla=..., id=..., columna=...)` |
| Dan una lista de a quién evaluar | `PREDECIR = dict(tabla=..., id=...)` |
| Piden un monto | `TIPO_PROBLEMA = "regresion"` |
| Otra capacidad/cupos | `CAPACIDAD`, `CUPOS_ZONA` (o `None`) |
| Nombres de la entrega | `ENTREGA["columnas"]` |
| Probar una idea sin romper la config principal | copiar a `config_prueba.py` y `python correr_todo.py --config config_prueba.py` |

### Cómo verifica que su parte está bien
- [ ] Paso 2: todas las líneas `[OK]` en la sección 1.
- [ ] La línea de tiempo muestra eventos antes y después del corte anterior (si no, no hay con qué entrenar).
- [ ] La tasa base es razonable (ni 0% ni 90%) y parecida entre cortes.
- [ ] Cada `[!!]` tiene una decisión anotada.
- [ ] El TARGET fue validado con el mentor.

### Cómo leer sus gráficos
- **2_linea_tiempo**: barras = eventos del target por mes. Franja naranja = target con el que se entrena; franja azul =
  target que se predice. Si la franja azul está vacía, es el futuro (normal en el evento).
- **2_lead**: conversión con y sin lead. Si la diferencia es grande, preguntar si piden convertir o habilitar.

### Errores típicos
- Dejar valores de ejemplo de los datos de práctica en la config (el paso 2 los detecta).
- Confundir el corte con el último dato: el corte es el día de DECIDIR, no el último día del archivo.
- Cambiar la config sin avisar: todos los pasos posteriores cambian.

### Preguntas del jurado
- *¿Por qué ese target?* "Es lo que pide el enunciado: factoring BCP no anulado en los 6 meses siguientes. Las
  anuladas no son conversiones reales."
- *¿Cómo evitaron usar el futuro?* "Todo se calcula con datos anteriores al corte, y entrenamos con un corte
  anterior cuyo resultado ya conocíamos."
- *¿Qué significa su resultado para el negocio?* "Con las mismas 125 llamadas, 2.3 veces más conversiones."

### Su día del evento
| Hora | Qué |
| --- | --- |
| 14:30 | Anotar: target, corte, horizonte, métrica, formato de entrega, capacidad, cupos |
| 16:00 | Hellen corre el paso 1 → Nat llena `config.py` → paso 2 hasta que no haya errores |
| ~18:00 | `correr_todo.py --desde 3`; reparto de alertas a cada dueña |
| ~22:00 | Primer submission válido en `main` |
| Sáb 9:00 | Congelar; presentación con el reporte |

### Ejercicio para hoy (30 min)
Copien `config.py` a `config_b.py` y conviértanla al **escenario B**: un archivo `etiquetas.csv` (separado por `;`)
con `ID Cliente` y `Compró` (SI/NO), y un Excel `a_evaluar.xlsx` con dos filas de título. Pistas: `OPCIONES_LECTURA`,
`TARGET` forma B, `PREDECIR`. Corran `python correr_todo.py --config config_b.py`.

---

## 2. HELLEN · Data Engineer 1 (ingesta y limpieza)

### Misión
Que los datos entren **completos y bien convertidos**, y poder demostrarlo con números.

### Qué entrega y a quién
A Nat: la lista de tablas y columnas (salida del paso 1) para llenar la config. A Kath: `salidas/limpio/*.parquet`
con tipos correctos y montos conciliados.

### Su código: `1_limpiar.py` (y las funciones de `comun.py`)
1. `leer_crudo()`: lee cada archivo **todo como texto**. Excel con varias hojas iguales → una tabla. CSV → DuckDB
   directo (sin pasar por memoria). Si falla: prueba latin-1 y luego pandas.
2. Vistas `crudo__<tabla>` con nombres normalizados; `UNIR` junta tablas partidas.
3. `decidir_tipo()` (**EDITABLE**): por cada columna mide qué % se lee como número y como fecha, y decide.
4. Limpia con `txt`, `idn`, `num`, `fecha` y quita duplicados exactos.
5. Concilia montos y cuenta valores anulados por columna.

### Conceptos que debe dominar
- **Por qué todo como texto.** Si se deja que la herramienta adivine, un RUC `00123` pierde ceros, `05/03` puede leerse
  como 3 de mayo, y un `S/D` en la fila 2 millones tumba la carga a los 20 minutos. Leer como texto nunca falla;
  el tipo se decide después, **midiendo**.
- **Las 4 funciones de limpieza** (en `comun.py`, en SQL):

| Función | Qué arregla | Entrada → salida |
| --- | --- | --- |
| `txt` | espacios, tildes, mayúsculas, "sin dato" | `' Comércio '` → `COMERCIO` · `'S/D'` → vacío |
| `idn` | llaves que no calzan al unir | `'20123456789.0'` → `20123456789` |
| `num` | números escritos como texto | `'S/ 1,234.50'` → 1234.5 · `'1.234,50'` → 1234.5 · `'(500)'` → −500 · `999999` → vacío |
| `fecha` | varios formatos | `'05/03/2024'`, `'20240305'`, `45356` (serial de Excel) → 2024-03-05 · `1900-01-01` → vacío |

- **Formato europeo con cuidado.** `'0.751'` es decimal (0.751), no 751. Solo se trata como europeo cuando no hay
  duda: `'1.234,50'`, `'1.234.567'`, `'12,5'`.
- **Centinela.** Un número que significa "sin dato" (`999999`, `-999`). Si se deja como número, infla los montos.
- **Conciliación.** La suma de cada monto antes y después debe cuadrar o explicarse. En la práctica: `imp_factura`
  pasa de 1 555 a 708 millones = 834 centinelas (834 millones) + 1 600 filas duplicadas (13 millones). Cuadra al sol.
- **Umbral 95%.** Una columna es número si al menos 95% de sus valores no vacíos se leen como número. Por debajo
  hay demasiados formatos raros para confiar: queda como texto y se avisa.

### Qué edita según el reto
| Situación | Dónde | Cambio |
| --- | --- | --- |
| Excel con título arriba / otra hoja | `config.OPCIONES_LECTURA` | `dict(hoja="X", saltar_filas=2)` (se lo pasa a Nat) |
| CSV con `;` | `config.OPCIONES_LECTURA` | `dict(separador=";")` |
| Una columna con tipo equivocado | `config.FORZAR_TIPO` | `{"tabla.columna": "texto"}` |
| Fechas `mm/dd/aaaa` | `config.FORMATOS_FECHA` | poner `"%m/%d/%Y"` primero |
| Columnas de fecha con otro nombre (`f_emis`) | `1_limpiar.py` → `PISTAS_FECHA` | agregar `"f_"` |
| Llaves con otro nombre (`nro_ruc`) | `1_limpiar.py` → `PISTAS_LLAVE` | agregar `"nro_ruc"` |
| Filas repetidas legítimas | `1_limpiar.py` | `QUITAR_DUPLICADOS = False` |

### Cómo verifica
- [ ] Ninguna tabla con 0 filas ni con una sola columna.
- [ ] Cada llave aparece como `[l]`, cada fecha como `[f]`, cada monto como `[n]` en la salida.
- [ ] Toda diferencia de montos explicada por centinelas + duplicados.
- [ ] Ninguna columna con más de 5% de valores anulados sin revisar.

### Cómo leer sus gráficos
- **1_filas**: crudo vs limpio por tabla; la diferencia son duplicados quitados.
- **1_conciliacion**: suma de cada monto antes/después con la explicación en naranja.
- **1_calidad**: % de valores que no se pudieron convertir; la línea roja es 5%.

### Errores típicos
- Una fecha que quedó como texto (formato no contemplado) → no habrá variables de tiempo.
- Un código numérico (CIIU, ubigeo) que quedó como número → `FORZAR_TIPO` a texto.
- Quitar duplicados cuando eran operaciones legítimas → revisar si la tabla tiene id por fila.

### Preguntas del jurado
- *¿Por qué DuckDB y no pandas?* "Con 8 GB pandas carga todo en memoria y se cae; DuckDB procesa por bloques y
  usa disco si falta RAM."
- *¿Se perdió información al limpiar?* "No: la suma de montos se concilia; la diferencia son 834 valores 999999
  (sin dato) y 1 600 filas duplicadas."
- *¿Cómo deciden el tipo de una columna?* "Midiendo: si 95% se lee como número, es número. No por el nombre."

### Su día del evento
| Hora | Qué |
| --- | --- |
| 16:00 | Copiar datos a `datos/`; `python 1_limpiar.py` |
| 16:20 | Pasar a Nat la lista de tablas/columnas; corregir lecturas raras |
| ~17:00 | Conciliación explicada; aviso "paso 1 listo" |

### Ejercicio para hoy (30 min)
1. Guarden `datos/maestro_clientes.csv` separado por `;` (ábranlo en Python y `to_csv(sep=";")`) y corran el paso 1:
   verán el aviso de "una sola columna". Arréglenlo con `OPCIONES_LECTURA`.
2. **Trampa escondida:** `num_trabajadores` trae `-1` en ~5% de las filas (mínimo = −1). ¿Es "sin dato"?
   Decídanlo y, si lo es, agreguen `-1` a `CENTINELAS_NUMERO` (ojo: aplica a TODAS las columnas numéricas;
   revisen que ninguna otra use −1 como valor real).
3. Fuercen `num_trabajadores` como texto con `FORZAR_TIPO` y vean cómo cambia la salida.

---

## 3. KATH · Data Engineer 2 (variables y fugas)

### Misión
Que la tabla del modelo sea **verdadera**: una fila por empresa, sin multiplicar ni perder empresas, y con variables
que usan **solo** el pasado.

### Qué entrega y a quién
A Sophia: `salidas/tabla_entrena.parquet` (con target) y `salidas/tabla_predice.parquet`, más `diccionario.csv`
(qué significa cada variable).

### Su código: `3_variables.py`
1. `preparar_atributos()`: tablas de 1 fila por empresa. Quita `COLUMNAS_FUERA`; fechas → días antes del corte;
   columnas mensuales (`saldo_202401…`) → `saldo_m1…m6` (meses antes del corte); texto libre fuera.
2. `resumir_eventos()`: por cada tabla de `EVENTOS`, las `AGREGACIONES` (**EDITABLE**) solo con fechas < corte.
3. `construir()`: une todo con `assert` de "1 fila por empresa" (si un JOIN duplica, se detiene).
4. Arma entrena / predice según la forma del target.
5. Prueba de fuga y gráfico de "una empresa en el tiempo".

### Conceptos que debe dominar
- **Grano.** Facturas tiene 16 filas por empresa. Si se une directo al maestro, cada empresa aparece 16 veces y sus
  montos se multiplican. Por eso primero se **resume** (una fila por empresa) y luego se une.
- **Agregaciones y su significado.** `n` (cuántos eventos), `monto_total`, `monto_3m` (últimos 3 meses),
  `recencia_dias` (hace cuánto fue el último: poco = activo), `antiguedad_dias`, `meses_activos`, `tendencia`
  (últimos 3 meses vs promedio trimestral: > 1 crece), `n_contrapartes` (diversificación).
- **Sin eventos = 0, no vacío.** Una empresa sin facturas tiene 0 facturas. Su recencia se llena con
  "más antiguo que la historia" (HISTORIA_MESES × 31 días), no con un vacío.
- **Columnas mensuales.** `saldo_202507` es posterior al corte 2025-07-01: no puede entrar. Se renombran relativas
  al corte (`saldo_m1` = junio 2025) para que las dos tablas tengan las mismas columnas.
- **Prueba de fuga.** Una variable sola con Gini > 0.5, o que salta mucho entre la tabla que entrena y la que
  predice, es sospechosa. Pregunta clave: **¿este dato existía el día de decidir?**
- **Fecha posterior al corte.** Si `fecha_ultimo_contacto` tiene fechas después del corte (18.5% en la práctica),
  esa columna mira el futuro: o se quita, o se confirma que es legítima.

### Qué edita según el reto
| Situación | Dónde | Cambio |
| --- | --- | --- |
| Una variable de eventos nueva | `AGREGACIONES` | `("n_pagadores", "count(DISTINCT cp)", "n° de pagadores", "cp")` |
| Esa variable necesita otra columna | `config.EVENTOS[...]["extra"]` | `extra=dict(cp="ruc_pagador")` (con Nat) |
| Un ratio o bandera | `variables_extra()` | `df["ratio"] = df["ops__monto_total"] / df["ventas_anuales"]` |
| Contar solo un tipo de evento | `AGREGACIONES` | `("n_web", "count(*) FILTER (WHERE cat = 'WEB')", "...", "cat")` |
| Más meses mensuales | `MESES_MENSUALES` | `12` |
| Categorías con muchos valores | `MAX_CATEGORIAS` | o agruparlas en `variables_extra()` |
| Una variable es fuga | `config.COLUMNAS_FUERA` (con Nat) | `"columna": "motivo"` |

En el SQL de `AGREGACIONES`: `f` = fecha del evento, `m` = monto en soles, `d` = fecha de corte, y los alias de
`extra` (`cp`, `cat`...).

### Cómo verifica
- [ ] "Entrena" y "Predice" con el número de filas esperado.
- [ ] Ningún `[!!]` de fuga sin decidir.
- [ ] En **3_una_empresa**, los puntos azules de cada fila = el valor de `__n` a la derecha.
- [ ] El diccionario explica cada variable nueva.

### Cómo leer sus gráficos
- **3_fugas**: fuerza de cada variable sola en las dos tablas. Línea roja = 0.5. Una barra que cruza la línea o
  que es mucho más larga en una tabla que en la otra = sospecha.
- **3_una_empresa**: los eventos de una empresa en el tiempo. Azul = se usa; gris = más viejo que la historia;
  naranja = después del corte (no se usa). Es la mejor diapositiva para explicar "sin futuro".

### Errores típicos
- Un id con formato distinto entre tablas (`.0`) → variables vacías para todos (Hellen lo arregla con `idn`).
- Una tabla de "foto" tomada hoy (perfil con acumulados al día de hoy) → fuga.
- Olvidar que la tabla del target también aporta variables de historia (`ops__n` = factoring ANTES del corte).

### Preguntas del jurado
- *¿Cómo garantizan que no usan el futuro?* "Cada variable filtra fecha < corte. Mostramos una empresa en el tiempo:
  sus eventos antes del corte cuentan (y su conteo coincide con la variable); los de después no."
- *¿Qué es la tendencia?* "Monto de los últimos 3 meses contra el promedio trimestral del año: más de 1 es que crece."
- *¿Por qué sacaron `ops_ultimo_semestre`?* "Es una foto tomada hoy: en el corte actual ya incluye el semestre que
  queremos predecir. Su Gini saltaba de 0.16 a 0.91."

### Su día del evento
| Hora | Qué |
| --- | --- |
| ~17:30 | `python 3_variables.py`; revisar fugas y "una empresa" |
| ~18:00 | Proponer variables nuevas (AGREGACIONES) con sentido de negocio |
| ~18:30 | Aviso "paso 3 listo" a Sophia |

### Ejercicio para hoy (30 min)
1. Agreguen a `AGREGACIONES` el plazo promedio de cobro de las facturas: en config, `extra=dict(cp="ruc_pagador",
   plazo="dias_plazo")` y la línea `("plazo_prom", "avg(plazo)", "días promedio de cobro", "plazo")`.
2. Agreguen en `variables_extra()` el ratio `ops__monto_total / ventas_anuales`. Corran `--desde 3` y vean si entra
   en la importancia del paso 4.

---

## 4. SOPHIA · Data Scientist 1 (modelos y validación)

### Misión
Un modelo **honesto** (sin fugas, validado en un periodo que no vio) y una frase que diga cuánto mejora frente a no
tener modelo.

### Qué entrega y a quién
A Liz: `salidas/predicciones_modelo.parquet` (`prob` o `pred` por empresa) e `importancia.csv`. A Nat: la frase
para el jurado y los gráficos del modelo.

### Su código: `4_modelo.py`
1. Filtro: fuera variables sin señal (fuerza < `MIN_SENAL`) y repetidas (parecido > `MAX_PARECIDO`).
2. `CANDIDATOS` (**EDITABLE**): regla de 1 variable → lineal → LightGBM, con la misma validación (5 pliegues).
3. Elige el mejor; si uno más simple queda a menos de `TOLERANCIA`, gana el simple.
4. Examen (si la tabla que predice tiene target) y predicción final.
5. Importancia por permutación, deciles y gráficos.

### Conceptos que debe dominar
- **OOF (fuera de pliegue).** Se parte la tabla en 5; cada parte se predice con un modelo que no la vio. Así la
  comparación entre modelos es justa.
- **Regla simple como línea base.** "Ordenar por ventas" es lo que haría un ejecutivo sin modelo (Gini 0.260).
  Si el modelo no le gana, no aporta.
- **Lineal (logística) vs LightGBM.** La logística suma efectos con pesos: se explica con "más ventas → más
  probabilidad". LightGBM combina reglas tipo árbol: capta no linealidades, pero se sobreajusta con pocos datos.
  En la práctica ganó la logística (0.308 vs 0.253): la señal es casi lineal.
- **Por qué logaritmo en los montos.** Montos de S/ 0 a S/ 2.9 millones: sin log, unas pocas empresas gigantes
  dominan los pesos de la logística. Sin filtro y sin log daba Gini 0.240 (OOF); con ambos, 0.308.
- **Filtro de variables.** Con 100 variables y ruido (40 de buró al azar), el modelo empeoraba frente a la regla.
  Quitar las que no ordenan solas y las duplicadas lo arregló.
- **Examen vs OOF.** Si el examen cae más de 0.05 frente al OOF → sobreajuste o fuga. En la práctica: 0.308 → 0.268.
- **Importancia por permutación.** Desordenar una variable y medir cuánto empeora. Más honesta que "cuánto la usó".
- **Regresión.** Si piden un monto: métrica R² (qué parte de la variación explica). Con muchos ceros, LightGBM con
  `objective="tweedie"` o el modelo en dos partes.

### Qué edita según el reto
| Situación | Dónde | Cambio |
| --- | --- | --- |
| Otro modelo | `CANDIDATOS` | descomentar `random_forest` o agregar uno |
| Otra métrica oficial | `metrica()` | `average_precision_score` (AUC-PR), F1 con umbral, MAE |
| Pocos datos (< 2 000 filas) | `PLIEGUES = 3` | y quedarse con regla/lineal |
| Más/menos variables | `MIN_SENAL`, `MAX_PARECIDO` | ej. 0.01 / 0.95 |
| LightGBM sobreajusta | `CANDIDATOS["lightgbm"]` | `num_leaves=7`, `min_child_samples=100` |
| Montos con ceros | `CANDIDATOS["lightgbm"]` | `objective="tweedie"` |

### Cómo verifica
- [ ] El elegido le gana a `regla_1var`.
- [ ] Examen vs OOF: caída < 0.05.
- [ ] Gini < 0.8 (más alto = buscar fuga con Kath).
- [ ] Las variables top tienen sentido de negocio.

### Cómo leer sus gráficos
- **4_modelos**: barras por candidato (gris OOF, azul examen). La etiqueta "ELEGIDO" marca el ganador.
- **4_deciles**: % que convierte en cada décimo de la lista. D1 alto y bajando = el modelo ordena bien.
- **4_importancia**: cuánto empeora el Gini al desordenar cada variable, con su dirección ("más → sube").

### Errores típicos
- Elegir el modelo por el Gini de entrenamiento y no por el OOF/examen.
- Reponderar clases "porque hay desbalance": baja el Gini e infla probabilidades (Liz las multiplica por montos).
- Usar Optuna/ajuste fino antes de tener buenas variables: mueve poco.

### Preguntas del jurado
- *¿Cómo validaron?* "Entrenamos con el corte anterior y examinamos con el actual, como hará el banco. Gini 0.308
  en validación cruzada y 0.268 en el periodo que el modelo no vio."
- *¿Por qué logística y no algo más complejo?* "Comparamos con la misma validación; LightGBM dio 0.253. Ante un
  empate preferimos el simple: se explica mejor y se rompe menos."
- *¿Qué variables importan?* "Ventas anuales, el monto de factoring que ya hizo y el rubro; más ventas → más probabilidad."

### Su día del evento
| Hora | Qué |
| --- | --- |
| 14:30 | Preguntar la métrica oficial y si piden probabilidad o monto |
| ~18:30 | `python 4_modelo.py`; revisar elegido, examen e importancia |
| ~21:00 | Aviso "paso 4 listo" a Liz |
| noche | Probar 1–2 candidatos más solo si sobra tiempo |

### Ejercicio para hoy (30 min)
1. Descomenten `random_forest` en `CANDIDATOS` y corran `python 4_modelo.py`. ¿Gana? ¿Por qué sí o no?
2. Cambien `metrica()` a AUC-PR (`average_precision_score`) y vean si cambia el elegido.

---

## 5. LIZ · Data Scientist 2 (priorización, hallazgos y entrega)

### Misión
Convertir el modelo en **decisiones**: a quién llamar, en qué zonas, cuánto valor, y dejar el CSV final validado.

### Qué entrega y a quién
A Nat: `salidas/submission.csv` (con los nombres del enunciado), `priorizados.csv`, los hallazgos de negocio y el
guion de impacto.

### Su código: `5_priorizar_entregar.py`
1. `monto_si_convierte()` (**EDITABLE**): mediana de su rubro entre las que convirtieron al entrenar.
2. Valor esperado = prob × monto.
3. `elegibles()` (**EDITABLE**): todos / con lead / sin lead.
4. `priorizar()` (**EDITABLE**): por zona con cupos (resto mayor) o global.
5. Gráficos de negocio, CSV final y 6 controles.

### Conceptos que debe dominar
- **Valor esperado.** Si importan los soles: prob × monto. Una empresa con 30% de probabilidad y S/ 100 000 vale más
  (30 000) que una con 60% y S/ 20 000 (12 000). Si importa el número de clientes: ordenar por probabilidad
  (`ORDENAR_POR = "prob"`).
- **Cupos por zona con "resto mayor".** 2.5% de 5 000 = 125. LIMA 50% = 62.5 → 62; el medio sobrante va a la zona
  con mayor decimal, para que los cupos sumen exactamente 125.
- **Dentro de cada zona, de mayor a menor valor.** Es la solución óptima cuando la única restricción es el cupo por
  zona (no hace falta optimización compleja).
- **Elegibles.** "Habilitar" = elegir entre quienes NO tienen lead (`ELEGIBLES = "sin_lead"`).
- **Curva de captura.** Si llamamos al 2.5% de arriba, ¿qué % de todas las conversiones capturamos? Al azar sería
  2.5%; con el modelo, unas 2.4 veces más (5.9% de las conversiones con el 2.5% de las llamadas).
- **Hallazgos con número.** "Comercio convierte 25% vs 18% del promedio" es una frase de negocio; "el modelo es
  bueno" no lo es.

### Qué edita según el reto
| Situación | Dónde | Cambio |
| --- | --- | --- |
| Otra forma de estimar el monto | `monto_si_convierte()` | usar `ops__monto_prom` (lo que ya financió) o un regresor |
| Solo con/sin lead | `config.ELEGIBLES` | `"con_lead"` / `"sin_lead"` |
| Maximizar clientes | `ORDENAR_POR` | `"prob"` |
| Mínimo por rubro, tope por segmento | `priorizar()` | agregar la regla en el bucle |
| Otros nombres de columnas | `config.ENTREGA` | `{"id": "ID", "prob": "PROBABILIDAD"}` |
| Solo probabilidades | `config.CAPACIDAD = None` | — |

### Cómo verifica
- [ ] Los 6 controles en `[OK]`.
- [ ] Priorizadas por zona = cupos.
- [ ] El CSV tiene exactamente las columnas y nombres que pide el enunciado.
- [ ] Validador oficial del evento (`python -m datafest.validar`) en OK.

### Cómo leer sus gráficos
- **5_rubros**: % que convierte por rubro; azules = sobre el promedio.
- **5_zonas**: priorizadas por zona ("de N" = cuántas había).
- **5_captura**: curva azul (modelo) sobre la diagonal (azar); el punto naranja es la capacidad.

### Errores típicos
- Nombres de columnas distintos a los del enunciado → la entrega no valida.
- Zonas escritas distinto (`Lima` vs `LIMA`) → nadie ocupa el cupo (Hellen normaliza con `txt`).
- Priorizar por probabilidad cuando el enunciado habla de "valor" (o al revés).

### Preguntas del jurado
- *¿Por qué esta empresa está primera?* "Tiene alta probabilidad (ventas altas, ya hizo factoring) y un monto
  esperado alto por su rubro."
- *¿Cómo respetan los cupos?* "Dentro de cada zona tomamos las de mayor valor hasta llenar su cupo."
- *¿Cuál es el impacto?* "Las 125 priorizadas convierten 45.6% contra 19.9% de la base: 2.3 veces más con las
  mismas llamadas."

### Su día del evento
| Hora | Qué |
| --- | --- |
| 15:30 | Leer el formato de entrega; ajustar `ENTREGA` con Nat |
| ~21:00 | `python 5_priorizar_entregar.py`; controles en OK |
| ~21:30 | Validador oficial y PR → primer submission a las 22:00 |
| Sáb 9:00 | Hallazgos y guion de impacto para Nat |

### Ejercicio para hoy (30 min)
1. Pongan `ELEGIBLES = "sin_lead"` (en una `config_prueba.py`) y `ORDENAR_POR = "prob"`. ¿Cómo cambian las
   priorizadas y su conversión?
2. Cambien `monto_si_convierte()` para usar `ops__monto_prom` cuando sea mayor que 0. ¿Cambia el valor total?

---

## 6. Ensayo general (todas juntas, 60 min)

1. Nat genera datos nuevos: `python datos_practica.py --empresas 8000 --semilla 11` (otra muestra, distinta a la de práctica).
2. Cada una corre su paso **en orden** y avisa en el chat al terminar (como en el evento).
3. Nat cronometra: objetivo **< 45 min** de datos a submission.
4. Ronda de jurado: cada una responde 2 preguntas de la sección de otra.
