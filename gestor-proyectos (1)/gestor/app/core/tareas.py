"""Creación, búsqueda y consultas sobre tareas (puro)."""
from collections import Counter

from app.core.edt import buscar_paquete
from app.domain.errors import PaqueteNoExiste, ResponsableNoExiste, TituloVacio
from app.domain.models import Estado, Integrante, Paquete, Prioridad, Tarea
from app.domain.result import Err, Ok


def buscar_tarea(tareas: tuple[Tarea, ...], tarea_id: int) -> Tarea | None:
    """Ausencia de valor: devuelve None si no existe."""
    return next((t for t in tareas if t.id == tarea_id), None)


def buscar_integrante(integrantes: tuple[Integrante, ...], integrante_id: int) -> Integrante | None:
    return next((i for i in integrantes if i.id == integrante_id), None)


def crear_tarea(proyecto_id: int, titulo: str, paquete_id: int,
                responsable_id: int | None, prioridad: Prioridad,
                paquetes: tuple[Paquete, ...],
                integrantes: tuple[Integrante, ...]) -> Ok | Err:
    if not titulo.strip():
        return Err(TituloVacio())
    if buscar_paquete(paquetes, paquete_id) is None:
        return Err(PaqueteNoExiste(paquete_id))
    if responsable_id is not None and buscar_integrante(integrantes, responsable_id) is None:
        return Err(ResponsableNoExiste(responsable_id))
    return Ok(Tarea(proyecto_id=proyecto_id, paquete_id=paquete_id, titulo=titulo.strip(),
                    responsable_id=responsable_id, prioridad=prioridad))


def pendientes_por_integrante(tareas: tuple[Tarea, ...]) -> dict[int, int]:
    """Cantidad de tareas no terminadas por responsable (ignora las sin asignar)."""
    return dict(Counter(t.responsable_id for t in tareas
                        if t.responsable_id is not None and t.estado != Estado.TERMINADA))
