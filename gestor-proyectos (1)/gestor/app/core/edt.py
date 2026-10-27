"""Operaciones puras sobre la EDT (jerarquía de paquetes)."""
from app.domain.errors import NombreVacio, PaqueteNoExiste
from app.domain.models import Paquete
from app.domain.result import Err, Ok


def buscar_paquete(paquetes: tuple[Paquete, ...], paquete_id: int) -> Paquete | None:
    return next((p for p in paquetes if p.id == paquete_id), None)


def crear_paquete(proyecto_id: int, nombre: str, padre_id: int | None,
                  paquetes: tuple[Paquete, ...]) -> Ok | Err:
    if not nombre.strip():
        return Err(NombreVacio("paquete"))
    if padre_id is not None and buscar_paquete(paquetes, padre_id) is None:
        return Err(PaqueteNoExiste(padre_id))
    return Ok(Paquete(proyecto_id=proyecto_id, nombre=nombre.strip(), padre_id=padre_id))


def _desde(paquetes, padre_id, nivel):
    hijos = sorted(filter(lambda p: p.padre_id == padre_id, paquetes), key=lambda p: p.id)
    return tuple(par for h in hijos
                 for par in ((h, nivel),) + _desde(paquetes, h.id, nivel + 1))


def aplanar_edt(paquetes: tuple[Paquete, ...]) -> tuple[tuple[Paquete, int], ...]:
    """Devuelve (paquete, nivel) en orden de árbol, listo para dibujar con sangría."""
    return _desde(paquetes, None, 0)
