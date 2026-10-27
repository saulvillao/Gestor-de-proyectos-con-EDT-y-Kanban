"""Pruebas del adaptador SQLite con base en memoria (nunca los datos reales)."""
import logging
import sqlite3

import pytest

from app.adapters.sqlite_repo import RepositorioSQLite
from app.domain.errors import ErrorPersistencia, TareaNoExiste
from app.domain.models import Estado, Integrante, Paquete, Prioridad, Proyecto, Tarea
from app.domain.result import Err, Ok


@pytest.fixture
def repo():
    return RepositorioSQLite.abrir(":memory:")


@pytest.fixture
def base(repo):
    p = repo.guardar_proyecto(Proyecto("Demo")).valor
    i = repo.guardar_integrante(Integrante(p.id, "Ana")).valor
    q = repo.guardar_paquete(Paquete(p.id, "Diseño")).valor
    return repo, p, i, q


def test_inicializar_es_idempotente(repo):
    assert repo.inicializar() == Ok(None)
    assert repo.inicializar() == Ok(None)


def test_proyecto_ida_y_vuelta(repo):
    guardado = repo.guardar_proyecto(Proyecto("Demo", "desc")).valor
    assert guardado.id is not None
    assert repo.listar_proyectos() == Ok((guardado,))


def test_lista_vacia_es_ok_y_no_error(repo):
    assert repo.listar_proyectos() == Ok(())
    assert repo.listar_tareas(1) == Ok(())


def test_tarea_ida_y_vuelta_y_actualizacion(base):
    repo, p, i, q = base
    t = repo.guardar_tarea(Tarea(p.id, q.id, "Login", i.id, Prioridad.ALTA)).valor
    assert repo.listar_tareas(p.id) == Ok((t,))
    from dataclasses import replace
    movida = replace(t, estado=Estado.EN_PROGRESO)
    assert repo.guardar_tarea(movida) == Ok(movida)
    assert repo.listar_tareas(p.id).valor[0].estado == Estado.EN_PROGRESO


def test_actualizar_tarea_inexistente(base):
    repo, p, i, q = base
    fantasma = Tarea(p.id, q.id, "x", None, Prioridad.BAJA, id=999)
    assert repo.guardar_tarea(fantasma) == Err(TareaNoExiste(999))


def test_fk_invalida_devuelve_err_y_no_deja_filas(base):
    repo, p, i, q = base
    r = repo.guardar_tarea(Tarea(p.id, 999, "huérfana", None, Prioridad.BAJA))
    assert isinstance(r, Err) and isinstance(r.error, ErrorPersistencia)
    assert repo.listar_tareas(p.id) == Ok(())


def test_check_de_la_bd_rechaza_titulo_vacio_sin_dejar_cambios(base):
    repo, p, i, q = base
    r = repo.guardar_tarea(Tarea(p.id, q.id, "   ", None, Prioridad.BAJA))
    assert isinstance(r, Err)
    assert repo.listar_tareas(p.id) == Ok(())


def test_filtra_por_proyecto(repo):
    a = repo.guardar_proyecto(Proyecto("A")).valor
    b = repo.guardar_proyecto(Proyecto("B")).valor
    repo.guardar_integrante(Integrante(a.id, "Ana"))
    assert repo.listar_integrantes(b.id) == Ok(())


def test_error_de_conexion_se_convierte_en_err():
    conn = sqlite3.connect(":memory:")
    repo = RepositorioSQLite(conn)
    conn.close()
    assert isinstance(repo.listar_proyectos(), Err)


def test_decorador_medir_registra_duracion(repo, caplog):
    with caplog.at_level(logging.INFO, logger="gestor"):
        repo.listar_proyectos()
    assert any("listar_proyectos tardó" in m for m in caplog.messages)
