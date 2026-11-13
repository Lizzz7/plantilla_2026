# Guía de Git y GitHub para el Datafest BCP 2026 (equipo MeowWo)

> Para qué sirve: entender Git desde cero y tener a mano los comandos exactos que usaremos el
> viernes 13 y sábado 14. Al final hay una **chuleta de una página** y una sección de **errores comunes**.
> Si la oficial (`docs/GUIA_INICIO.md`, `REGLAS.md`) dice algo distinto, manda la oficial.

---

## 1. Qué es Git (en 2 minutos)

- **Git** es un programa que guarda la historia de una carpeta: cada vez que "guardas" (commit) queda
  una foto de los archivos, con autor, fecha y mensaje. Puedes ver qué cambió, quién y volver atrás.
- **GitHub** es la web donde vive una copia compartida de esa carpeta (el *remoto*). Cada integrante
  tiene una copia en su laptop (el *local*) y se sincronizan con `push` (subir) y `pull` (bajar).
- **Analogía:** el repo es un Google Doc con historial, pero cada una edita su propia copia y luego
  se juntan los cambios de forma controlada.

### Las tres zonas (lo más importante para no perderse)

```
 Carpeta de trabajo  --git add-->  Zona de preparación  --git commit-->  Historial local  --git push-->  GitHub
  (archivos que editas)            (lo que entrará al commit)            (tus commits)                  (remoto)
```

- Editar un archivo **no** lo guarda en Git. Hay que hacer `git add` y luego `git commit`.
- Hacer commit **no** lo sube. Hay que hacer `git push`.
- Lo que no está en GitHub, **para la organización no existe**. Y para el jurado solo cuenta lo que
  está en `main` al cierre.

---

## 2. Glosario

| Término | Qué es | Ejemplo |
|---|---|---|
| **Repositorio (repo)** | La carpeta del proyecto con todo su historial | `Datafest-BCP/MeowWo` |
| **Clonar** | Bajar el repo de GitHub a tu laptop por primera vez | `git clone <url>` |
| **Commit** | Un guardado con mensaje | `git commit -m "features: agrega ratio deuda"` |
| **Rama (branch)** | Línea de trabajo paralela; no afecta a las demás hasta fusionarse | `saph1r0/modelo` |
| **main** | La rama principal. **Solo cuenta lo que está aquí al cierre** | — |
| **Push** | Subir tus commits de tu rama a GitHub | `git push` |
| **Pull** | Bajar cambios de GitHub y juntarlos con lo tuyo | `git pull origin main` |
| **Pull Request (PR)** | Pedido en GitHub para fusionar tu rama en `main` | Lo abre cada una, lo fusiona Nat |
| **Merge (fusionar)** | Juntar los cambios de una rama en otra | Botón *Merge pull request* |
| **Conflicto** | Dos personas cambiaron las mismas líneas; Git pide que elijas | Marcas `<<<<<<<` en el archivo |
| **origin** | Nombre corto del remoto (GitHub) | `git push origin mi-rama` |
| **HEAD** | "Donde estoy parada ahora" (rama y commit actual) | — |
| **.gitignore** | Lista de archivos que Git ignora (ej. `data/`, `*.parquet`) | — |
| **Actions** | Revisión automática que corre GitHub en cada push (✅ ⚠️ ❌) | Pestaña *Actions* |

---

## 3. Preparación (una sola vez por laptop)

### 3.1 Comprobar que todo está instalado

```bash
git --version        # cualquier versión 2.x sirve
python3 --version    # 3.10 o superior
code --version       # VS Code
```

En Linux Mint, si falta Git: `sudo apt update && sudo apt install git`.

### 3.2 Decirle a Git quién eres (con el correo anónimo)

El correo anónimo está en GitHub → foto → **Settings → Emails** (con *Keep my email addresses private*
y *Block command line pushes that expose my email* marcados). Tiene la forma
`123456+usuario@users.noreply.github.com`.

```bash
git config --global user.name "natlpx"
git config --global user.email "123456+natlpx@users.noreply.github.com"
git config --global init.defaultBranch main
git config --global pull.rebase false     # pull = merge (lo más simple y seguro)
git config --global core.editor "code --wait"
```

Comprobar: `git config --global --list`.

