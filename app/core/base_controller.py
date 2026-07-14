from config.base_datos import supabase
from app.core.excepciones import InventarioException
import logging

class BaseController:
    """Clase Padre para todos los controladores. Encapsula la BD y ejecución segura."""
    def __init__(self):
        # Atributo protegido
        self._db = supabase

    def _safe_execute(self, funcion_logica, *args, **kwargs):
        """Método protegido (Encapsulamiento) para ejecutar lógica y capturar errores."""
        try:
            return funcion_logica(*args, **kwargs)
        except InventarioException as ie:
            raise ie
        except Exception as e:
            logging.error(f"Error en ejecución segura: {str(e)}")
            raise InventarioException(mensaje=f"Error en operación: {str(e)}")