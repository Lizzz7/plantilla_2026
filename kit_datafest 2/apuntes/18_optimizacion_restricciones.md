# 18 · Priorizar "el 10%" con restricciones

**Quién:** Liz. **Código:** `scripts/optimizacion/priorizar_restricciones.py`.

```
python optimizacion/priorizar_restricciones.py          # usa salidas/prob.parquet
python optimizacion/priorizar_restricciones.py demo     # inventa una columna de ejecutivo para practicar
```

Instalar: `pip install "pulp<3"` (la versión 2.x trae el solver adentro). Si PuLP no está, el script usa `scipy.optimize.milp`, que viene con scikit-learn, y da **el mismo resultado** (comprobado).

## La idea

El modelo da una probabilidad por empresa. El negocio no puede llamar a todas: tiene una **capacidad** (10%, 500 llamadas) y **reglas** (cupos por zona, no concentrar en un rubro, presupuesto, carga por ejecutivo). Priorizar = elegir el grupo que **maximiza el valor** respetando todas las reglas.

**Valor de cada empresa** = probabilidad × monto si convierte (= soles esperados). Si piden solo "a quién llamar" sin montos, el valor es la probabilidad (`OBJETIVO = "prob"`).

## Las restricciones típicas y cómo se escriben

| Regla del negocio | Ajuste | En matemáticas |
|---|---|---|
| "Solo podemos contactar al 10%" | `CAPACIDAD = 0.10` | Σ xᵢ ≤ K |
| "Respeten los cupos por zona" | `CUPOS_ZONA = "proporcional"` o `A.CUPOS` | Σ_{zona z} xᵢ ≤ cupo_z |
| "Al menos 5 por rubro" (diversificar) | `MIN_POR_RUBRO = 5` | Σ_{rubro r} xᵢ ≥ 5 |
| "Ningún rubro más del 30%" (concentración) | `MAX_POR_RUBRO = 0.30` | Σ_{rubro r} xᵢ ≤ 0.3·K |
| "El monto total no pase de S/ X" (presupuesto / apetito de riesgo) | `PRESUPUESTO` | Σ montoᵢ·xᵢ ≤ X |
| "Cada ejecutivo atiende máximo 15" | `MAX_POR_EJECUTIVO = 15` | Σ_{ejecutivo e} xᵢ ≤ 15 |
| "No vale llamar si la prob < 5%" | `PROB_MINIMA = 0.05` | se sacan antes |
| "Corporativos no" / "ya clientes no" | `EXCLUIR = "segmento == 'CORPORATIVO'"` | se sacan antes |

Si una regla no aplica, se pone `None`.

## Dos formas de resolver

**A) Greedy (codicioso):** ordenar por valor; primero asegurar los mínimos por rubro con los mejores de cada uno; después ir tomando de arriba hacia abajo mientras no se rompa ninguna regla.
- ✅ Se explica en una frase. Rapidísimo.
- ❌ Con presupuesto (montos distintos) no es óptimo: puede gastar el presupuesto en pocas empresas caras.

**B) Programación entera (PuLP / scipy):** se escribe el problema tal cual (maximizar Σ valorᵢ·xᵢ con xᵢ ∈ {0,1} sujeto a las reglas) y el solver encuentra el **óptimo**.
- ✅ Óptimo garantizado; avisa si las reglas son **imposibles** de cumplir juntas.
- ❌ Hay que instalar algo; explicarlo toma 2 frases más.

**Cuál entregar:** si empatan (diferencia < 0.1%), greedy. Si la entera gana, la entera, y dicen cuánto ganó.

### Resultado en la práctica (K = 500, 5 zonas, presupuesto 70%, 60 ejecutivos)

| | Top K sin reglas | Greedy | Entera |
|---|---|---|---|
| Empresas | 500 | 349 | 372 |
| Valor esperado | S/ 6.88 M | S/ 5.16 M | **S/ 5.32 M (+3.2%)** |
| Cumple todo | ❌ | ✅ | ✅ |
| % que convierte (real) | 38.6% | 40.7% | 40.9% |

Lecturas que valen puntos:
- El "top K sin reglas" es el **techo**: la diferencia con él es el **precio de las reglas** (aquí S/ 1.56 M). Eso es información para el negocio: "el tope de presupuesto nos cuesta X soles esperados".
- Con presupuesto, el greedy llena menos cupos (349) porque se gasta el presupuesto en empresas de monto alto; la entera encuentra combinaciones más eficientes (372).
- Ojo: el "monto real capturado" puede ser mayor en el greedy aunque el valor *esperado* sea menor. Eso es ruido de una sola realización; se decide con el valor esperado, que es lo que conocemos al momento de elegir.

## Cupos que sumen exacto: el método del resto mayor

Si 500 llamadas se reparten 49.2% / 18% / 18% / 9.8% / 5% → 246.0 / 90.0 / 90.0 / 49.0 / 25.0. Cuando salen decimales, se toma la parte entera y se le suma 1 a las zonas con mayor resto hasta completar K. Así la suma es exacta y nadie discute.

## Si el solver dice "Infeasible" (imposible)

Las reglas chocan. Ejemplos: mínimo 5 por rubro × 13 rubros = 65, pero el presupuesto alcanza para 40; o cupo de ORIENTE = 25 pero solo hay 10 elegibles allí. Qué hacer:
1. Relajar la regla menos importante (preguntar cuál es "dura" y cuál es "deseable").
2. Convertir la regla en penalidad (avanzado: restar del objetivo por cada unidad que falte).
3. Reportarlo: "con estas reglas no hay solución; relajando X obtenemos Y". **Eso también es un hallazgo.**

## Otras formas de "priorizar" que pueden pedir

| Piden | Qué hacer |
|---|---|
| "el 10% con mayor probabilidad" | `nlargest(K, "prob")`, sin más |
| "maximizar ganancia neta" | valor = prob × margen − costo de contacto; contactar solo si valor > 0 |
| "a quién llamar primero" (orden) | ordenar por valor; entregar el rango |
| "maximizar conversiones por ejecutivo" | restricción por ejecutivo + objetivo = prob |
| "quién responde **por** la llamada" (uplift) | necesita datos de tratados vs no tratados; si no hay, decirlo |