> Si usas el correo real por error, GitHub **rechazará el push** (por la opción "Block command line
> pushes..."). Arreglo: corrige `user.email` y mira la sección 9.

### 3.3 Iniciar sesión en GitHub desde la terminal

GitHub ya no acepta la contraseña normal en la terminal. Opciones:

- **VS Code (lo más fácil):** al hacer el primer `push`, VS Code abre el navegador para autorizar.
- **GitHub CLI:** `sudo apt install gh` y luego `gh auth login` (elegir HTTPS y navegador).
- **Token:** GitHub → Settings → Developer settings → Personal access tokens; se pega como contraseña.

Para que no la pida cada vez: `git config --global credential.helper store` (o el que use `gh`).

### 3.4 Clonar el repo del equipo

1. Aceptar la invitación del correo de GitHub (*View invitation → Accept*). Sin esto no se puede clonar.
2. En GitHub, botón verde **Code → HTTPS → copiar**.
3. En la terminal:

```bash
cd ~
git clone https://github.com/Datafest-BCP/<equipo>.git
cd <equipo>
git status           # debe decir: On branch main, nothing to commit
```

---

## 4. Cómo trabajamos (reglas del equipo + reglas del evento)

1. **Nadie hace commit directo a `main`.** Cada una trabaja en su rama `<usuario>/<tema>`.
2. **`git push` de tu rama al menos una vez por hora**, aunque el trabajo esté a medias.
3. **PR a `main` al menos cada 2 horas** y aviso a Nat por el chat. Nat (integradora) fusiona.
4. **Antes de cada commit: `git status`.** Si aparece algo de `data/`, un `.parquet`, `.pkl`, `.zip` o
   un `.csv` que no sea `entregas/submission.csv`, **no se sube**.
5. **Nunca `git push --force`** ni reescribir historial (queda registrado).
6. **No tocar** `.github/`, `scripts/verificar_checkpoint.sh`, `scripts/validar_papers.py`, `REGLAS.md`.
7. **No tocar `base_conocimiento/`** después de las 14:00 del viernes.
8. **Quien teclea hace el commit con su cuenta.** Si rotan de laptop, cambian `user.name/user.email`
   con `git config` (sin `--global`, solo para ese repo) o cada una usa su laptop.
9. **Commits chicos y seguidos.** El control automático avisa si suben bloques grandes de golpe.

### Ramas del equipo (simulacro / evento)

| Quién | Rol | Rama sugerida |
|---|---|---|
| Nat (`natlpx`) | Líder, docs, negocio, integradora | `natlpx/config`, `natlpx/docs` |
| Hellen (`hellen228`) | Data engineer | `hellen228/datos` |
| Kath (`kmzc`) | Data engineer | `kmzc/tabla` |
| Sophia (`saph1r0`) | Data scientist | `saph1r0/modelo` |
| Liz (`Lizzz7`) | Data scientist / entrega | `Lizzz7/entrega` |

> Si usan una rama `dev` para integrar: ramas → PR a `dev` → PR de `dev` a `main`. Pero como **solo
> cuenta `main`**, fusionen `dev` en `main` seguido (mínimo cada 2 h). Si hay prisa, PR directo a `main`.

---

## 5. El ciclo de trabajo de cada integrante (copiar y repetir)

### 5.1 Al empezar (una vez)

```bash
git checkout main
git pull origin main                 # bajar lo último
git checkout -b saph1r0/modelo       # crear tu rama y pasarte a ella
```

### 5.2 Cada vez que avanzas algo (cada 20–40 min)

```bash
git status                           # ¿qué cambié? ¿hay datos? (regla 4)
git add trabajo/notas_modelo.md      # añadir archivos concretos (mejor que "git add .")
git commit -m "modelo: prueba LightGBM con 5 folds"
git push                             # la primera vez: git push -u origin saph1r0/modelo
```

### 5.3 Para que tu trabajo llegue a `main` (cada ≤ 2 h)

1. `git push` de tu rama.
2. En GitHub aparece un aviso amarillo **"Compare & pull request"** → clic.
   (O pestaña *Pull requests → New pull request*, base: `main`, compare: tu rama.)
3. Título claro (`modelo: primer modelo validado`) → **Create pull request**.
4. Avisar a Nat en el chat: "PR listo: saph1r0/modelo".

### 5.4 Traer a tu rama lo que otras ya fusionaron

Hazlo después de cada fusión de Nat, y **siempre antes** de editar `config_evento.py`:

```bash
git status                           # que esté limpio (si no, commit primero)
git pull origin main                 # estando en TU rama: trae main y lo junta con lo tuyo
```

Si sale un conflicto, ve a la sección 7.

### 5.5 Mensajes de commit

Formato corto: `área: qué hiciste`. Ejemplos:
`datos: limpia fechas de facturas` · `tabla: agrega mora últimos 3 meses` ·
`entrega: genera submission.csv` · `docs: actualiza SUPUESTOS`.
Evitar: `cambios`, `asdf`, `final final 2`.

---

## 6. Tareas de la integradora (Nat)

### 6.1 Fusionar un PR

1. GitHub → pestaña **Pull requests** → abrir el PR.
2. Mirar la pestaña **Files changed**: ¿hay datos? ¿toca archivos prohibidos? ¿borra cosas de otras?
3. Mirar el resultado de **Actions** (✅ ⚠️ ❌). Un ⚠️ no bloquea, pero lee qué dice.
4. Si dice **"This branch has no conflicts with the base branch"** → botón verde
   **Merge pull request → Confirm merge**. (Dejar "Create a merge commit", no hace falta otra opción.)
5. Avisar en el chat: "Fusionado X, hagan `git pull origin main` en su rama".
6. **No** borrar la rama si la persona seguirá trabajando en ella (si GitHub ofrece "Delete branch",
   se puede ignorar).

### 6.2 Si el PR tiene conflictos

- Si son pocos y simples: botón **Resolve conflicts** en GitHub, editar, **Mark as resolved → Commit merge**.
- Si son muchos o no está claro qué conservar: pedir a la autora que haga en su laptop
  `git pull origin main`, resuelva (sección 7) y haga `git push`; el PR se actualiza solo.

### 6.3 Orden recomendado de fusión

Fusionar primero lo que otros necesitan (config, datos/tabla) y después modelo y entrega. Después de
fusionar `config_evento.py`, avisar a todas de inmediato.

### 6.4 Checklist del cierre (sábado 10:00, cierre 10:30)

- [ ] Todos los PR abiertos fusionados (pestaña Pull requests vacía o solo lo descartado).
- [ ] En GitHub, rama `main`: existe `entregas/submission.csv` con las columnas exactas del enunciado.
- [ ] Existen `presentacion/index.html`, `docs/USO_DE_IA.md`, `docs/BITACORA_FUENTES.md`, `trabajo/SUPUESTOS.md`.
- [ ] Último Actions en `main` revisado.
- [ ] Verificado **mirando GitHub, no la laptop**.

---

## 7. Conflictos: qué son y cómo resolverlos sin pánico

Pasa cuando dos ramas cambiaron **las mismas líneas** del mismo archivo. Git no adivina; te muestra:

```
<<<<<<< HEAD
CORTE = "2025-06-30"          <- lo que tú tienes
=======
CORTE = "2025-03-31"          <- lo que vino de main
>>>>>>> origin/main
```

Pasos:

1. `git status` muestra los archivos en conflicto ("both modified").
2. Abrir el archivo en VS Code: aparecen botones **Accept Current / Accept Incoming / Accept Both**.
   Elegir lo correcto (si dudas, pregunta a quien hizo el otro cambio) y **borrar todas las marcas**
   `<<<<<<<`, `=======`, `>>>>>>>`.
3. Guardar y terminar:

```bash
git add trabajo/config_evento.py
git commit -m "merge: resuelve conflicto en config"
git push
```

¿Te asustaste a mitad? `git merge --abort` deja todo como antes del pull.

**Cómo evitar conflictos:** cada una edita sus propios archivos (tabla del punto 4); `config_evento.py`
lo edita **solo Nat** (las demás le dictan el cambio); hacer `git pull origin main` seguido.

---

## 8. Ver qué está pasando

```bash
git status                     # estado actual: rama, cambios, qué falta subir
git branch                     # ramas locales (* = en la que estás)
git branch -a                  # incluye las remotas
git log --oneline --graph -15  # últimos 15 commits en forma de árbol
git diff                       # qué cambié y aún no añadí
git diff --staged              # qué añadí y entrará al commit
git remote -v                  # a dónde apunta origin
```

En VS Code, el ícono de **Source Control** (ramita, a la izquierda) muestra lo mismo con botones.

---

## 9. Errores comunes y cómo salir

| Síntoma / mensaje | Qué pasa | Qué hacer |
|---|---|---|
| `fatal: not a git repository` | No estás dentro de la carpeta del repo | `cd ~/<equipo>` |
| `Repository not found` al clonar | No aceptaste la invitación o URL mal | Aceptar invitación; copiar URL de nuevo |
| `Authentication failed` / pide contraseña | GitHub no acepta contraseña normal | `gh auth login` o token (3.3) |
| `push declined due to email privacy restrictions` | Commit firmado con correo real | Ver "commit con correo equivocado" abajo |
| `rejected ... (fetch first)` / `non-fast-forward` | Hay cambios en GitHub que no tienes | `git pull origin <tu-rama>` y luego `git push`. **Nunca `--force`** |
| `The current branch has no upstream branch` | Primera vez que subes esa rama | `git push -u origin <tu-rama>` |
| `Your local changes would be overwritten` | Tienes cambios sin commit y quieres pull/cambiar de rama | Haz commit primero (o `git stash`, luego `git stash pop`) |
| `CONFLICT (content)` | Conflicto | Sección 7 |
| Se abre una pantalla rara al hacer pull (Vim) | Git pide mensaje de merge | Escribe `:wq` y Enter (o configura `core.editor`, 3.2) |
| Hice commit en `main` por error (sin push) | — | `git branch mi-usuario/tema` → `git reset --hard origin/main` → `git checkout mi-usuario/tema` |
| Añadí un archivo de datos (sin commit) | — | `git restore --staged data/archivo.csv` |
| Hice commit de un dato (sin push) | — | `git reset --soft HEAD~1`, `git restore --staged <archivo>`, volver a commitear sin él |
| Subí un dato (con push) | Ya está en GitHub | **Avisar a Nat y a la organización**; no intentar borrar historial con force |
| Quiero deshacer un commit ya subido | — | `git revert <id-del-commit>` (crea un commit que lo anula; no reescribe historial) |
| Quiero descartar cambios de un archivo (sin commit) | — | `git restore <archivo>` (¡se pierden!) |

**Commit con correo equivocado (aún sin push):**

```bash
git config user.email "123456+usuario@users.noreply.github.com"
git commit --amend --reset-author --no-edit     # corrige el último commit
git push
```

(Solo si **no** se subió. Si ya está en GitHub, no se usa `--amend`.)

---

## 10. Base de conocimiento (viernes 13, antes de las 14:00)

Plazo oficial 14:00; meta del equipo **13:30**. Máximo 20 MB, sin datos ni modelos.

```bash
git checkout main && git pull origin main
git checkout -b natlpx/base
# copiar archivos dentro de base_conocimiento/ y anotarlos en base_conocimiento/INVENTARIO.md
git add base_conocimiento
git status                                    # nada de data/ ni .csv
git commit -m "base: plantilla, notas e inventario"
git push -u origin natlpx/base
```

PR → Nat fusiona → comprobar en `github.com/Datafest-BCP/<equipo>/tree/main/base_conocimiento`.
Cada archivo debe tener su fila en `INVENTARIO.md` (qué es, quién lo escribió, para qué sirve).

---

## 11. Chuleta de una página

```bash
# --- Una vez ---
git config --global user.name "USUARIO"
git config --global user.email "ID+USUARIO@users.noreply.github.com"
git clone https://github.com/Datafest-BCP/<equipo>.git && cd <equipo>

# --- Empezar a trabajar ---
git checkout main && git pull origin main
git checkout -b USUARIO/tema

# --- Ciclo (cada 20-40 min) ---
git status
git add <archivos>
git commit -m "area: que hice"
git push                      # 1a vez: git push -u origin USUARIO/tema

# --- Cada 2 h: PR en GitHub -> avisar a Nat ---

# --- Traer lo fusionado a mi rama ---
git pull origin main

# --- Mirar ---
git log --oneline --graph -10
git branch -a
git diff

# --- Salvavidas ---
git merge --abort             # salir de un conflicto
git restore <archivo>         # descartar cambios sin commit
git restore --staged <arch>   # sacar del add
git revert <commit>           # deshacer un commit ya subido
git stash / git stash pop     # guardar cambios a un lado un momento

# --- PROHIBIDO ---
# git push --force   |   commit directo a main   |   subir data/   |   tocar base_conocimiento/ después de 14:00
```

---

*Nota de autoría para el INVENTARIO: documento preparado antes del evento con asistencia de una IA
distinta del Copilot del evento (Claude, de Anthropic), revisado por el equipo MeowWo.*
