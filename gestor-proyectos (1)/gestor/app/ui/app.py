"""Shell: componentes ReactPy. Los callbacks solo llaman al controlador y muestran el resultado."""
from reactpy import component, html, use_state

from app.core import filtros
from app.core.comandos import AsignarResponsable, CambiarEstado
from app.core.edt import aplanar_edt
from app.core.kanban import TRANSICIONES
from app.core.tareas import pendientes_por_integrante
from app.domain.models import Estado, Prioridad
from app.domain.result import Err, Ok
from app.ui import controlador as ctl
from app.ui.mensajes import mensaje_de_error

ESTILO = {"fontFamily": "system-ui, sans-serif", "maxWidth": "1100px", "margin": "0 auto", "padding": "16px"}
CAJA = {"border": "1px solid #ccc", "borderRadius": "8px", "padding": "12px", "marginBottom": "16px"}
COLORES_PRIO = {Prioridad.ALTA: "#c0392b", Prioridad.MEDIA: "#d68910", Prioridad.BAJA: "#2874a6"}


def a_int(texto: str) -> int | None:
    """'' -> None (sin valor); '3' -> 3."""
    return int(texto) if texto.strip().isdigit() else None


def valor(evento) -> str:
    return evento["target"]["value"]


def opciones(pares, vacio: str | None = None):
    base = [html.option({"value": ""}, vacio)] if vacio is not None else []
    return base + [html.option({"value": str(v), "key": str(v)}, etiqueta) for v, etiqueta in pares]


def vista_inicial(repo):
    match ctl.cargar_vista(repo, None):
        case Ok(v):
            return v
        case Err():
            return ctl.Vista()


@component
def Campo(etiqueta, texto, al_cambiar, placeholder=""):
    return html.label({"style": {"marginRight": "8px"}}, etiqueta + " ",
                      html.input({"value": texto, "placeholder": placeholder,
                                  "on_change": lambda e: al_cambiar(valor(e))}))


@component
def Tarjeta(tarea, nombre_responsable, integrantes, ejecutar):
    destino, set_destino = use_state(tarea.estado.name)
    asignado, set_asignado = use_state(str(tarea.responsable_id or ""))
    return html.div(
        {"style": {"border": "1px solid #bbb", "borderLeft": f"6px solid {COLORES_PRIO[tarea.prioridad]}",
                                    "borderRadius": "6px", "padding": "8px", "marginBottom": "8px", "background": "#fff"}},
        html.strong(f"#{tarea.id} {tarea.titulo}"),
        html.div(f"Responsable: {nombre_responsable} · Prioridad: {tarea.prioridad.name.title()}"),
        html.div(html.select({"value": destino, "on_change": lambda e: set_destino(valor(e))},
                             *opciones([(e.name, e.value) for e in Estado])),
                 html.button({"on_click": lambda e: ejecutar(CambiarEstado(tarea.id, Estado[destino]), "Tarea movida.")}, "Mover")),
        html.div(html.select({"value": asignado, "on_change": lambda e: set_asignado(valor(e))},
                             *opciones([(i.id, i.nombre) for i in integrantes], "Sin asignar")),
                 html.button({"on_click": lambda e: ejecutar(AsignarResponsable(tarea.id, a_int(asignado)), "Responsable actualizado.")},
                             "Asignar")),
    )


