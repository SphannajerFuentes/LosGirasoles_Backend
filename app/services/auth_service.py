# logistica-backend/app/services/auth_service.py
from fastapi import HTTPException, status
from app.db.supabase import supabase
from app.schemas.auth import LoginInput
import base64

class AuthService:
    @staticmethod
    def iniciar_sesion(datos: LoginInput):
        try:
            # Limpiamos espacios extras alrededor del texto ingresado
            nombre_limpio = datos.nombre.strip()
            
            # .ilike hace que 'Sphannajer', 'SPHANNAJER' o 'sphannajer' sean válidos
            respuesta = supabase.table("usuario").select("*").ilike("nombre", nombre_limpio).execute()
            
            # Si no hay coincidencias
            if not respuesta.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado en el sistema. Verifique el nombre o contacte al administrador."
                )
            
            user = respuesta.data[0]
            
            # Generamos el token de sesión simulado
            token_simulado = base64.b64encode(f"user_{user['id']}".encode()).decode()
                
            return {
                "access_token": token_simulado,
                "token_type": "bearer",
                "user": {
                    "id": str(user["id"]),
                    "nombre": user["nombre"],
                    "rol": user["rol"]
                }
            }
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"Error interno en el servidor: {str(e)}"
            )