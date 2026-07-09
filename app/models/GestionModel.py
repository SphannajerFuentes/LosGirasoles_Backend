# app/models/GestionModel.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contrasena: str = Field(..., min_length=6)
    rol: int # 1, 2 o 3

class ProveedorCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contacto: str
    telefono: str

# --- HU08: MODELOS PARA SALIDAS (VENTAS FIFO) ---
class SalidaItem(BaseModel):
    medicamento_id: int = Field(..., description="ID del medicamento vendido")
    cantidad: int = Field(..., gt=0, description="Cantidad a retirar (debe ser mayor a 0)")

class SalidaMedicamentoRequest(BaseModel):
    items: List[SalidaItem]

class MovimientoDetalleResponse(BaseModel):
    lote_id: int
    cantidad_retirada: int
    fecha_caducidad: str

class SalidaResponse(BaseModel):
    status: str = "success"
    message: str
    detalles_despacho: List[MovimientoDetalleResponse]


# =====================================================================
# --- HU08: MODELOS PARA SALIDAS (VENTAS FIFO) ---
# =====================================================================
class SalidaItem(BaseModel):
    # Mantenemos medicamento_id aquí para el JSON que envía el Frontend
    medicamento_id: int = Field(..., description="ID del medicamento vendido")
    cantidad: int = Field(..., gt=0, description="Cantidad a retirar")

class SalidaMedicamentoRequest(BaseModel):
    items: List[SalidaItem]

class MovimientoDetalleResponse(BaseModel):
    lote_id: int
    cantidad_retirada: int
    fecha_caducidad: str

class SalidaResponse(BaseModel):
    status: str = "success"
    message: str
    detalles_despacho: List[MovimientoDetalleResponse]


# =====================================================================
# --- HU09: MODELOS PARA KARDEX ---
# =====================================================================
class KardexRegistroResponse(BaseModel):
    id: int
    fecha_movimiento: datetime
    tipo_movimiento: str       # Mapeado a texto ('INGRESO' / 'SALIDA') para el cliente
    cantidad: int
    numero_lote: Optional[str] = None  # Corregido: se alineó con 'numero_lote' de tu BD
    motivo: Optional[str] = None

class KardexKardexResponse(BaseModel):
    medicamento_id: int
    nombre: str
    stock_actual: int
    historial: List[KardexRegistroResponse]


# =====================================================================
# --- HU10: MODELOS PARA ALERTAS ---
# =====================================================================
class AlertaStockResponse(BaseModel):
    medicamento_id: int
    nombre: str
    stock_actual: int
    punto_reorden: int  # Corregido: se alineó con el nombre real de tu columna en 'medicamentos'
    mensaje: str