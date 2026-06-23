from pydantic import Field
from app.models.BaseModel import EntidadBase

class IncidenciaCreate(EntidadBase):
    id_orden_compra: int
    id_proveedor: int
    descripcion: str 
    tipo: int = Field(..., description="1: Dañada, 2: Faltante, 3: Retraso")