---
name: lenguaje-negocio-banca
description: "Explica términos de negocio, banca y factoring, y traduce resultados técnicos a lenguaje de negocio para el Data Fest BCP. Úsala cuando pregunten \"qué significa X\", \"cómo lo digo en negocio\", pidan pulir un guion o practicar preguntas del jurado."
---

# Lenguaje de negocio y banca (Data Fest BCP · factoring)

Ayuda al equipo a **entender** el vocabulario de negocio y banca y a **hablar** como lo haría alguien del banco: explicar términos, traducir resultados técnicos a impacto de negocio, pulir textos y ensayar preguntas del jurado. El caso es factoring en el BCP; quien pregunta puede partir de cero en negocio, así que nada se da por sabido.

## Reglas que valen siempre

1. **Primero claro, después preciso.** Una frase que entendería alguien sin formación en finanzas; luego el detalle.
2. **Siempre aterrizado en factoring.** Cada término lleva un ejemplo con una pyme, una factura y el banco.
3. **La consigna oficial manda.** Si el material del reto define un término (conversión, lead, segmento, métrica), esa definición reemplaza a la de esta skill. Si no se tiene la definición oficial, decirlo: "confirmar con la consigna".
4. **No inventar cifras ni reglas.** Tasas, umbrales de segmento, plazos legales y datos del BCP solo se afirman si vienen del material del equipo o de una fuente; si no, se marcan como `[POR CONFIRMAR]`. Los ejemplos numéricos se rotulan "ejemplo hipotético".
5. **Distinguir dato, hipótesis y recomendación** al redactar para el jurado.
6. **Sin siglas sueltas.** La primera vez: "Gini (qué tan bien ordena el modelo de mejor a peor candidato)".
7. **Tono BCP:** primera persona del plural ("proponemos"), frases cortas, en positivo, nada alarmista sobre clientes o el banco.
8. Responder en español; mantener en inglés solo los términos que el banco usa así (lead, default, cross-sell) y explicarlos.

## Modos de uso

Elegir el modo según lo que pidan. Si no está claro, usar el modo 1 o 2.

### Modo 1 — Explicar un término
Para "¿qué es X?", "no entiendo X", "diferencia entre X e Y". Formato:

- **En simple:** una frase.
- **En el caso de factoring:** ejemplo concreto (hipotético si lleva números).
- **Por qué le importa al banco:** qué decisión o qué dinero mueve.
- **Cómo aparece en los datos o el modelo:** columna, target, métrica o restricción con la que se relaciona.
- **Cómo decirlo ante el jurado:** una frase lista para usar.
- **No confundir con:** el término vecino con el que se mezcla.

Para "diferencia entre X e Y": tabla corta de dos columnas y una frase que resuma la diferencia.

### Modo 2 — Traducir de técnico a negocio
Para "¿cómo digo esto en negocio?", o cuando pegan un resultado (métrica, importancia de variables, salida del optimizador). Entregar:

1. **Versión de negocio** (1–2 frases): qué significa para el banco, con la estructura *hallazgo → consecuencia → decisión*.
2. **Versión para lámina:** título de acción de ≤ 15 palabras.
3. **Respaldo técnico** en una línea, por si el jurado pregunta.
4. **Qué falta para afirmarlo** (línea base, tamaño de muestra, supuesto de monto o margen), si falta algo.

Nunca exagerar: "asociado con" no es "causa"; una métrica en validación no es un resultado en producción.

### Modo 3 — Revisar un texto o guion
Para "revisa mi pitch", "¿suena a negocio?", "mejora esta lámina". Devolver:

- El texto reescrito en lenguaje de negocio.
- Lista breve de cambios: jerga técnica sin traducir, siglas sin explicar, afirmaciones sin respaldo, cifras sin línea base, frases que no llevan a una decisión.
- Verificar el arco **negocio → modelo → negocio**: abre con el problema del banco, cierra con la decisión que se pide.

### Modo 4 — Ensayo de preguntas del jurado
Para "hazme preguntas", "simula al jurado", "quiz de términos". Hacer **una pregunta por vez**, esperar la respuesta y luego dar: qué estuvo bien, qué faltó y una respuesta modelo de 2–3 frases. Mezclar perfiles: jurado de negocio (valor, viabilidad, riesgo, cliente) y jurado de analítica (target, fuga de información, validación, desbalanceo). Subir la dificultad si responde bien. Para quiz de vocabulario: 5 preguntas, alternando "define" y "úsalo en una frase del pitch".

