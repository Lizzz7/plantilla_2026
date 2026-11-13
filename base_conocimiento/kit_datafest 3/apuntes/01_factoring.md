# Factoring · el negocio detrás de los datos

## 1. Qué es

Una empresa vende a crédito: entrega hoy y su cliente (el **pagador**) le paga en 30, 60 o 90 días. Mientras tanto
necesita caja para pagar sueldos, proveedores e insumos. Con **factoring**, la empresa (el **cedente** o
**proveedor**) cede sus facturas por cobrar a una entidad financiera, que le adelanta el dinero hoy, descontando
intereses y comisiones. Al vencimiento, el banco cobra al pagador.

```
Proveedor (pyme) --vende a crédito--> Pagador (empresa grande)
      │  cede la factura                     │  paga al vencimiento
      ▼                                      ▼
   Banco  --adelanta el dinero hoy-->  Proveedor
```

- **Con recurso**: si el pagador no paga, el proveedor responde. **Sin recurso**: el riesgo lo asume el banco.
- **Factoring electrónico**: en Perú la factura electrónica (SUNAT) puede negociarse como "factura negociable"
  (marco de la Ley 29623) y se registra en una institución de compensación y liquidación (CAVALI).
- **Confirming / factoring inverso**: el pagador grande ofrece a sus proveedores adelantar sus facturas.

## 2. Por qué una empresa lo toma (qué debería predecir el modelo)

| Motivo | Señal en los datos | Variable |
| --- | --- | --- |
| Vende a crédito con plazos largos | facturas con plazo alto | promedio de `dias_plazo` |
| Factura mucho / creciendo | más facturas, monto subiendo | `fact_n`, `fact_monto`, tendencia 3m vs 12m |
| Pagadores grandes y confiables | factura a pocos pagadores sólidos | n° de pagadores, concentración |
| Ya conoce el producto | operaciones de factoring previas | `ops_n`, `ops_recencia` (en los datos de práctica es la 2.ª variable más importante) |
| Necesita caja | saldos bajando, uso alto de líneas | tendencia de saldo |
| Tamaño intermedio (pyme) | ventas anuales | `ventas_anuales` (la más importante en la práctica) |
| Rubro con capital de trabajo intenso | comercio, manufactura | `rubro_economico` (COMERCIO 25% vs 18.4% promedio) |
| Relación comercial previa | lead asignado, cliente del banco | `flag_lead_factoring` |

## 3. Cómo gana el banco

Ingreso ≈ monto financiado × tasa × plazo, menos pérdidas y costos. Por eso importa el **valor esperado**:
`probabilidad de que tome × monto que financiaría`. Una empresa con 30% y S/ 100 000 (valor 30 000) vale más que
una con 60% y S/ 20 000 (valor 12 000).

## 4. Las dos formas de crecer (si el reto las plantea)

- **Convertir más**: entre quienes ya tienen oportunidad (lead), contactar primero a quienes más probablemente
  acepten.
- **Habilitar más**: elegir a quiénes **sin** lead conviene darles uno. Es otra lista: el modelo debe ordenar bien
  dentro de ese grupo.

## 5. Vocabulario para la presentación

| Término | Significado |
| --- | --- |
| Cedente / proveedor | quien vende la factura (nuestra empresa objetivo) |
| Pagador / deudor | quien debe pagar la factura |
| Aforo / anticipo | % de la factura que el banco adelanta |
| Tasa de descuento | costo financiero del adelanto |
| Conversión | la empresa tomó factoring en la ventana del target |
| Lead | oportunidad comercial asignada a un ejecutivo |
| Capacidad comercial | cuántas empresas puede contactar la fuerza de venta |
| Cupo por zona | parte de la capacidad asignada a cada región |
