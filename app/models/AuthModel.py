from pydantic import BaseModel, Field

class RegistroInput(BaseModel):
    nombre: str = Field(..., min_length=3)
    contrasena: str = Field(..., min_length=6)
    rol: int

class LoginInput(BaseModel):
    nombre: str
    contrasena: str