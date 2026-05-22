from pydantic import BaseModel, Field

class LoginInput(BaseModel):
    nombre: str = Field(..., description="Nombre exacto del usuario registrado por el admin")