# Guía de negocio, banca y lenguaje comercial — Datafest BCP 2026 (caso factoring)

> Para qué sirve: entender el negocio del caso, hablar como alguien del banco y defender la solución
> ante el jurado. Lo marcado `[POR CONFIRMAR]` depende de la consigna oficial del evento: **la consigna
> manda** sobre esta guía. Todos los números de ejemplo son **hipotéticos**; en la exposición se usan
> solo cifras calculadas con los datos del reto.

---

## 0. Lo esencial en 60 segundos

- **Pregunta central del caso:** ¿a qué empresas debería contactar primero el banco para hacer más
  eficiente el crecimiento de su negocio de factoring?
- **No es "contactar a todas":** la fuerza de ventas es limitada. Hay que **identificar, valorar y
  priorizar**.
- **El jurado quiere tres respuestas:**
  - **¿Cuánto?** Cuánto se amplía la base de oportunidades y qué potencial representa.
  - **¿Quiénes?** Qué empresas contactar primero (Top-K según capacidad comercial).
  - **¿Por qué?** Qué señales en los datos explican esa selección.
- **Arco de la exposición:** negocio → modelo → negocio. Abrir con el problema del banco, explicar el
  método en simple, cerrar con la decisión y el impacto.
- **Frase de cierre modelo:** «Ampliamos la base **[X] veces**. Dentro de ella, priorizamos **[K]
  empresas** porque presentan **[señales]** y concentran **[métrica de valor o conversión]**. Esta
  selección respeta la capacidad comercial y se sustenta en **[método y evidencia]**.»

---

## 1. Cómo funciona el factoring

**En simple:** una empresa vendió algo y emitió una factura que le pagarán en, por ejemplo, 60 días.
Necesita el dinero ya (para planilla, insumos). El banco le **adelanta** el dinero hoy a cambio de un
**descuento**, y luego el banco cobra la factura cuando vence.

```
 Proveedor (pyme)  --vende y emite factura-->  Pagador (empresa grande)
        |                                              |
        | cede la factura                              | paga al vencimiento
        v                                              v
      BANCO (factor)  --adelanta hoy (factura - descuento)--> Proveedor
```

**Ejemplo hipotético:** factura de S/ 10,000 a 60 días. El banco adelanta S/ 9,800 hoy. Los S/ 200 de
diferencia son el ingreso del banco (descuento + comisiones) por dar el dinero antes y asumir el riesgo.

Fórmula simplificada: `descuento ≈ monto × tasa anual × días / 360`.

### Por qué le sirve a cada uno

| Actor | Qué gana |
|---|---|
| Proveedor (pyme) | Liquidez inmediata sin esperar el cobro; no se endeuda con un préstamo tradicional. |
| Pagador (empresa grande) | Sus proveedores están más sanos y le pueden dar mejores plazos. |
| Banco | Ingreso por descuento y comisiones, nuevos clientes y relación con toda la cadena de proveedores. Riesgo acotado: a menudo se mira la solidez del **pagador**. |

### Vocabulario del factoring

| Término | En simple |
|---|---|
| **Factoring** | Ceder facturas por cobrar al banco y recibir el dinero hoy, con descuento. |
| **Proveedor / cedente** | Empresa que vendió, emitió la factura y pide el adelanto. Es el cliente del factoring. |
| **Pagador / deudor / aceptante / girador** | Empresa que compró y paga la factura al vencimiento. Confirmar cómo lo llaman los datos `[POR CONFIRMAR]`. |
| **Factor** | Quien adelanta el dinero y cobra la factura (aquí, el BCP). |
| **Tasa de descuento** | Precio del adelanto. A más plazo o más riesgo, mayor descuento. |
| **Desembolso / monto adelantado** | Lo que recibe el proveedor: factura menos descuento y comisiones. |
| **Con recurso / sin recurso** | Con recurso: si el pagador no paga, el banco cobra al proveedor. Sin recurso: el banco asume ese riesgo. |
| **Confirming (factoring de proveedores)** | Lo impulsa la empresa grande pagadora: el banco ofrece a sus proveedores cobrar antes. |
| **Factura negociable** | Factura que puede transferirse para financiarse. En Perú se registra en CAVALI `[detalles legales: confirmar]`. |
| **Conformidad** | Aceptación de la factura por el pagador; sin ella es más difícil financiarla. |
| **Línea de factoring** | Monto máximo aprobado a una empresa para operar factoring. |
| **Plazo / vencimiento** | Días entre el adelanto y el pago del deudor. |
| **MIPE / PYME** | Micro y pequeña / pequeña y mediana empresa. Cortes exactos del BCP `[POR CONFIRMAR]`. |
| **SPI** | Sistema mencionado como fuente de operaciones observables. Alcance `[POR CONFIRMAR]`. |

