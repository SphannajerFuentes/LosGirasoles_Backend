from pydantic import BaseModel
from datetime import date
from typing import List
from app.models.BaseModel import EntidadBase

class DetalleOrden(BaseModel):
    id_medicamento: int
    cantidad: int
    precio_unitario: float

class OrdenCompraCreate(EntidadBase):
    id_proveedor: int
    fecha_emision: date
    detalles: List[DetalleOrden]

class DetalleRecepcion(BaseModel):
    id_medicamento: int
    cantidad_recibida: int
    numero_lote: str
    fecha_caducidad: date

class RecepcionOrdenCreate(BaseModel):
    detalles: List[DetalleRecepcion]