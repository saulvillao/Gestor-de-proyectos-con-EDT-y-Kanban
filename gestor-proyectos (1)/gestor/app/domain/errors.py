"""Errores esperados del dominio, como valores (no excepciones)."""
from dataclasses import dataclass

from app.domain.models import Estado


@dataclass(frozen=True)
class NombreVacio:
    campo: str


@dataclass(frozen=True)
class TituloVacio:
    pass


@dataclass(frozen=True)
class TransicionInvalida:
    origen: Estado
    destino: Estado


@dataclass(frozen=True)
class ResponsableNoExiste:
    id: int


@dataclass(frozen=True)
class PaqueteNoExiste:
    id: int


@dataclass(frozen=True)
class TareaNoExiste:
    id: int


@dataclass(frozen=True)
class ErrorPersistencia:
    mensaje: str


ErrorDominio = (NombreVacio | TituloVacio | TransicionInvalida
                | ResponsableNoExiste | PaqueteNoExiste | TareaNoExiste
                | ErrorPersistencia)
