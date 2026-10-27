"""Reglas del tablero Kanban (puras)."""
from dataclasses import replace
from types import MappingProxyType

from app.domain.errors import TransicionInvalida
from app.domain.models import Estado, Tarea
from app.domain.result import Err, Ok

# Tabla de transiciones permitidas, de solo lectura.
TRANSICIONES = MappingProxyType({
    Estado.PENDIENTE: frozenset({Estado.EN_PROGRESO}),
    Estado.EN_PROGRESO: frozenset({Estado.EN_REVISION, Estado.PENDIENTE}),
    Estado.EN_REVISION: frozenset({Estado.TERMINADA, Estado.EN_PROGRESO}),
    Estado.TERMINADA: frozenset(),
})


def cambiar_estado(tarea: Tarea, nuevo: Estado) -> Ok | Err:
    if nuevo in TRANSICIONES[tarea.estado]:
        return Ok(replace(tarea, estado=nuevo))  # copia; no muta la original
    return Err(TransicionInvalida(tarea.estado, nuevo))
