"""Shell: coordina repositorio + núcleo. Aquí no hay reglas de negocio, solo orquestación.

Patrón de cada operación:  leer datos (repo) -> función pura (core) -> guardar (repo).
"""
from dataclasses import dataclass

from app.core import comandos, edt, proyecto, tareas
from app.domain.models import Integrante, Paquete, Prioridad, Proyecto, Tarea
from app.domain.result import Err, Ok, encadenar


@dataclass(frozen=True)
class Vista:
    """Foto inmutable de lo que la interfaz necesita mostrar."""
    proyectos: tuple[Proyecto, ...] = ()
    proyecto: Proyecto | None = None
    integrantes: tuple[Integrante, ...] = ()
    paquetes: tuple[Paquete, ...] = ()
    tareas: tuple[Tarea, ...] = ()


def cargar_vista(repo, proyecto_id: int | None) -> Ok | Err:
    def con_proyectos(todos):
        if proyecto_id is None:
            return Ok(Vista(proyectos=todos))
        actual = next((p for p in todos if p.id == proyecto_id), None)  # ausencia de valor
        if actual is None:
            return Ok(Vista(proyectos=todos))
        return encadenar(repo.listar_integrantes(proyecto_id), lambda ints:
               encadenar(repo.listar_paquetes(proyecto_id), lambda pqs:
               encadenar(repo.listar_tareas(proyecto_id), lambda ts:
                         Ok(Vista(todos, actual, ints, pqs, ts)))))
    return encadenar(repo.listar_proyectos(), con_proyectos)


def crear_proyecto(repo, nombre: str, descripcion: str):
    return encadenar(proyecto.crear_proyecto(nombre, descripcion), repo.guardar_proyecto)


def agregar_integrante(repo, pid: int, nombre: str):
    return encadenar(proyecto.crear_integrante(pid, nombre), repo.guardar_integrante)


def agregar_paquete(repo, pid: int, nombre: str, padre_id: int | None):
    return encadenar(repo.listar_paquetes(pid), lambda pqs:
           encadenar(edt.crear_paquete(pid, nombre, padre_id, pqs), repo.guardar_paquete))


def agregar_tarea(repo, pid: int, titulo: str, paquete_id: int | None,
                  responsable_id: int | None, prioridad: Prioridad):
    return encadenar(repo.listar_paquetes(pid), lambda pqs:
           encadenar(repo.listar_integrantes(pid), lambda ints:
           encadenar(tareas.crear_tarea(pid, titulo, paquete_id, responsable_id, prioridad, pqs, ints),
                     repo.guardar_tarea)))


def ejecutar_comando(repo, pid: int, comando):
    return encadenar(repo.listar_tareas(pid), lambda ts:
           encadenar(repo.listar_integrantes(pid), lambda ints:
           encadenar(comandos.aplicar(comando, ts, ints), repo.guardar_tarea)))
