"""Creación y validación de proyectos e integrantes (puro)."""
from app.domain.errors import NombreVacio
from app.domain.models import Integrante, Proyecto
from app.domain.result import Err, Ok


def crear_proyecto(nombre: str, descripcion: str = "") -> Ok | Err:
    if not nombre.strip():
        return Err(NombreVacio("proyecto"))
    return Ok(Proyecto(nombre=nombre.strip(), descripcion=descripcion.strip()))


def crear_integrante(proyecto_id: int, nombre: str) -> Ok | Err:
    if not nombre.strip():
        return Err(NombreVacio("integrante"))
    return Ok(Integrante(proyecto_id=proyecto_id, nombre=nombre.strip()))
