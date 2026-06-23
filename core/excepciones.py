from fastapi import Request
from fastapi.responses import JSONResponse
import logging

# TUPLA: Códigos de error inmutables
CODIGOS_HTTP = (400, 401, 403, 404, 409, 500)

class InventarioException(Exception):
    """Clase base (Padre) para excepciones del sistema."""
    def __init__(self, mensaje: str, codigo_estado: int = CODIGOS_HTTP[5]):
        self.mensaje = mensaje
        self.codigo_estado = codigo_estado
        super().__init__(self.mensaje)

class ReglaNegocioError(InventarioException):
    """Excepción (Hija) para validaciones de negocio."""
    def __init__(self, detalle: str, codigo_estado: int = CODIGOS_HTTP[0]):
        super().__init__(mensaje=detalle, codigo_estado=codigo_estado)

class NoEncontradoError(InventarioException):
    """Excepción (Hija) para recursos inexistentes."""
    def __init__(self, recurso: str):
        super().__init__(mensaje=f"No encontrado: {recurso}", codigo_estado=CODIGOS_HTTP[3])

class AutorizacionError(InventarioException):
    """Excepción (Hija) para problemas de tokens o roles."""
    def __init__(self, detalle: str):
        super().__init__(mensaje=detalle, codigo_estado=CODIGOS_HTTP[1])

def configurar_manejadores_errores(app):
    @app.exception_handler(InventarioException)
    async def manejador_inventario(request: Request, exc: InventarioException):
        logging.warning(f"Excepción de Inventario: {exc.mensaje}")
        return JSONResponse(
            status_code=exc.codigo_estado,
            content={"error": True, "tipo": exc.__class__.__name__, "detalle": exc.mensaje}
        )

    @app.exception_handler(Exception)
    async def manejador_global(request: Request, exc: Exception):
        logging.error(f"Fallo crítico no controlado: {str(exc)}")
        return JSONResponse(
            status_code=CODIGOS_HTTP[5],
            content={"error": True, "tipo": "ErrorInterno", "detalle": "Ha ocurrido un error inesperado en el servidor."}
        )