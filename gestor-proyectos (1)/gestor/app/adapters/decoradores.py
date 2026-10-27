"""Decoradores transversales de la shell. Ninguno contiene reglas del dominio."""
import functools
import logging
import sqlite3
import time

from app.domain.errors import ErrorPersistencia
from app.domain.result import Err

log = logging.getLogger("gestor")


def medir(func):
    """Registra cuánto tarda cada operación (preocupación externa: observabilidad)."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            log.info("%s tardó %.4fs", func.__name__, time.perf_counter() - inicio)
    return envoltura


def captura_errores_sqlite(func):
    """Convierte sqlite3.Error en Err(ErrorPersistencia): sin excepciones hacia arriba."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as e:
            log.error("%s falló: %s", func.__name__, e)
            return Err(ErrorPersistencia(str(e)))
    return envoltura
