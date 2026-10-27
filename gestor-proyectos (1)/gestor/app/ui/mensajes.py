"""Shell: convierte errores del núcleo en mensajes para personas (pattern matching)."""
from app.domain.errors import (ErrorPersistencia, NombreVacio, PaqueteNoExiste,
                               ResponsableNoExiste, TareaNoExiste, TituloVacio,
                               TransicionInvalida)


def mensaje_de_error(error) -> str:
    match error:
        case TituloVacio():
            return "El título de la tarea no puede estar vacío."
        case NombreVacio(campo):
            return f"El nombre de {campo} no puede estar vacío."
        case TransicionInvalida(origen, destino):
            return f"No se puede pasar de «{origen.value}» a «{destino.value}»."
        case ResponsableNoExiste(id):
            return f"El integrante #{id} no existe."
        case PaqueteNoExiste(id):
            return f"El paquete #{id} no existe."
        case TareaNoExiste(id):
            return f"La tarea #{id} no existe."
        case ErrorPersistencia(detalle):
            return f"No se pudo guardar o leer en la base de datos: {detalle}"
        case _:
            return "Ocurrió un error inesperado."
