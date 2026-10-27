"""Comandos sobre tareas procesados con pattern matching (puro)."""
from dataclasses import dataclass, replace

from app.core.kanban import cambiar_estado
from app.core.tareas import buscar_integrante, buscar_tarea
from app.domain.errors import ResponsableNoExiste, TareaNoExiste
from app.domain.models import Estado, Integrante, Tarea
from app.domain.result import Err, Ok


@dataclass(frozen=True)
class CambiarEstado:
    tarea_id: int
    nuevo: Estado


@dataclass(frozen=True)
class AsignarResponsable:
    tarea_id: int
    responsable_id: int | None  # None = dejar sin asignar


Comando = CambiarEstado | AsignarResponsable


def aplicar(comando: Comando, tareas: tuple[Tarea, ...],
            integrantes: tuple[Integrante, ...]) -> Ok | Err:
    """Devuelve la tarea actualizada (Ok) o el error esperado (Err). No guarda nada."""
    tarea = buscar_tarea(tareas, comando.tarea_id)
    if tarea is None:
        return Err(TareaNoExiste(comando.tarea_id))
    match comando:
        case CambiarEstado(_, nuevo):
            return cambiar_estado(tarea, nuevo)
        case AsignarResponsable(_, None):
            return Ok(replace(tarea, responsable_id=None))
        case AsignarResponsable(_, rid) if buscar_integrante(integrantes, rid) is None:
            return Err(ResponsableNoExiste(rid))
        case AsignarResponsable(_, rid):
            return Ok(replace(tarea, responsable_id=rid))
