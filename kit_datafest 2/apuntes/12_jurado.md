# Preguntas del jurado · y respuestas en nuestras palabras

Regla: respondan con **qué hicimos + por qué + un número**. Nunca "lo hizo el código"; mejor "lo medimos y la
regla fue…". Si no saben algo: "no lo medimos; lo haríamos así…".

## Problema y negocio (Nat, Liz)

| Pregunta | Respuesta base |
| --- | --- |
| ¿Qué problema resolvieron? | Ordenar a las empresas por su probabilidad de tomar factoring en los próximos 6 meses, para que la fuerza de venta llame primero a las de mayor valor dentro de su capacidad |
| ¿Por qué ese target? | Es lo que pide el enunciado: factoring BCP no anulado entre el corte y 6 meses después. Las anuladas no son conversiones reales |
| ¿Cuál es el impacto? | Las 125 priorizadas convierten 52% contra 19.9% de la base: 2.6 veces más con las mismas llamadas |
| ¿Qué aprendieron del negocio? | Comercio convierte 25% vs 18.4%; quien ya hizo factoring es la segunda señal más fuerte; el tamaño (ventas) es la primera |
| ¿Cómo respetaron la capacidad? | 2.5% de la base repartido por cupos de zona; dentro de cada zona, las de mayor valor esperado |

## Datos (Hellen, Kath)

| Pregunta | Respuesta base |
| --- | --- |
| ¿Cómo limpiaron? | Leímos todo como texto y decidimos el tipo midiendo: si el 95% se lee como número, es número. Una función por tipo de dato |
| ¿Perdieron información? | No: conciliamos montos. La diferencia eran 834 valores 999999 ("sin dato") y 1 600 filas duplicadas |
| ¿Por qué DuckDB? | Con archivos grandes, pandas carga todo en memoria; DuckDB procesa por bloques y su SQL es fácil de revisar |
| ¿Cómo unieron las tablas? | Primero resumimos cada tabla de eventos a una fila por empresa y luego unimos. Así no se multiplican los montos |
| ¿Qué es una variable para ustedes? | Una descripción de la empresa el día del corte: cuánto factura, si crece, si ya usó factoring |

## Modelo y validación (Sophia, Kath)

| Pregunta | Respuesta base |
| --- | --- |
| ¿Cómo evitaron usar el futuro? | Toda variable usa fechas anteriores al corte, y entrenamos con un corte anterior cuyo resultado ya conocíamos |
| ¿Cómo lo comprobaron? | Prueba de fuga: ninguna variable sola supera Gini 0.5. Además metimos una fuga a propósito: el Gini saltó de 0.31 a 0.87 y la prueba la detectó |
| ¿Cómo validaron? | Fuera de tiempo: entrenamos con enero y examinamos con julio, como hará el banco. Gini 0.29 en el periodo no visto |
| ¿Por qué ese modelo? | Comparamos regla simple (0.26), logística (0.29) y LightGBM (0.25) con la misma validación. Ganó la logística, que además se explica |
| ¿Qué significa Gini 0.29? | Que ordena bastante mejor que el azar (0) y mejor que la regla simple (0.26); el 10% de arriba convierte 2 veces el promedio |
| ¿Por qué no un modelo más complejo? | Lo probamos (LightGBM) y midió menos: con 5 000 empresas y una señal casi lineal, lo simple generaliza mejor |
| ¿Qué variables importan? | Ventas, historia de factoring y rubro; más ventas y más historia suben la probabilidad |
| ¿Por qué no balancearon clases? | El Gini mide orden: balancear no lo mejora e infla las probabilidades que usamos en el valor esperado |

## Limitaciones (todas)

- Los datos del corte actual no traen el resultado: el Gini que reportamos es de un periodo anterior.
- El monto si convierte es una mediana por rubro (simple); un regresor podría mejorarlo.
- Las variables con historia distinta entre cortes las igualamos a 12 meses.

## Uso de IA (todas, con honestidad)

"Usamos IA para preparar material de estudio y una estructura inicial antes del evento; lo declaramos en
USO_DE_IA.md. El código que entregamos lo escribimos y lo entendemos: cada una puede explicar su parte."
(Digan esto solo si es verdad: por eso cada una reescribe su script.)
