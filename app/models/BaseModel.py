from pydantic import BaseModel, Field
from datetime import date

# TUPLAS: Constantes del sistema
ROLES_SISTEMA = (1, 2, 3) # 1: Admin, 2: Almacenero, 3: Farmacéutico
ESTADOS_SISTEMA = (0, 1)  # 0: Inactivo, 1: Activo

class EntidadBase(BaseModel):
    """Clase Padre para modelos. Estandariza campos comunes de la base de datos."""
    estado: int = Field(default=ESTADOS_SISTEMA[1])
    creado_el: date = Field(default_factory=date.today)