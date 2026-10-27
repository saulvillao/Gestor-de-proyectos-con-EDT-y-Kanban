"""Filtros y orden: closures + funciones de orden superior (puro)."""
from typing import Callable

from app.domain.models import Estado, Prioridad, Tarea

Criterio = Callable[[Tarea], bool]


# Closures: cada una captura su criterio y no guarda estado mutable.
def por_estado(estado: Estado) -> Criterio:
    return lambda t: t.estado == estado


def por_responsable(responsable_id: int) -> Criterio:
    return lambda t: t.responsable_id == responsable_id


def por_prioridad(prioridad: Prioridad) -> Criterio:
    return lambda t: t.prioridad == prioridad


def construir_criterios(estado: Estado | None = None, responsable_id: int | None = None,
                        prioridad: Prioridad | None = None) -> tuple[Criterio, ...]:
    """Convierte filtros opcionales (None = sin filtro) en una tupla de criterios."""
    candidatos = ((estado, por_estado), (responsable_id, por_responsable), (prioridad, por_prioridad))
    return tuple(fabrica(valor) for valor, fabrica in candidatos if valor is not None)


def filtrar(tareas: tuple[Tarea, ...], *criterios: Criterio) -> tuple[Tarea, ...]:
    """HOF: recibe funciones-criterio y deja las tareas que cumplen todas."""
    return tuple(t for t in tareas if all(c(t) for c in criterios))


def ordenar_por_prioridad(tareas: tuple[Tarea, ...]) -> tuple[Tarea, ...]:
    # lambda pequeña: mayor prioridad primero, desempate por id.
    return tuple(sorted(tareas, key=lambda t: (-t.prioridad.value, t.id or 0)))


def agrupar_por_estado(tareas: tuple[Tarea, ...]) -> dict[Estado, tuple[Tarea, ...]]:
    return {e: filtrar(tareas, por_estado(e)) for e in Estado}
