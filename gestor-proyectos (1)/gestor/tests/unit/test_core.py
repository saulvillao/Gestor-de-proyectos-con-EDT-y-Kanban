"""Pruebas del núcleo funcional: sin ReactPy, sin FastAPI, sin SQLite, sin mocks."""
import dataclasses

import pytest

from app.core import comandos as cmd
from app.core import edt, filtros, kanban, proyecto, tareas
from app.domain.errors import (NombreVacio, PaqueteNoExiste, ResponsableNoExiste,
                               TareaNoExiste, TituloVacio, TransicionInvalida)
from app.domain.models import Estado, Integrante, Paquete, Prioridad, Tarea
from app.domain.result import Err, Ok, encadenar

ANA = Integrante(proyecto_id=1, nombre="Ana", id=1)
LUIS = Integrante(proyecto_id=1, nombre="Luis", id=2)
INTEGRANTES = (ANA, LUIS)
PAQUETES = (Paquete(1, "Diseño", None, 1), Paquete(1, "Mockups", 1, 2), Paquete(1, "Código", None, 3))


def t(id, estado=Estado.PENDIENTE, resp=1, prio=Prioridad.MEDIA):
    return Tarea(proyecto_id=1, paquete_id=1, titulo=f"T{id}", responsable_id=resp,
                 prioridad=prio, estado=estado, id=id)


# --- Inmutabilidad -------------------------------------------------------
def test_tarea_es_inmutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        t(1).estado = Estado.TERMINADA


# --- Kanban --------------------------------------------------------------
def test_transicion_valida_devuelve_copia_sin_mutar_original():
    original = t(1)
    r = kanban.cambiar_estado(original, Estado.EN_PROGRESO)
    assert r == Ok(dataclasses.replace(original, estado=Estado.EN_PROGRESO))
    assert original.estado == Estado.PENDIENTE


@pytest.mark.parametrize("origen,destino", [
    (Estado.PENDIENTE, Estado.TERMINADA),
    (Estado.PENDIENTE, Estado.EN_REVISION),
    (Estado.TERMINADA, Estado.PENDIENTE),   # límite: Terminada es final
    (Estado.PENDIENTE, Estado.PENDIENTE),   # límite: mismo estado
])
def test_transicion_invalida(origen, destino):
    assert kanban.cambiar_estado(t(1, origen), destino) == Err(TransicionInvalida(origen, destino))


def test_flujo_completo_hasta_terminada():
    tarea = t(1)
    for siguiente in (Estado.EN_PROGRESO, Estado.EN_REVISION, Estado.TERMINADA):
        match kanban.cambiar_estado(tarea, siguiente):
            case Ok(nueva):
                tarea = nueva
            case Err(e):
                pytest.fail(f"no debía fallar: {e}")
    assert tarea.estado == Estado.TERMINADA


def test_se_puede_retroceder_de_revision():
    assert isinstance(kanban.cambiar_estado(t(1, Estado.EN_REVISION), Estado.EN_PROGRESO), Ok)


# --- Crear tareas / validación -------------------------------------------
def test_crear_tarea_ok():
    r = tareas.crear_tarea(1, "  Hacer login ", 1, 1, Prioridad.ALTA, PAQUETES, INTEGRANTES)
    assert r == Ok(Tarea(1, 1, "Hacer login", 1, Prioridad.ALTA))


@pytest.mark.parametrize("titulo", ["", "   ", "\t\n"])
def test_titulo_vacio(titulo):
    assert tareas.crear_tarea(1, titulo, 1, 1, Prioridad.BAJA, PAQUETES, INTEGRANTES) == Err(TituloVacio())


def test_paquete_inexistente():
    r = tareas.crear_tarea(1, "x", 99, 1, Prioridad.BAJA, PAQUETES, INTEGRANTES)
    assert r == Err(PaqueteNoExiste(99))


def test_responsable_inexistente():
    r = tareas.crear_tarea(1, "x", 1, 99, Prioridad.BAJA, PAQUETES, INTEGRANTES)
    assert r == Err(ResponsableNoExiste(99))


def test_tarea_sin_responsable_es_valida():
    assert isinstance(tareas.crear_tarea(1, "x", 1, None, Prioridad.BAJA, PAQUETES, INTEGRANTES), Ok)


def test_crear_proyecto_e_integrante():
    assert proyecto.crear_proyecto(" App ", " desc ").valor.nombre == "App"
    assert proyecto.crear_proyecto("  ") == Err(NombreVacio("proyecto"))
    assert proyecto.crear_integrante(1, "") == Err(NombreVacio("integrante"))


# --- Ausencia de valor ---------------------------------------------------
def test_buscar_tarea_devuelve_none_si_no_existe():
    assert tareas.buscar_tarea((t(1),), 5) is None
    assert tareas.buscar_tarea((t(1),), 1) == t(1)
    assert tareas.buscar_tarea((), 1) is None  # lista vacía != tarea inexistente con error


