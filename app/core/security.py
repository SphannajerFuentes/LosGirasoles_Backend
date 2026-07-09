from fastapi import Depends, Header
from config.base_datos import supabase
from app.core.excepciones import AutorizacionError
import base64

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        decoded_id = base64.b64decode(token).decode().split("_")[1]
        
        usuario_db = supabase.table("usuarios").select("id, rol").eq("id", decoded_id).single().execute()
        
        if not usuario_db.data:
            raise AutorizacionError("Usuario no encontrado en el sistema.")
            
        # Retorna un DICCIONARIO
        return {"user_id": usuario_db.data["id"], "role": usuario_db.data["rol"]}
    except Exception:
        raise AutorizacionError("Token inválido o expirado.")

class RoleChecker:
    def __init__(self, allowed_roles: list[int]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in self.allowed_roles:
            raise AutorizacionError("No tienes permisos suficientes para realizar esta acción.")
        return current_user