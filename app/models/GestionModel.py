# app/models/GestionModel.py
from pydantic import BaseModel, Field

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contrasena: str = Field(..., min_length=6)
    rol: int # 1, 2 o 3

class ProveedorCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150)
    contacto: str
    telefono: str