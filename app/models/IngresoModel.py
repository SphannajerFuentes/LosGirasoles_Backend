from datetime import date
from app.models.BaseModel import EntidadBase

class IngresoCreate(EntidadBase):
    id_medicamento: int
    numero_lote: str
    cantidad: int
    fecha_caducidad: date