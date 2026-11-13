# El flujo completo y los 10 conceptos que todas deben saber

## 1. Del archivo al CSV

```
datos/  →  1 leer y limpiar  →  2 revisar  →  3 variables  →  4 modelo  →  5 entregar  →  submission.csv
           (Hellen)             (Nat)         (Kath)          (Sophia)      (Liz)
           tablas limpias       ¿todo existe?  entrena.parquet  prob.parquet  CSV + controles
                                tasa base      predice.parquet
```

Cada paso deja su archivo en `salidas/`. Si el paso 4 falla, no hay que volver a leer el Excel: se corre desde el 4.

## 2. Los 10 conceptos

| # | Concepto | En una frase | Ejemplo |
| --- | --- | --- | --- |
| 1 | Fecha de corte | El día de decidir: variables con datos ANTES, target DESPUÉS | 2025-07-01 |
| 2 | Horizonte | Cuánto tiempo después del corte se mira el target | 6 meses (jul–dic) |
| 3 | Target | Lo que se predice: 1 si la empresa tomó factoring (no anulado, en el BCP) en la ventana | 19.9% de las empresas |
| 4 | Entidad / grano | Qué es una fila. El modelo usa 1 fila por empresa | facturas: 16 filas por empresa → se resumen |
| 5 | Variable (feature) | Un número o categoría que describe a la empresa el día del corte | ventas, n° de facturas de los últimos 3 meses |
| 6 | Fuga | Usar información que no existía el día de decidir | una columna tomada hoy que ya incluye el target |
| 7 | Corte anterior | Corte − horizonte: su target ya ocurrió, así que sirve para entrenar | 2025-01-01 |
| 8 | Validación fuera de tiempo | Entrenar con el corte anterior, examinar con el actual | como evaluará el banco |
| 9 | Gini | Qué tan bien ORDENA el modelo: 0 azar, 1 perfecto | 0.29 (la regla simple, 0.26) |
| 10 | Valor esperado | Probabilidad × monto si convierte | a quién llamar primero |

## 3. El tiempo, dibujado

```
2024-01 ............ 2025-01 ........ 2025-07 ........ 2026-01
   │← historia (12m) →│← target ENTRENA →│
                      corte anterior
              │← historia (12m) →│← target PREDICE →│
                                 corte actual
```

- Las variables de cada tabla miran solo su "historia" (a la izquierda de su corte).
- El modelo aprende en el corte anterior (su target ya se conoce) y se aplica en el actual.
- En el evento, el target del corte actual **es el futuro**: no está en los datos. Lo evalúa el banco.

## 4. Los relevos del equipo

| Termina | Entrega | Recibe | Qué revisa al recibir |
| --- | --- | --- | --- |
| Hellen | tablas limpias + lista de columnas | Nat | nombres para `ajustes.py` |
| Nat | `ajustes.py` + paso 2 en OK | Kath | que la tasa base tenga sentido |
| Kath | `entrena.parquet`, `predice.parquet` | Sophia | ninguna alerta de fuga sin decidir |
| Sophia | `prob.parquet` + Gini | Liz | que el modelo le gane a la regla |
| Liz | `submission.csv` + controles OK | Nat | formato del enunciado, validador oficial |

## 5. Lo que separa a un equipo que "corrió un script" de uno que entiende sus datos

1. Saber explicar por qué cada columna salió o se quedó.
2. Poder demostrar que ninguna variable ve el futuro.
3. Comparar contra una línea base (la regla simple).
4. Traducir el Gini a negocio ("2 veces más conversiones con las mismas llamadas").
5. Tener la entrega validada temprano (primer submission antes de las 22:00) y mejorar después.
