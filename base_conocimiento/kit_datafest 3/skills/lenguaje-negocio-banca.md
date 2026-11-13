# Lenguaje de negocio y banca (Data Fest BCP · factoring)

Documento de consulta del equipo MeowWo. Sirve para **entender** el vocabulario de negocio y banca y para **hablar** como lo haría alguien del banco al exponer.

> **Importante**
> - La consigna oficial manda: si el material del reto define un término, esa definición reemplaza a la de este documento.
> - Lo marcado como `[POR CONFIRMAR]` no está verificado: contrastarlo con la consigna o con el banco.
> - Todos los números de los ejemplos son hipotéticos. Usar siempre los del equipo.

## Cómo usarlo con Copilot

Adjuntar este archivo en el chat (`#file`) y pedir una de estas cosas de forma explícita:

| Qué necesito | Qué escribir |
|---|---|
| Entender un término | "Según este archivo, explícame qué es [término] con el formato de la sección 'Cómo explicar un término'." |
| Pasar un resultado a negocio | "Traduce a lenguaje de negocio: [métrica o resultado]. Dame versión de negocio, título de lámina y respaldo técnico." |
| Pulir un texto | "Revisa este texto con las reglas de la sección 'Reglas de redacción' y reescríbelo: [texto]." |
| Practicar | "Hazme una pregunta de jurado por vez sobre nuestra solución; espera mi respuesta y corrígeme." |
| Glosario del caso | "Extrae los términos de negocio de esta consigna y defínelos en una línea: [texto]." |

## Cómo explicar un término

1. **En simple:** una frase que entendería alguien sin formación en finanzas.
2. **En el caso de factoring:** ejemplo con una pyme, una factura y el banco.
3. **Por qué le importa al banco:** qué decisión o qué dinero mueve.
4. **Cómo aparece en los datos o el modelo:** columna, target, métrica o restricción.
5. **Cómo decirlo ante el jurado:** una frase lista para usar.
6. **No confundir con:** el término vecino con el que se mezcla.

## Reglas de redacción

- Primero claro, después preciso.
- Arco **negocio → modelo → negocio**: abrir con el problema del banco, cerrar con la decisión que se pide.
- Distinguir dato, hipótesis y recomendación.
- No inventar cifras; toda mejora se compara con una línea base.
- Sin siglas sueltas. La primera vez: "Gini (qué tan bien ordena el modelo de mejor a peor candidato)".
- "Asociado con" no es "causa". Una métrica en validación no es un resultado en producción.
- Primera persona del plural ("proponemos"), frases cortas, en positivo, nada alarmista sobre clientes o el banco.

## Glosario

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
| Factura negociable | Factura que puede transferirse a un tercero para financiarse. En Perú se registra en CAVALI `[detalles legales: POR CONFIRMAR]`. |
| Conformidad | Aceptación de la factura por parte del pagador; sin ella la factura es más difícil de financiar. |
| Línea de factoring | Monto máximo que el banco aprueba a una empresa para operar factoring. |
| Plazo / vencimiento | Días entre el adelanto y la fecha en que paga el deudor. |

Fórmula ilustrativa (simplificada): `descuento ≈ monto de la factura × tasa anual × días / 360`

### Finanzas de la empresa cliente

| Término | En simple |
|---|---|
| Liquidez | Tener efectivo disponible para pagar lo de hoy (planilla, proveedores). |
| Capital de trabajo | Dinero que la empresa necesita para operar el día a día mientras espera cobrar. |
| Cuentas por cobrar | Ventas ya hechas que todavía no se cobran. Es la materia prima del factoring. |
| Días de cobro | Cuánto tarda en promedio la empresa en cobrar a sus clientes. Más días, más necesidad de factoring. |
| Ciclo de caja | Tiempo entre que la empresa paga a sus proveedores y cobra a sus clientes. |
| Pyme / segmento | Grupo de empresas según tamaño (ventas, deuda). Cortes exactos del BCP: `[POR CONFIRMAR]`. |
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
| "Convertir más" / "Habilitar más" | Líneas de crecimiento del reto: mejorar la conversión de la base actual / ampliar la base con nuevos leads. Significado exacto: `[POR CONFIRMAR]`. |

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

## Frases y verbos del registro de negocio

- **Verbos:** priorizar, capturar valor, habilitar, convertir, profundizar la relación, escalar, mitigar, rentabilizar, focalizar.
- **Plantilla de valor:** "Para [quién] que [problema], nuestra solución [qué hace] y logra [resultado medible]."
- **Plantilla de hallazgo:** "[Dato] → por eso [consecuencia para el banco] → proponemos [acción]."
- **Plantilla de impacto:** "Con la misma capacidad comercial, pasamos de [línea base] a [resultado], un incremento de [X] `[supuestos]`."
- **Evitar:** "el modelo predice bien" (¿cuánto y frente a qué?), "es muy preciso" (sin cifra), "revolucionario", promesas sin rango ni supuesto, y nombres de algoritmos como argumento principal.

## Preguntas de jurado para ensayar

**Negocio**
- ¿Qué problema del banco resuelven y cuánto vale?
- ¿Por qué una pyme elegiría factoring en vez de otro crédito?
- ¿Cómo usaría esto un ejecutivo de negocios el lunes por la mañana?
- ¿Cuál es su línea base y de dónde sale el incremento que prometen?
- ¿Qué riesgo asume el banco con las empresas que recomiendan?
- ¿Qué necesitarían para llevarlo a un piloto?

**Analítica**
- ¿Cuál es su variable objetivo y cómo la definieron?
- ¿Cómo se aseguraron de que no hay fuga de información?
- ¿Por qué eligieron esa métrica y ese modelo?
- ¿Cómo trataron el desbalanceo de clases?
- ¿Qué tan distinto es el desempeño entre entrenamiento y validación?
- ¿Cómo conectaron las predicciones con las restricciones del reto?
