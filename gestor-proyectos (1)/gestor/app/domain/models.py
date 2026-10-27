"""Tipos del dominio. Todos son inmutables (frozen=True)."""
from dataclasses import dataclass
from enum import Enum


class Estado(Enum):
    PENDIENTE = "Pendiente"
    EN_PROGRESO = "En progreso"
    EN_REVISION = "En revisión"
    TERMINADA = "Terminada"


class Prioridad(Enum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3


# id=None significa "todavía no guardado": lo asigna la base de datos.
@dataclass(frozen=True)
class Proyecto:
    nombre: str
    descripcion: str = ""
    id: int | None = None


@dataclass(frozen=True)
class Integrante:
    proyecto_id: int
    nombre: str
    id: int | None = None


@dataclass(frozen=True)
class Paquete:
    """Nodo de la EDT. padre_id=None -> entregable de primer nivel."""
    proyecto_id: int
    nombre: str
    padre_id: int | None = None
    id: int | None = None


@dataclass(frozen=True)
class Tarea:
    proyecto_id: int
    paquete_id: int
    titulo: str
    responsable_id: int | None
    prioridad: Prioridad
    estado: Estado = Estado.PENDIENTE
    id: int | None = None
