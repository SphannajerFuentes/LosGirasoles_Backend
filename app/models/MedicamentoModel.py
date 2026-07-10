from pydantic import BaseModel

class MedicamentoCreate(BaseModel):
    nombre: str
    principio_activo: str
    presentacion: str
    precio: float
    stock_actual: int = 0
    stock_maximo: int
    stock_minimo: int
    punto_reorden: int
    categoria_abc: str  # 'A', 'B' o 'C'