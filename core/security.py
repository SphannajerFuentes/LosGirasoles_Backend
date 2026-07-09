from fastapi import HTTPException, Depends, Header
from config.base_datos import supabase
import base64

def get_current_user(authorization: str = Header(...)):
    try:
        # 1. Tu token viene como "Bearer <token_base64>"
        token = authorization.replace("Bearer ", "")
        
        # 2. Decodificamos el ID que pusiste en el token (ej: "user_1")
        decoded_id = base64.b64decode(token).decode().split("_")[1]
        
        # 3. Consultamos el rol REAL en tu tabla de Base de Datos
        user = supabase.table("usuarios").select("id, rol").eq("id", decoded_id).single().execute()
        
        if not user.data:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
            
        return {"user_id": user.data["id"], "role": user.data["rol"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

# 🚀 AGREGA ESTA CLASE COMPLETA AQUÍ ABAJO:
class RoleChecker:
    def __init__(self, allowed_roles: list[int]): # Cambiado a list[int]
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        # Ahora comparamos int con int
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail="No tienes permisos suficientes para realizar esta acción"
            )
        return current_user
