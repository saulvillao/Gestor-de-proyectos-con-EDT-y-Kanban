"""Flujo completo shell + core + SQLite en memoria (sin ReactPy)."""
import pytest

from app.adapters.sqlite_repo import RepositorioSQLite
from app.core.comandos import AsignarResponsable, CambiarEstado
from app.domain.errors import NombreVacio, TituloVacio, TransicionInvalida
from app.domain.models import Estado, Prioridad
from app.domain.result import Err, Ok
from app.ui import controlador as ctl
from app.ui.mensajes import mensaje_de_error


@pytest.fixture
def escenario():
    repo = RepositorioSQLite.abrir(":memory:")
    p = ctl.crear_proyecto(repo, "Demo", "").valor
    ana = ctl.agregar_integrante(repo, p.id, "Ana").valor
    q = ctl.agregar_paquete(repo, p.id, "Diseño", None).valor
    t = ctl.agregar_tarea(repo, p.id, "Login", q.id, ana.id, Prioridad.ALTA).valor
    return repo, p, ana, q, t


def test_crear_y_cargar_vista(escenario):
    repo, p, ana, q, t = escenario
    v = ctl.cargar_vista(repo, p.id).valor
    assert v.proyecto == p and v.integrantes == (ana,) and v.paquetes == (q,) and v.tareas == (t,)


def test_proyecto_inexistente_da_vista_sin_proyecto(escenario):
    repo, *_ = escenario
    assert ctl.cargar_vista(repo, 999).valor.proyecto is None


def test_mover_tarea_valida_se_persiste(escenario):
    repo, p, _, _, t = escenario
    assert isinstance(ctl.ejecutar_comando(repo, p.id, CambiarEstado(t.id, Estado.EN_PROGRESO)), Ok)
    assert ctl.cargar_vista(repo, p.id).valor.tareas[0].estado == Estado.EN_PROGRESO


def test_transicion_invalida_no_modifica_la_bd(escenario):
    repo, p, _, _, t = escenario
    r = ctl.ejecutar_comando(repo, p.id, CambiarEstado(t.id, Estado.TERMINADA))
    assert r == Err(TransicionInvalida(Estado.PENDIENTE, Estado.TERMINADA))
    assert ctl.cargar_vista(repo, p.id).valor.tareas[0].estado == Estado.PENDIENTE
    assert "No se puede pasar de «Pendiente» a «Terminada»" in mensaje_de_error(r.error)


def test_datos_invalidos_no_se_guardan(escenario):
    repo, p, _, q, _ = escenario
    assert ctl.agregar_tarea(repo, p.id, "  ", q.id, None, Prioridad.BAJA) == Err(TituloVacio())
    assert ctl.agregar_integrante(repo, p.id, "") == Err(NombreVacio("integrante"))
    assert len(ctl.cargar_vista(repo, p.id).valor.tareas) == 1


def test_reasignar_responsable(escenario):
    repo, p, _, _, t = escenario
    ctl.ejecutar_comando(repo, p.id, AsignarResponsable(t.id, None))
    assert ctl.cargar_vista(repo, p.id).valor.tareas[0].responsable_id is None
