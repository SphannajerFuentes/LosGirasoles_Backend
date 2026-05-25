from pydantic import BaseModel, Field

class IncidenciaCreate(BaseModel):
    id_orden_compra: int
    id_proveedor: int
    descripcion: str = Field(..., min_length=10)
    tipo: int # 1: Mercadería Dañada, 2: Discrepancia/Faltante, 3: Retraso