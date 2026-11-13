# 20 · ¿Un modelo o varios? ¿Los datos van juntos o separados?

**Quién:** Sophia (decide) + Kath (prepara los datos según la decisión).
**Código:** `extra/uno_o_varios.py` (global vs uno por grupo) y `extra/mas_modelos.py` (varios en paralelo + ensamble).

Hay **5 formas** de usar "más de un modelo". Se confunden mucho; cada una responde a una pregunta distinta.

| Forma | Pregunta que responde | ¿La usamos siempre? |
|---|---|---|
| **1. Varios en paralelo para comparar** | ¿cuál modelo es mejor para estos datos? | **Sí, siempre** (es la validación) |
| **2. Ensamble** (combinar varios) | ¿combinar mejora al mejor solo? | Solo si gana por > 0.005 y hay tiempo |
| **3. Un modelo por segmento** | ¿cada zona/segmento se comporta tan distinto que merece su modelo? | Solo si se mide y gana |
| **4. Modelos en cadena** (dos etapas) | ¿la respuesta tiene dos partes? (quién + cuánto) | Cuando piden probabilidad y monto |
| **5. Un modelo por objetivo** | ¿hay varios targets? (varios productos, varios horizontes) | Cuando el enunciado pide varias cosas |

---

## 1. Varios en paralelo para comparar (siempre)

No es "usar 6 modelos". Es **probar** varios con la misma validación y **entregar uno**.

```
mismos datos ──┬── regla 1 variable ──┐
               ├── logística ─────────┤
               ├── random forest ─────┼──> misma validación OOF ──> elegir 1
               ├── LightGBM ──────────┤
               ├── XGBoost ───────────┤
               └── CatBoost ──────────┘
```

- Mínimo: regla + logística + un boosting (`4_modelo.py`). Si sobra tiempo: los 7 (`extra/mas_modelos.py`).
- Se elige el mejor OOF, pero **si uno más simple está a menos de 0.005, gana el simple**.

## 2. Ensamble: cuándo combinar

**Sí:** cuando los modelos se equivocan en cosas distintas (uno lineal + uno de árboles), el ensamble supera al mejor solo por > 0.005 en OOF **y** en el examen, y pueden explicarlo en una frase.

**No:** cuando uno domina claramente, cuando piden probabilidades calibradas (el ensamble por rango da posiciones, no probabilidades) o cuando no hay tiempo de validarlo.

En la práctica: el ensamble top 3 dio 0.282 OOF contra 0.295 de la logística sola. **No convino.** El ensamble no siempre gana.

Cómo se combina (en `mas_modelos.py`): se promedia el **rango** (posición 0–1) de cada modelo, no la probabilidad, porque cada modelo tiene su propia escala.

## 3. ¿Un modelo global o uno por segmento?

Esta es la pregunta de "¿los datos van en uno solo o en varios?".

### Árbol de decisión

```
¿Cada grupo tiene ≥ 100 positivos?
├── No ──> UN MODELO GLOBAL (el grupo entra como variable)
└── Sí ──> ¿El enunciado trata a los grupos como negocios distintos?
           (productos distintos, reglas distintas, datos distintos por grupo)
           ├── Sí ──> probar uno por grupo
           └── No ──> ¿uno_o_varios.py dice que por grupo gana por > 0.01?
                      ├── Sí ──> uno por grupo (y los grupos chicos usan el global)
                      └── No ──> UN MODELO GLOBAL
```

### Por qué el global suele ganar

- **Más datos por modelo.** Un modelo por zona en ORIENTE aprende de 54 positivos; el global, de 921.
- **Lo común se aprende una sola vez.** "Más facturación → más factoring" vale en todas las zonas.
- **La diferencia entre zonas ya entra**, porque `zona` es una variable del modelo global.
- **Un solo modelo** que explicar, validar y mantener.

### Lo que dio en la práctica (`python extra/uno_o_varios.py`)

| | Gini examen | Gini dentro de zona (examen) |
|---|---|---|
| **Un modelo global** | **0.292** | **0.292** |
| Uno por zona (LIMA, NORTE y SUR; CENTRO y ORIENTE usan el global) | 0.279 | 0.277 |
| Uno por segmento | 0.286 | 0.281 |

**El global gana.** Ojo con la columna "dentro de zona": como el reto reparte cupos por zona, lo que importa es ordenar bien a las empresas **de la misma zona**. Esa es la métrica correcta para esta decisión.

### Cuándo SÍ conviene separar

- Los grupos tienen **variables distintas**. Ejemplo: personas y empresas, donde una tiene RUC y facturas y la otra no.
- El comportamiento es **opuesto** entre grupos. Ejemplo: una variable sube la probabilidad en un segmento y la baja en otro, y no hay forma simple de que el modelo lo vea.
- El enunciado lo pide, o el negocio lo opera por separado (equipos y presupuestos distintos).
- Cada grupo tiene **muchos** positivos (cientos o miles).

Alternativa intermedia: un **global con variables de interacción** (ej. `ventas × es_LIMA`), o LightGBM, que encuentra interacciones solo.

## 4. Modelos en cadena (dos etapas)

Cuando la respuesta tiene dos partes:

```
Etapa 1: ¿convierte?        clasificador con todas las empresas         -> P(convierte)
Etapa 2: ¿cuánto, si sí?    regresor SOLO con las que convirtieron      -> monto si convierte
Resultado:                  valor esperado = P(convierte) × monto        -> priorizar
```

- Está en `5_entregar.py` (etapa 2 simple: la mediana del rubro).
- Por qué no un solo regresor sobre todos: el 80% tiene monto 0, así que el regresor aprende "casi siempre 0" y ordena mal.

## 5. Un modelo por objetivo

| El enunciado pide… | Modelos |
|---|---|
| propensión a factoring **y** a leasing | dos clasificadores (uno por producto), con la misma tabla de variables |
| a 1, 3 y 6 meses | tres clasificadores (uno por horizonte); comprobar que la probabilidad a 6 meses sea ≥ que a 3 |
| qué producto ofrecer primero | un binario por producto y se ofrece el de mayor valor esperado |

La tabla de variables es **una sola** (Kath la arma una vez). Lo que cambia es el target.

## ¿Paralelo en la computadora? (velocidad)

"En paralelo" también puede significar usar varios núcleos:
- `n_jobs=-1` en Random Forest y XGBoost usa todos los núcleos.
- LightGBM ya usa varios núcleos por defecto.
- En el evento, el tiempo lo come la **validación** (5 pliegues × N modelos). Si no alcanza: usar `rapido`, bajar a 3 pliegues o muestrear 50% de las filas **solo para comparar** y entrenar el elegido con todo.

## Resumen para decir al jurado

*"Comparamos 7 modelos en paralelo con la misma validación y elegimos uno. Probamos un modelo por zona contra uno global midiendo el orden dentro de cada zona, que es lo que importa con cupos. Ganó el global (0.292 vs 0.279): con pocos positivos por zona, separar los datos le quita información a cada modelo. Para el monto usamos dos etapas, probabilidad × monto esperado, porque el 80% de las empresas no convierte."*
