"""Resultado explícito: Ok(valor) o Err(error)."""
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T]):
    valor: T


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E


Resultado = Ok | Err


def encadenar(resultado: Resultado, f: Callable[[object], Resultado]) -> Resultado:
    """Aplica f solo si hay Ok; si hay Err lo propaga sin tocarlo (HOF)."""
    match resultado:
        case Ok(valor):
            return f(valor)
        case Err():
            return resultado
