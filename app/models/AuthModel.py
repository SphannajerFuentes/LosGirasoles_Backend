from pydantic import BaseModel, Field

class RegistroInput(BaseModel):
    nombre: str
    contrasena: str
    rol: int  # 1: Admin, 2: Almacenero, 3: Farmacéutico

class LoginInput(BaseModel):
    nombre: str
    contrasena: str