# --- Pendientes por integrante -------------------------------------------
def test_pendientes_por_integrante():
    ts = (t(1, resp=1), t(2, Estado.TERMINADA, resp=1), t(3, resp=2), t(4, resp=None))
    assert tareas.pendientes_por_integrante(ts) == {1: 1, 2: 1}
    assert tareas.pendientes_por_integrante(()) == {}


# --- Filtros: closures y HOF ---------------------------------------------
def test_closures_capturan_su_criterio():
    solo_ana = filtros.por_responsable(1)
    solo_luis = filtros.por_responsable(2)
    ts = (t(1, resp=1), t(2, resp=2))
    assert filtros.filtrar(ts, solo_ana) == (t(1, resp=1),)
    assert filtros.filtrar(ts, solo_luis) == (t(2, resp=2),)  # la primera closure no se alteró


def test_filtrar_combina_criterios_y_sin_criterios_devuelve_todo():
    ts = (t(1, resp=1), t(2, Estado.EN_PROGRESO, resp=1), t(3, Estado.EN_PROGRESO, resp=2))
    crit = filtros.construir_criterios(estado=Estado.EN_PROGRESO, responsable_id=1)
    assert filtros.filtrar(ts, *crit) == (ts[1],)
    assert filtros.filtrar(ts) == ts
    assert filtros.construir_criterios() == ()


def test_filtrar_sin_resultados():
    assert filtros.filtrar((t(1),), filtros.por_estado(Estado.TERMINADA)) == ()


def test_ordenar_por_prioridad():
    ts = (t(1, prio=Prioridad.BAJA), t(2, prio=Prioridad.ALTA), t(3, prio=Prioridad.ALTA))
    assert [x.id for x in filtros.ordenar_por_prioridad(ts)] == [2, 3, 1]


def test_agrupar_por_estado_incluye_columnas_vacias():
    g = filtros.agrupar_por_estado((t(1), t(2, Estado.TERMINADA)))
    assert set(g) == set(Estado)
    assert len(g[Estado.PENDIENTE]) == 1 and g[Estado.EN_REVISION] == ()


# --- EDT -----------------------------------------------------------------
def test_aplanar_edt_respeta_jerarquia():
    plano = edt.aplanar_edt(PAQUETES)
    assert [(p.nombre, n) for p, n in plano] == [("Diseño", 0), ("Mockups", 1), ("Código", 0)]
    assert edt.aplanar_edt(()) == ()


def test_crear_paquete():
    assert isinstance(edt.crear_paquete(1, "Pruebas", 3, PAQUETES), Ok)
    assert edt.crear_paquete(1, "Pruebas", 99, PAQUETES) == Err(PaqueteNoExiste(99))
    assert edt.crear_paquete(1, " ", None, PAQUETES) == Err(NombreVacio("paquete"))


def test_crear_paquete_no_muta_la_edt_recibida():
    antes = PAQUETES
    edt.crear_paquete(1, "Nuevo", None, PAQUETES)
    assert PAQUETES == antes


# --- Comandos (pattern matching) -----------------------------------------
def test_comando_cambiar_estado():
    r = cmd.aplicar(cmd.CambiarEstado(1, Estado.EN_PROGRESO), (t(1),), INTEGRANTES)
    assert r.valor.estado == Estado.EN_PROGRESO


def test_comando_transicion_invalida_se_propaga():
    r = cmd.aplicar(cmd.CambiarEstado(1, Estado.TERMINADA), (t(1),), INTEGRANTES)
    assert r == Err(TransicionInvalida(Estado.PENDIENTE, Estado.TERMINADA))


def test_comando_sobre_tarea_inexistente():
    assert cmd.aplicar(cmd.CambiarEstado(9, Estado.EN_PROGRESO), (t(1),), INTEGRANTES) == Err(TareaNoExiste(9))


def test_comando_asignar_responsable():
    assert cmd.aplicar(cmd.AsignarResponsable(1, 2), (t(1),), INTEGRANTES).valor.responsable_id == 2
    assert cmd.aplicar(cmd.AsignarResponsable(1, None), (t(1),), INTEGRANTES).valor.responsable_id is None
    assert cmd.aplicar(cmd.AsignarResponsable(1, 99), (t(1),), INTEGRANTES) == Err(ResponsableNoExiste(99))


# --- Result --------------------------------------------------------------
def test_encadenar_propaga_el_primer_error_sin_ejecutar_el_resto():
    llamado = []
    r = encadenar(Err("falló"), lambda v: llamado.append(v) or Ok(v))
    assert r == Err("falló") and llamado == []
    assert encadenar(Ok(2), lambda v: Ok(v * 2)) == Ok(4)
