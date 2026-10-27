"""Adaptador SQLite. Cada escritura es una transacción: o se guarda todo o nada."""
import sqlite3
from dataclasses import replace

from app.adapters.decoradores import captura_errores_sqlite, medir
from app.domain.errors import TareaNoExiste
from app.domain.models import Estado, Integrante, Paquete, Prioridad, Proyecto, Tarea
from app.domain.result import Err, Ok

ESQUEMA = """
CREATE TABLE IF NOT EXISTS proyectos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    descripcion TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS integrantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0)
);
CREATE TABLE IF NOT EXISTS paquetes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
    nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    padre_id INTEGER REFERENCES paquetes(id)
);
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
    paquete_id INTEGER NOT NULL REFERENCES paquetes(id),
    titulo TEXT NOT NULL CHECK (length(trim(titulo)) > 0),
    responsable_id INTEGER REFERENCES integrantes(id),
    prioridad INTEGER NOT NULL CHECK (prioridad BETWEEN 1 AND 3),
    estado TEXT NOT NULL CHECK (estado IN ('Pendiente','En progreso','En revisión','Terminada'))
);
"""


class RepositorioSQLite:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._conn.execute("PRAGMA foreign_keys = ON")

    @classmethod
    def abrir(cls, ruta: str = ":memory:") -> "RepositorioSQLite":
        # check_same_thread=False: el servidor puede atender eventos desde otro hilo.
        repo = cls(sqlite3.connect(ruta, check_same_thread=False))
        repo.inicializar()
        return repo

    # --- helpers privados -------------------------------------------------
    def _insertar(self, sql: str, params: tuple) -> int:
        with self._conn:  # commit si todo va bien, rollback si hay excepción
            return self._conn.execute(sql, params).lastrowid

    def _consultar(self, sql: str, params: tuple = ()) -> list[tuple]:
        return self._conn.execute(sql, params).fetchall()

    # --- operaciones ------------------------------------------------------
    @medir
    @captura_errores_sqlite
    def inicializar(self):
        with self._conn:
            self._conn.executescript(ESQUEMA)
        return Ok(None)

    @medir
    @captura_errores_sqlite
    def guardar_proyecto(self, p: Proyecto):
        nuevo_id = self._insertar("INSERT INTO proyectos (nombre, descripcion) VALUES (?, ?)",
                                  (p.nombre, p.descripcion))
        return Ok(replace(p, id=nuevo_id))

    @medir
    @captura_errores_sqlite
    def listar_proyectos(self):
        filas = self._consultar("SELECT id, nombre, descripcion FROM proyectos ORDER BY id")
        return Ok(tuple(Proyecto(id=i, nombre=n, descripcion=d) for i, n, d in filas))

    @medir
    @captura_errores_sqlite
    def guardar_integrante(self, i: Integrante):
        nuevo_id = self._insertar("INSERT INTO integrantes (proyecto_id, nombre) VALUES (?, ?)",
                                  (i.proyecto_id, i.nombre))
        return Ok(replace(i, id=nuevo_id))

    @medir
    @captura_errores_sqlite
    def listar_integrantes(self, proyecto_id: int):
        filas = self._consultar("SELECT id, proyecto_id, nombre FROM integrantes "
                                "WHERE proyecto_id = ? ORDER BY id", (proyecto_id,))
        return Ok(tuple(Integrante(id=i, proyecto_id=p, nombre=n) for i, p, n in filas))

    @medir
    @captura_errores_sqlite
    def guardar_paquete(self, p: Paquete):
        nuevo_id = self._insertar("INSERT INTO paquetes (proyecto_id, nombre, padre_id) VALUES (?, ?, ?)",
                                  (p.proyecto_id, p.nombre, p.padre_id))
        return Ok(replace(p, id=nuevo_id))

    @medir
    @captura_errores_sqlite
    def listar_paquetes(self, proyecto_id: int):
        filas = self._consultar("SELECT id, proyecto_id, nombre, padre_id FROM paquetes "
                                "WHERE proyecto_id = ? ORDER BY id", (proyecto_id,))
        return Ok(tuple(Paquete(id=i, proyecto_id=p, nombre=n, padre_id=pa) for i, p, n, pa in filas))

    @medir
    @captura_errores_sqlite
    def guardar_tarea(self, t: Tarea):
        if t.id is None:
            nuevo_id = self._insertar(
                "INSERT INTO tareas (proyecto_id, paquete_id, titulo, responsable_id, prioridad, estado) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (t.proyecto_id, t.paquete_id, t.titulo, t.responsable_id, t.prioridad.value, t.estado.value))
            return Ok(replace(t, id=nuevo_id))
        with self._conn:
            cur = self._conn.execute(
                "UPDATE tareas SET paquete_id=?, titulo=?, responsable_id=?, prioridad=?, estado=? WHERE id=?",
                (t.paquete_id, t.titulo, t.responsable_id, t.prioridad.value, t.estado.value, t.id))
        return Ok(t) if cur.rowcount else Err(TareaNoExiste(t.id))

    @medir
    @captura_errores_sqlite
    def listar_tareas(self, proyecto_id: int):
        filas = self._consultar(
            "SELECT id, proyecto_id, paquete_id, titulo, responsable_id, prioridad, estado "
            "FROM tareas WHERE proyecto_id = ? ORDER BY id", (proyecto_id,))
        return Ok(tuple(Tarea(id=i, proyecto_id=p, paquete_id=pa, titulo=ti, responsable_id=r,
                              prioridad=Prioridad(pr), estado=Estado(es))
                        for i, p, pa, ti, r, pr, es in filas))