---

## 2. El problema de negocio

- El banco quiere **crecer en factoring**, pero cada ejecutivo atiende un número limitado de empresas.
- Contactar a la empresa equivocada = tiempo perdido. No contactar a la correcta = oportunidad perdida
  (quizá se la lleva otro banco).
- Dos líneas de crecimiento mencionadas en el material:
  - **Convertir más:** mejorar la conversión dentro de la base actual (se mencionó un ~10 % de clientes
    PYME con el producto o relación) `[POR CONFIRMAR]`.
  - **Habilitar más:** ampliar la base con nuevas empresas (leads) que hoy no se trabajan.
- **Nuestra propuesta en una línea:** con la misma capacidad comercial, contactar primero a las empresas
  con mayor **valor esperado** (probabilidad de convertir × valor si convierten).

### Lo que NO se debe confundir (el jurado puede preguntarlo)

- Empresa **identificada** ≠ empresa **elegible** ≠ empresa **contactable**.
- **Probabilidad estimada** ≠ conversión garantizada.
- **Monto transado** ≠ monto **factorizable**.
- El historial de factoring observado **no** es todo el mercado (hay empresas que hacen factoring con otros bancos).
- **Más volumen** no siempre es **más rentabilidad** (hay que mirar margen y riesgo).
- **Asociado con** ≠ **causa**.

---

## 3. Finanzas de la empresa cliente (para entender por qué necesita factoring)

| Término | En simple | Señal en los datos (posible) |
|---|---|---|
| **Liquidez** | Tener efectivo para pagar lo de hoy. | Saldos, uso de líneas. |
| **Capital de trabajo** | Dinero para operar mientras espera cobrar. | Ventas vs. plazos de cobro. |
| **Cuentas por cobrar** | Ventas hechas aún no cobradas. Es la "materia prima" del factoring. | Facturas emitidas pendientes. |
| **Días de cobro** | Cuánto tarda en cobrar. Más días → más necesidad de factoring. | Plazo promedio de facturas. |
| **Ciclo de caja** | Tiempo entre pagar a proveedores y cobrar a clientes. | — |
| **Concentración de clientes** | Qué tanto depende de pocos pagadores. Si vende a empresas grandes y sólidas, es buena candidata. | Pagadores distintos, % del principal. |
| **Estacionalidad** | Ventas que suben en ciertos meses → picos de necesidad de liquidez. | Facturación por mes. |
| **RUC / CIIU** | Identificador tributario / código de actividad (rubro). | Llave y rubro. |

**Perfil típico (hipótesis a validar con datos):** empresa que factura con frecuencia, a pagadores
grandes, con plazos largos de cobro, en crecimiento y con buen comportamiento de pago.

---

## 4. Vocabulario comercial