### Modo 5 — Glosario del caso
Para "arma el glosario", o al recibir la consigna, un documento o la lista de columnas. Extraer los términos de negocio que aparezcan, definirlos en una línea cada uno con su relación con los datos, y separar los que tienen definición oficial de los que están `[POR CONFIRMAR]`. Para el significado de cada columna de una base, usar la skill `diccionario-campos`; para armar las láminas, `bcp-presentaciones`.

## Glosario base

Punto de partida, no lista cerrada: cualquier otro término de negocio o banca se explica con el mismo formato.

### Factoring
| Término | En simple |
|---|---|
| Factoring | Una empresa cede al banco sus facturas por cobrar y recibe el dinero hoy, con un descuento, en vez de esperar a que su cliente pague. |
| Proveedor / cedente | La empresa que vendió, emitió la factura y pide el adelanto. Es el cliente del factoring. |
| Pagador / deudor / adquirente | La empresa que compró y debe pagar la factura al vencimiento. |
| Factor | La entidad (aquí, el banco) que adelanta el dinero y luego cobra la factura. |
| Tasa de descuento | El precio del adelanto: lo que el banco cobra por dar el dinero antes. A más plazo o más riesgo, mayor descuento. |
| Monto adelantado / desembolso | Lo que recibe el proveedor: valor de la factura menos descuento y comisiones. |
| Con recurso / sin recurso | Con recurso: si el pagador no paga, el banco puede cobrarle al proveedor. Sin recurso: el banco asume ese riesgo. |
| Confirming / factoring de proveedores | Lo origina la empresa grande que paga: el banco ofrece a sus proveedores cobrar antes. El riesgo se mira sobre el pagador. |
| Factura negociable | Factura que puede transferirse a un tercero para financiarse. En Perú se registra en CAVALI `[detalles legales: confirmar]`. |
| Conformidad | Aceptación de la factura por parte del pagador; sin ella la factura es más difícil de financiar. |
| Línea de factoring | Monto máximo que el banco aprueba a una empresa para operar factoring. |
| Plazo / vencimiento | Días entre el adelanto y la fecha en que paga el deudor. |

Fórmula ilustrativa (simplificada): `descuento ≈ monto de la factura × tasa anual × días / 360`.

### Finanzas de la empresa cliente
| Término | En simple |
|---|---|
| Liquidez | Tener efectivo disponible para pagar lo de hoy (planilla, proveedores). |
| Capital de trabajo | Dinero que la empresa necesita para operar el día a día mientras espera cobrar. |
| Cuentas por cobrar | Ventas ya hechas que todavía no se cobran. Es la materia prima del factoring. |
| Días de cobro | Cuánto tarda en promedio la empresa en cobrar a sus clientes. Más días, más necesidad de factoring. |
| Ciclo de caja | Tiempo entre que la empresa paga a sus proveedores y cobra a sus clientes. |
| Pyme / segmento | Grupo de empresas según tamaño (ventas, deuda). Los cortes exactos del BCP: `[POR CONFIRMAR]` con la consigna. |
| RUC / CIIU | Identificador tributario de la empresa / código de su actividad económica (rubro). |

### Comercial
| Término | En simple |
|---|---|
| Lead | Empresa o contacto con posible interés que todavía no ha contratado. |
| Prospecto | Empresa que el banco considera candidata a ofrecerle el producto. |
| Conversión / tasa de conversión | Que el lead termine contratando / porcentaje de contactados que contratan. |
| Embudo (funnel) | Etapas de la venta: base → contactados → interesados → aprobados → desembolsados. En cada una se pierde gente. |
| Propensión | Probabilidad estimada de que una empresa tome el producto. Es lo que suele predecir el modelo. |
| Priorización | Ordenar a quién contactar primero, porque no alcanza para contactar a todos. |
| Capacidad comercial | Cuántas empresas puede atender el equipo de ventas en un periodo. Suele ser la restricción. |
| Ejecutivo / funcionario de negocios | Persona del banco que gestiona y visita a las empresas. |
| Cartera | Conjunto de clientes (o de créditos) asignados a un ejecutivo o al banco. |
| Campaña | Acción comercial dirigida a una lista de empresas en un periodo. |
| Venta cruzada (cross-sell) | Ofrecer otro producto a quien ya es cliente. |
| Principalidad | Qué tanto el cliente usa a este banco como su banco principal. |
| Participación de billetera (share of wallet) | Qué parte del negocio financiero del cliente está en este banco y cuánto en otros. |
| Ticket promedio | Monto promedio por operación o por cliente. |
| "Convertir más" / "Habilitar más" | Líneas de crecimiento del reto: mejorar la conversión de la base actual / ampliar la base con nuevos leads. Significado exacto: `[POR CONFIRMAR]` con la consigna. |

