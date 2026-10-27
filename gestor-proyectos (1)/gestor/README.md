# Gestor de proyectos con EDT y Kanban

Aplicación web local (ReactPy + FastAPI + SQLite) para crear un proyecto, descomponerlo en una
**EDT/WBS** (entregables → paquetes), asignar responsables y seguir las tareas en un **tablero Kanban**.
La EDT responde *¿qué trabajo hay?*; Kanban responde *¿en qué estado está?*.

**Integrantes:** [Alex Ariel Guale Muñoz](https://eva.upse.edu.ec/user/view.php?id=6239&course=2235) · [Luis Angel Crespin Lucas](https://eva.upse.edu.ec/user/view.php?id=6243&course=2235) · [Saul Joshue Villao Lopez](https://eva.upse.edu.ec/user/view.php?id=6883&course=2235)

**Repositorio:** _(enlace)_ · **Video:** _(enlace)_

## Instalación y ejecución

Requiere Python 3.10+ (probado con 3.12).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000. Los datos se guardan en `gestor.db` (variable `GESTOR_DB` para cambiar la ruta).
No hay API REST propia: FastAPI solo sirve la app ReactPy.

Pruebas: `python -m pytest` (núcleo puro en `tests/unit`, SQLite en memoria en `tests/integration`).

> Nota: ReactPy 1.1.0 no es compatible con Starlette ≥ 0.50; por eso `requirements.txt` fija las versiones.

## Estructura

```text
app/
  domain/     models.py (dataclasses frozen), errors.py (errores como valores), result.py (Ok/Err)
  core/       FUNCTIONAL CORE (puro): kanban, tareas, edt, filtros, comandos, proyecto
  ports/      repositorio.py: contrato (Protocol) de persistencia
  adapters/   IMPERATIVE SHELL: sqlite_repo.py, decoradores.py
  ui/         IMPERATIVE SHELL: controlador.py, mensajes.py, app.py (ReactPy)
  main.py     ensamble: repo + FastAPI + ReactPy
tests/unit/ tests/integration/
```

Flujo de cada evento: `evento ReactPy → controlador lee datos (repo) → función pura del core → match Ok/Err → guarda (repo) y refresca la UI`.
`core/` no importa `sqlite3`, `reactpy` ni `fastapi`.

## Reglas Kanban

| Desde | Hacia (permitido) |
|---|---|
| Pendiente | En progreso |
| En progreso | En revisión, Pendiente |
| En revisión | Terminada, En progreso |
| Terminada | — (estado final) |

Cualquier otra transición devuelve `Err(TransicionInvalida)` y no modifica nada. La interfaz deja intentar
cualquier destino a propósito, para que la regla (y no la UI) sea quien rechace.

## Evidencia de los temas del curso

| Tema | Archivo | Función / elemento | Por qué |
|---|---|---|---|
| Del cómo al qué | `core/filtros.py` | `filtrar`, `agrupar_por_estado`, `construir_criterios` | Declaran *qué* tareas se quieren, sin bucles con acumuladores |
| Pattern matching | `core/comandos.py` | `aplicar` | `match/case` sobre `CambiarEstado` / `AsignarResponsable` con guarda y patrón `None` |
| Pattern matching | `ui/mensajes.py` | `mensaje_de_error` | Cada variante de error se convierte en un mensaje |
| Funciones de orden superior | `core/filtros.py` | `filtrar(tareas, *criterios)` | Recibe funciones-criterio |
| Funciones de orden superior | `domain/result.py` | `encadenar` | Aplica una función solo si hay `Ok`; usada en `ui/controlador.py` |
| Lambdas | `core/filtros.py`, `core/edt.py` | `ordenar_por_prioridad`, `_desde` | Criterios de una línea (`key=`, `filter`). Se usa función con nombre cuando la lógica es reutilizable o necesita docstring (`por_estado`, `cambiar_estado`) |
| Closures | `core/filtros.py` | `por_estado`, `por_responsable`, `por_prioridad` | Capturan su criterio; no hay estado mutable |
| Inmutabilidad | `domain/models.py`, `core/kanban.py` | `@dataclass(frozen=True)`, `dataclasses.replace`, `MappingProxyType` | Cambiar estado devuelve una copia; la tabla de transiciones es de solo lectura |
| Pureza y efectos | `core/*` vs `adapters/`, `ui/` | — | Todo `core/` es puro. Efectos (SQLite, logging, ReactPy) están en la shell |
| Ausencia de valor | `core/tareas.py`, `ui/controlador.py` | `buscar_tarea`, `buscar_integrante`, `buscar_paquete`, `cargar_vista` | Devuelven `None` si no existe; una lista vacía es un valor válido distinto |
| Errores funcionales | `domain/result.py`, `domain/errors.py`, `core/kanban.py` | `Ok`/`Err`, `TransicionInvalida`, `TituloVacio`… | Errores esperados como valores; `ErrorPersistencia` en lugar de excepciones SQLite |
| Decoradores | `adapters/decoradores.py` | `medir`, `captura_errores_sqlite` | Cuestiones transversales (tiempo y conversión de errores). No tocan reglas del dominio |

## Pureza: qué es puro y qué no

- **Puro:** todo `app/core/` y `app/domain/`. Misma entrada → misma salida, sin I/O.
- **Efectos (shell):** `adapters/sqlite_repo.py` (BD), `adapters/decoradores.py` (logging/tiempo),
  `ui/controlador.py` (orquesta), `ui/app.py` (estado visual y eventos), `main.py` (servidor).

## Atomicidad

Cada escritura usa `with conn:` (commit o rollback). Las restricciones `CHECK` y `FOREIGN KEY` del esquema
son una segunda barrera; si fallan, el adaptador devuelve `Err(ErrorPersistencia)` y no queda nada parcial.
Las pruebas del adaptador usan `:memory:`.

## Contribuciones

| Integrante | Responsabilidad | Dónde se evidencia |
|---|---|---|
| Alex Ariel Guale Muñoz | Núcleo: `domain/`, `core/`, `tests/unit/` | rama `feature/core` |
| Luis Angel Crespin Lucas | Persistencia: `ports/`, `adapters/`, `main.py`, `tests/integration/` | rama `feature/sqlite` |
| Saul Joshue Villao Lopez | Interfaz: `ui/`, README, PDF | rama `feature/ui` |