| Término | En simple |
|---|---|
| **Lead** | Empresa o contacto con posible interés que aún no contrata. |
| **Prospecto** | Empresa que el banco considera candidata para ofrecerle el producto. |
| **Habilitar** | Identificar con datos qué empresas del universo conviene trabajar. |
| **Conversión / tasa de conversión** | Que el lead contrate / % de contactados que contratan. Definición exacta del reto `[POR CONFIRMAR]`. |
| **Embudo (funnel)** | Base → elegibles → contactados → interesados → aprobados → desembolsados. En cada etapa se pierde gente. |
| **Propensión** | Probabilidad estimada de que una empresa tome el producto en un horizonte. Lo que predice el modelo. |
| **Priorización / ranking** | Ordenar a quién contactar primero. |
| **Top-K** | Las primeras K empresas del ranking, según capacidad de contacto. |
| **Capacidad comercial** | Cuántas empresas puede atender ventas en un periodo. Es **la** restricción. |
| **Ejecutivo / funcionario de negocios** | Persona del banco que gestiona y visita empresas. |
| **Cartera** | Conjunto de clientes asignados a un ejecutivo o al banco. |
| **Campaña** | Acción comercial a una lista de empresas en un periodo. |
| **Venta cruzada (cross-sell)** | Ofrecer otro producto a quien ya es cliente (ej. cliente de cuenta corriente → factoring). |
| **Principalidad** | Qué tanto el cliente usa al BCP como banco principal. |
| **Share of wallet** | Qué parte del negocio financiero del cliente está en el BCP vs. otros bancos. |
| **Ticket promedio** | Monto promedio por operación o cliente. |
| **Tasa base** | Conversión si se contacta al azar o como se hace hoy. Contra esto se mide la mejora. |

---

## 5. Vocabulario de riesgo

| Término | En simple |
|---|---|
| **Riesgo de crédito** | Posibilidad de que no le paguen al banco. |
| **Default / incumplimiento** | No pagar según lo pactado (definición de días de atraso según datos). |
| **Mora** | Deuda con atraso. |
| **PD / LGD / EAD** | Probabilidad de incumplir / % que se pierde si incumple / monto expuesto. |
| **Pérdida esperada** | `PD × LGD × EAD`: lo que el banco espera perder en promedio. |
| **Provisiones** | Dinero que el banco aparta para cubrir pérdidas; reduce la utilidad. |
| **Clasificación SBS** | Normal, CPP (con problemas potenciales), Deficiente, Dudoso, Pérdida. |
| **RCC** | Reporte de la SBS con las deudas de una empresa en todo el sistema financiero. |
| **SBS / SUNAT** | Regulador de bancos / administración tributaria. |
| **Apetito de riesgo** | Cuánto riesgo acepta el banco para crecer. |

**Por qué importa en el caso:** una empresa con alta propensión pero mal comportamiento de pago puede
no ser una buena recomendación. Si los datos lo permiten, mencionar que la priorización considera (o
podría considerar) el riesgo.

---

## 6. Rentabilidad y caso de negocio

| Término | En simple |
|---|---|
| **Margen financiero / spread** | Lo que el banco cobra menos lo que le cuesta el dinero. |
| **Costo de fondeo** | Lo que le cuesta al banco conseguir el dinero que presta. |
| **Comisión** | Ingreso por servicio, aparte de intereses/descuento. |
| **Valor esperado** | `probabilidad de convertir × valor si convierte` (valor = monto, margen, etc.). |
| **Rentabilidad ajustada por riesgo** | Ganancia menos pérdida esperada. |
| **Línea base** | Cómo están las cosas hoy sin la solución. Sin línea base no hay "mejora". |
| **Incremental / uplift** | Lo que se gana **adicional** gracias a la solución. |
| **Piloto y grupo de control** | Probar con una parte de empresas y comparar con otras que no reciben la solución. |
| **KPI** | Indicador para medir si la propuesta funciona. |
| **ROI / costo-beneficio** | Cuánto se gana por cada sol invertido. |
| **Supuestos y sensibilidad** | Qué asumimos y cómo cambia el resultado si el supuesto falla. |
| **Escalabilidad / viabilidad** | Si puede crecer / si el banco puede implementarla de verdad. |

### KPIs sugeridos para la propuesta

| Dimensión | Indicador | Pregunta que responde |
|---|---|---|
| Cobertura | Empresas elegibles | ¿Qué universo se puede trabajar? |
| Expansión | Nuevas empresas habilitadas y % de crecimiento | ¿Cuánto ampliamos la base? |
| Conversión | Conversiones / contactadas | ¿Qué tan efectiva es la campaña? |
| Ranking | Conversión del Top-K vs. tasa base (lift) | ¿Sirve priorizar? |
| Valor | Monto factorizado o margen esperado | ¿Qué impacto económico genera? |
| Eficiencia | Conversiones por ejecutivo o por contacto | ¿Usamos bien la capacidad? |
| Calidad predictiva | Gini, R² u otra métrica del jurado `[POR CONFIRMAR]` | ¿Qué tan bien ordena/predice? |

