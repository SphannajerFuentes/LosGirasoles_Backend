from pydantic import BaseModel
from datetime import date

class IngresoCreate(BaseModel):
    id_medicamento: int
    numero_lote: str
    cantidad: int
    fecha_caducidad: date
    # id_usuario vendrá del token (seguridad), no del JSON