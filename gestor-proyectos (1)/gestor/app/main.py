"""Ensamble: crea el repositorio SQLite, la app FastAPI y monta ReactPy. Sin endpoints propios."""
import logging
import os

from fastapi import FastAPI
from reactpy import component
from reactpy.backend.fastapi import configure

from app.adapters.sqlite_repo import RepositorioSQLite
from app.ui.app import App

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

repo = RepositorioSQLite.abrir(os.environ.get("GESTOR_DB", "gestor.db"))


@component
def Raiz():
    return App(repo)


app = FastAPI()
configure(app, Raiz)