---

## 7. Puente técnico → negocio (cómo decir los resultados)

| Lo técnico | Cómo decirlo al jurado |
|---|---|
| "Gini de 0,60" | "El modelo ordena bien: los mejores candidatos quedan arriba de la lista." |
| "Lift de 3 en el primer decil" | "En el 10 % mejor puntuado hay tres veces más conversiones que contactando al azar." |
| "Recall 70 % contactando al 20 %" | "Contactando a 1 de cada 5 empresas capturamos 7 de cada 10 oportunidades." |
| "Precision 30 %" | "De cada 10 visitas recomendadas, 3 terminan en venta." |
| "Falso positivo / falso negativo" | "Visita que no rinde / oportunidad que dejamos pasar." |
| "Importancia de variables / SHAP" | "Las señales que mejor distinguen a una empresa lista para factoring." |
| "Clases desbalanceadas" | "Las empresas que convierten son pocas; por eso importa saber encontrarlas." |
| "Validado fuera de muestra, sin sobreajuste" | "Lo probamos con empresas que el modelo nunca vio y mantiene su desempeño." |
| "Optimización con restricciones" | "La mejor lista posible respetando la capacidad del equipo y los límites del banco." |
| "Umbral de decisión" | "Desde qué puntaje vale la pena contactar." |
| "Fuga de información (leakage)" | "Usar datos que en la vida real todavía no existirían al momento de decidir. Lo evitamos con una fecha de corte." |
| "Fecha de corte / ventana" | "Miramos el pasado hasta un día X y medimos quién convirtió después, como pasaría en la realidad." |
| "R²" | "Qué parte de la variación del monto logra explicar el modelo." |

(Cifras hipotéticas: reemplazar con las nuestras.)

**Estructura para cualquier hallazgo:** *dato → consecuencia para el banco → acción que proponemos.*
Ejemplo hipotético: "Las empresas que facturan a más de 5 pagadores distintos convierten el doble →
son prioridad para ventas → proponemos que encabecen la lista de la primera campaña."

---

## 8. Estructura del pitch (10 minutos con preguntas `[POR CONFIRMAR]`)

| # | Bloque | Tiempo aprox. | Qué decir |
|---|---|---|---|
| 1 | Problema y oportunidad | 1 min | Capacidad comercial limitada; queremos crecer en factoring de forma eficiente. |
| 2 | Datos y método (en simple) | 1.5 min | Unimos las fuentes, definimos fecha de corte, estimamos probabilidad y valor, ordenamos. |
| 3 | ¿Cuánto? | 1 min | Cuánto crece la base habilitada y su potencial. |
| 4 | ¿Quiénes? | 1 min | Top-K, segmentos/rubros que concentran el potencial; mostrar dashboard o simulador. |
| 5 | ¿Por qué? | 1 min | 3 señales principales, conectadas con hipótesis de negocio. |
| 6 | Impacto, supuestos, limitaciones, siguiente paso | 1 min | Valor esperado, qué asumimos, cómo lo mediríamos (piloto con grupo de control). |
| — | Preguntas | ~3 min | — |

**Título de cada lámina = la conclusión** (≤ 15 palabras), no el tema.
❌ "Resultados del modelo" → ✅ "Contactando al 20 % capturamos 7 de cada 10 oportunidades".

---

## 9. Frases y verbos del registro de negocio

- **Verbos:** priorizar, focalizar, habilitar, convertir, capturar valor, profundizar la relación,
  rentabilizar, escalar, mitigar.
- **Primera persona del plural, frases cortas, en positivo:** "Proponemos…", "Encontramos…", "Recomendamos…".
- **Plantilla de valor:** "Para [quién] que [problema], nuestra solución [qué hace] y logra [resultado medible]."
- **Plantilla de impacto:** "Con la misma capacidad comercial, pasamos de [línea base] a [resultado],
  un incremento de [X], bajo el supuesto de [supuesto]."