### Riesgo
| Término | En simple |
|---|---|
| Riesgo de crédito | Posibilidad de que no le paguen al banco. |
| Default / incumplimiento | No pagar según lo pactado; la definición exacta (días de atraso) depende de los datos. |
| Mora | Deuda con atraso en el pago. |
| PD, LGD, EAD | Probabilidad de incumplir, porcentaje que se pierde si incumple, monto expuesto. |
| Pérdida esperada | `PD × LGD × EAD`: lo que el banco espera perder en promedio. |
| Provisiones | Dinero que el banco aparta para cubrir pérdidas esperadas; reduce su utilidad. |
| Clasificación SBS del deudor | Categorías del regulador: Normal, CPP (con problemas potenciales), Deficiente, Dudoso, Pérdida. |
| RCC | Reporte de la SBS con las deudas de una empresa en todo el sistema financiero. |
| SBS / SUNAT | Regulador de bancos / administración tributaria. |
| Apetito de riesgo | Cuánto riesgo está dispuesto a aceptar el banco para crecer. |

### Rentabilidad y caso de negocio
| Término | En simple |
|---|---|
| Margen financiero / spread | Diferencia entre lo que el banco cobra por prestar y lo que le cuesta conseguir ese dinero. |
| Costo de fondeo | Lo que le cuesta al banco el dinero que presta. |
| Comisión | Ingreso por el servicio, aparte de los intereses. |
| Rentabilidad ajustada por riesgo | Ganancia después de descontar la pérdida esperada. |
| Valor esperado | `probabilidad × monto × margen`: cuánto vale en promedio contactar a una empresa. |
| Línea base | Cómo están hoy las cosas sin la solución; sin ella no se puede hablar de mejora. |
| Incremental / uplift | Lo que se gana **adicional** gracias a la solución frente a la línea base. |
| Piloto y grupo de control | Prueba pequeña comparando a quienes reciben la solución con quienes no. |
| KPI | Indicador con el que se mide si la propuesta funciona. |
| ROI / costo-beneficio | Cuánto se gana por cada sol invertido. |
| Supuestos y sensibilidad | Lo que se asumió y cómo cambia el resultado si el supuesto falla. |
| Escalabilidad / viabilidad | Si la solución puede crecer y si el banco puede realmente implementarla. |

## Puente técnico → negocio

| Lo técnico | Cómo decirlo |
|---|---|
| "Gini de 0,60" | "El modelo ordena bien: los mejores candidatos quedan arriba de la lista." |
| "Lift de 3 en el primer decil" | "En el 10 % mejor puntuado hay tres veces más conversiones que al contactar al azar." |
| "Recall del 70 % contactando al 20 %" | "Contactando solo a 1 de cada 5 empresas capturamos 7 de cada 10 oportunidades." |
| "Precision del 30 %" | "De cada 10 visitas que recomendamos, 3 terminan en venta." |
| "Falso positivo / falso negativo" | "Visita que no rinde / oportunidad que dejamos pasar." |
| "Importancia de variables / SHAP" | "Las señales que mejor distinguen a una empresa lista para factoring." |
| "Clases desbalanceadas" | "Las empresas que convierten son pocas; por eso importa saber encontrarlas." |
| "Sin sobreajuste; validado fuera de muestra" | "Lo probamos con empresas que el modelo nunca vio y mantiene su desempeño." |
| "Optimización con restricciones" | "La mejor lista de contacto posible respetando la capacidad del equipo y los límites del banco." |
| "Umbral de decisión" | "El punto de corte: desde qué puntaje vale la pena contactar." |
| "Fuga de información" | "Usar datos que en la vida real aún no existirían al momento de decidir." |

Los números de esta tabla son ejemplos hipotéticos; usar siempre los del equipo.

## Frases y verbos del registro de negocio

- **Verbos:** priorizar, capturar valor, habilitar, convertir, profundizar la relación, escalar, mitigar, rentabilizar, focalizar.
- **Plantilla de valor:** "Para [quién] que [problema], nuestra solución [qué hace] y logra [resultado medible]."
- **Plantilla de hallazgo:** "[Dato] → por eso [consecuencia para el banco] → proponemos [acción]."
- **Plantilla de impacto:** "Con la misma capacidad comercial, pasamos de [línea base] a [resultado], un incremento de [X] `[supuestos]`."
- **Evitar:** "el modelo predice bien" (¿cuánto y frente a qué?), "es muy preciso" (sin cifra), "revolucionario", promesas sin rango ni supuesto, y nombres de algoritmos como argumento principal.