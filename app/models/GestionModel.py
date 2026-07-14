from pydantic import BaseModel, Field
from typing import List

# --- Modelos de Entidades ---
class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contrasena: str = Field(..., min_length=6)
    rol: int 

class ProveedorCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contacto: str
    telefono: str

# --- Modelos para Operaciones de Inventario (HU08, HU09, HU10) ---
class SalidaItem(BaseModel):
    medicamento_id: int
    cantidad: int

class SalidaMedicamentoRequest(BaseModel):
    items: List[SalidaItem]

class MovimientoDetalleResponse(BaseModel):
    lote_id: int
    cantidad_retirada: int
    fecha_caducidad: str

class SalidaResponse(BaseModel):
    message: str
    detalles_despacho: List[MovimientoDetalleResponse]

class KardexRegistroResponse(BaseModel):
    id: int
    fecha_movimiento: str
    tipo_movimiento: str
    cantidad: int
    lote_codigo: str
    motivo: str

class KardexKardexResponse(BaseModel):
    medicamento_id: int
    nombre: str
    stock_actual: int
    historial: List[KardexRegistroResponse]

class AlertaStockResponse(BaseModel):
    medicamento_id: int
    nombre: str
    stock_actual: int
    stock_minimo: int
    mensaje: str