@component
def App(repo):
    vista, set_vista = use_state(lambda: vista_inicial(repo))
    aviso, set_aviso = use_state(("", ""))  # (tipo, texto)
    # formularios
    n_proy, set_n_proy = use_state("")
    d_proy, set_d_proy = use_state("")
    n_int, set_n_int = use_state("")
    n_paq, set_n_paq = use_state("")
    padre, set_padre = use_state("")
    t_titulo, set_t_titulo = use_state("")
    t_paq, set_t_paq = use_state("")
    t_resp, set_t_resp = use_state("")
    t_prio, set_t_prio = use_state(Prioridad.MEDIA.name)
    # filtros
    f_est, set_f_est = use_state("")
    f_resp, set_f_resp = use_state("")
    f_prio, set_f_prio = use_state("")

    pid = vista.proyecto.id if vista.proyecto else None

    def recargar(proyecto_id):
        match ctl.cargar_vista(repo, proyecto_id):
            case Ok(nueva):
                set_vista(nueva)
            case Err(error):
                set_aviso(("error", mensaje_de_error(error)))

    def manejar(resultado, texto_ok, despues=lambda: None):
        match resultado:
            case Ok(_):
                recargar(pid)
                despues()
                set_aviso(("ok", texto_ok))
            case Err(error):
                set_aviso(("error", mensaje_de_error(error)))  # nada se guardó

    def crear_proyecto(_):
        match ctl.crear_proyecto(repo, n_proy, d_proy):
            case Ok(p):
                recargar(p.id); set_n_proy(""); set_d_proy(""); set_aviso(("ok", f"Proyecto «{p.nombre}» creado."))
            case Err(error):
                set_aviso(("error", mensaje_de_error(error)))

    def abrir(texto):
        recargar(a_int(texto))
        set_aviso(("", ""))

    # ---- pantalla sin proyecto ----
    banner = html.div({"style": {"padding": "8px", "borderRadius": "6px", "marginBottom": "12px",
                                 "background": "#fdecea" if aviso[0] == "error" else "#e8f6ec"}}, aviso[1]) if aviso[1] else ""
    if pid is None:
        return html.div({"style": ESTILO}, html.h1("Gestor de proyectos"), banner,
            html.div({"style": CAJA}, html.h3("Nuevo proyecto"),
                     Campo("Nombre", n_proy, set_n_proy), Campo("Descripción", d_proy, set_d_proy),
                     html.button({"on_click": crear_proyecto}, "Crear")),
            html.div({"style": CAJA}, html.h3("Proyectos guardados"),
                     html.ul(*[html.li({"key": p.id}, f"{p.nombre} ",
                                       html.button({"on_click": lambda e, i=p.id: recargar(i)}, "Abrir"))
                               for p in vista.proyectos]) if vista.proyectos
                     else html.p("Todavía no hay proyectos. Crea el primero arriba.")))

    # ---- datos derivados (todo calculado con funciones puras del core) ----
    nombres = {i.id: i.nombre for i in vista.integrantes}
    criterios = filtros.construir_criterios(
        Estado[f_est] if f_est else None, a_int(f_resp), Prioridad[f_prio] if f_prio else None)
    visibles = filtros.ordenar_por_prioridad(filtros.filtrar(vista.tareas, *criterios))
    columnas = filtros.agrupar_por_estado(visibles)
    plano = aplanar_edt(vista.paquetes)
    pend = pendientes_por_integrante(vista.tareas)
    nombre_paquete = {p.id: p.nombre for p in vista.paquetes}

    def ejecutar(comando, texto_ok):
        manejar(ctl.ejecutar_comando(repo, pid, comando), texto_ok)

    def agregar_tarea(_):
        manejar(ctl.agregar_tarea(repo, pid, t_titulo, a_int(t_paq), a_int(t_resp), Prioridad[t_prio]),
                "Tarea creada.", lambda: set_t_titulo(""))

    return html.div({"style": ESTILO},
        html.h1(f"Proyecto: {vista.proyecto.nombre}"),
        html.p(vista.proyecto.descripcion) if vista.proyecto.descripcion else "",
        html.button({"on_click": lambda e: abrir("")}, "← Cambiar de proyecto"),
        banner,
        html.div({"style": CAJA}, html.h3("Integrantes"),
            html.ul(*[html.li({"key": i.id}, f"{i.nombre} — {pend.get(i.id, 0)} tarea(s) pendiente(s)")
                      for i in vista.integrantes]) if vista.integrantes else html.p("Aún no hay integrantes."),
            Campo("Nombre", n_int, set_n_int),
            html.button({"on_click": lambda e: manejar(ctl.agregar_integrante(repo, pid, n_int), "Integrante agregado.",
                                                      lambda: set_n_int(""))}, "Agregar")),
        html.div({"style": CAJA}, html.h3("EDT (entregables y paquetes de trabajo)"),
            html.ul(*[html.li({"key": p.id, "style": {"marginLeft": f"{n * 24}px", "listStyle": "none"}},
                              ("└ " if n else "▪ ") + p.nombre) for p, n in plano])
            if plano else html.p("La EDT está vacía. Agrega un primer entregable."),
            Campo("Nombre", n_paq, set_n_paq),
            html.select({"value": padre, "on_change": lambda e: set_padre(valor(e))},
                        *opciones([(p.id, p.nombre) for p in vista.paquetes], "Entregable de primer nivel")),
            html.button({"on_click": lambda e: manejar(ctl.agregar_paquete(repo, pid, n_paq, a_int(padre)),
                                                      "Paquete agregado.", lambda: set_n_paq(""))}, "Agregar")),
        html.div({"style": CAJA}, html.h3("Nueva tarea"),
            Campo("Título", t_titulo, set_t_titulo),
            html.select({"value": t_paq, "on_change": lambda e: set_t_paq(valor(e))},
                        *opciones([(p.id, p.nombre) for p in vista.paquetes], "Paquete…")),
            html.select({"value": t_resp, "on_change": lambda e: set_t_resp(valor(e))},
                        *opciones([(i.id, i.nombre) for i in vista.integrantes], "Sin asignar")),
            html.select({"value": t_prio, "on_change": lambda e: set_t_prio(valor(e))},
                        *opciones([(p.name, p.name.title()) for p in Prioridad])),
            html.button({"on_click": agregar_tarea}, "Crear tarea")),
        html.div({"style": CAJA}, html.h3("Filtros"),
            html.select({"value": f_est, "on_change": lambda e: set_f_est(valor(e))},
                        *opciones([(s.name, s.value) for s in Estado], "Todos los estados")),
            html.select({"value": f_resp, "on_change": lambda e: set_f_resp(valor(e))},
                        *opciones([(i.id, i.nombre) for i in vista.integrantes], "Todos los responsables")),
            html.select({"value": f_prio, "on_change": lambda e: set_f_prio(valor(e))},
                        *opciones([(p.name, p.name.title()) for p in Prioridad], "Todas las prioridades")),
            html.button({"on_click": lambda e: (set_f_est(""), set_f_resp(""), set_f_prio(""))}, "Limpiar")),
        html.h3("Tablero Kanban"),
        html.p("No hay tareas con ese filtro." if vista.tareas else "Aún no hay tareas. Crea la primera arriba.")
        if not visibles else "",
        html.div({"style": {"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "12px"}},
            *[html.div({"key": e.name, "style": {**CAJA, "background": "#f5f5f5", "marginBottom": "0"}},
                       html.h4(f"{e.value} ({len(columnas[e])})"),
                       *[Tarjeta(t, nombres.get(t.responsable_id, "Sin asignar"), vista.integrantes, ejecutar, key=t.id)
                         for t in columnas[e]])
              for e in Estado]),
    )