- **Cómo admitir un límite sin perder fuerza:** "Una limitación es [X]; por eso proponemos validarlo con
  un piloto de [N] empresas y grupo de control."

### Evitar

- "El modelo predice bien" (¿cuánto y frente a qué?).
- "Es muy preciso", "revolucionario", "100 % seguro".
- Nombres de algoritmos como argumento principal ("usamos XGBoost" no convence a negocio).
- Cifras sin línea base, siglas sin explicar, causalidad sin evidencia.
- Mencionar la universidad (la evaluación es ciega a la institución).

---

## 10. Preguntas probables del jurado y respuestas modelo

**Negocio**

1. **¿Por qué estas empresas y no otras?** → "Porque combinan alta probabilidad de convertir y alto
   valor esperado; las señales principales son [A, B, C], coherentes con la necesidad de liquidez."
2. **¿Cuánto dinero representa?** → "Bajo el supuesto de [monto/margen], el Top-K representa S/ [X]
   de valor esperado, frente a S/ [Y] si se contactara al azar."
3. **¿Cómo lo implementaría el banco?** → "Entregamos una lista ordenada por ejecutivo, con el motivo de
   cada recomendación; se arranca con un piloto y se mide contra un grupo de control."
4. **¿Qué pasa si la capacidad comercial cambia?** → "El ranking se mantiene; solo se mueve el corte K.
   El simulador muestra el valor capturado para cada K."
5. **¿Y el riesgo?** → "[Si se incluyó] Filtramos/penalizamos empresas con señales de mal pago. [Si no]
   Es el siguiente paso: combinar propensión con riesgo para priorizar valor ajustado por riesgo."
6. **¿Qué fue lo más sorprendente?** → Un hallazgo respaldado por datos, con su consecuencia comercial.

**Analítica**

7. **¿Cómo definieron el target?** → "Empresa que [convirtió/hizo factoring] en los [N] meses posteriores
   a la fecha de corte."
8. **¿Cómo evitaron la fuga de información?** → "Las variables solo usan información anterior a la fecha
   de corte; el resultado se mide después."
9. **¿Cómo validaron?** → "Con empresas/periodos que el modelo no vio; reportamos [métrica] en validación."
10. **Las conversiones son pocas, ¿cómo lo manejaron?** → "Evaluamos con métricas de orden (Gini/lift)
    en vez de exactitud, y [ponderación/estratificación]."
11. **¿Por qué ese modelo?** → "Por desempeño en validación, rapidez y porque permite explicar las señales;
    comparamos contra una línea base simple."
12. **¿Qué parte venía de la base de conocimiento y qué hicieron en el evento?** → Cualquiera puede ser
    elegida: todas deben saberlo.

---

## 11. Dato, hipótesis y recomendación: no mezclarlos

| Tipo | Cómo se dice | Ejemplo hipotético |
|---|---|---|
| **Dato** | "En los datos observamos…" | "El 60 % de las conversiones está en 3 rubros." |
| **Hipótesis** | "Creemos que… porque…" | "Creemos que convierten más porque venden a grandes pagadores con plazos largos." |
| **Recomendación** | "Proponemos…" | "Proponemos empezar la campaña por esos rubros." |

---

## 12. Checklist antes de exponer

- [ ] ¿Respondemos explícitamente **cuánto, quiénes y por qué**?
- [ ] ¿Cada cifra tiene **línea base** y **supuesto**?
- [ ] ¿Las cifras salen de nuestros cálculos (no de esta guía)?
- [ ] ¿Explicamos siglas la primera vez (Gini, Top-K, lift)?
- [ ] ¿Aclaramos si hablamos de **empresas, conversiones, monto o margen**?
- [ ] ¿Mencionamos limitaciones y el siguiente paso (piloto, medir)?
- [ ] ¿Todas pueden explicar el target, la fecha de corte y la fuga de información?
- [ ] ¿Cerramos con la decisión que le pedimos al banco?

---

*Nota de autoría para el INVENTARIO: documento preparado antes del evento con asistencia de una IA
distinta del Copilot del evento (Claude, de Anthropic), a partir de las notas del equipo; revisado por
el equipo MeowWo. No contiene datos del reto.*
