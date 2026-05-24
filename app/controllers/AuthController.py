from fastapi import APIRouter, HTTPException, status
from config.base_datos import supabase
from app.models.AuthModel import RegistroInput, LoginInput
import bcrypt  # Usamos bcrypt directamente
import base64

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

class AuthController:
    @staticmethod
    def registrar(datos: RegistroInput):
        # 1. Encriptar contraseña (usamos [:72] para evitar errores de longitud de bcrypt)
        password_bytes = datos.contrasena.encode('utf-8')[:72]
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        # 2. Insertar en tabla usuarios
        # Nota: Guardamos el hash como string decodificado a utf-8
        try:
            res = supabase.table("usuarios").insert({
                "nombre": datos.nombre,
                "contrasena": hashed_password.decode('utf-8'),
                "rol": datos.rol  # 1: Admin, 2: Almacenero, 3: Farmacéutico
            }).execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Error al registrar usuario en la base de datos.")
        
        return {"mensaje": "Usuario registrado exitosamente"}

    @staticmethod
    def login(datos: LoginInput):
        # 1. Buscar usuario por nombre
        res = supabase.table("usuarios").select("*").eq("nombre", datos.nombre).execute()
        
        if not res.data:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        user = res.data[0]
        
        # 2. Verificar contraseña
        password_bytes = datos.contrasena.encode('utf-8')[:72]
        hashed_db = user["contrasena"].encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hashed_db):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # 3. Crear token
        token = base64.b64encode(f"user_{user['id']}".encode()).decode()
        
        return {
            "accessToken": token,
            "rol": user["rol"],
            "mensaje": "Login exitoso"
        }

# --- RUTAS ---
@router.post("/register")
def register(payload: RegistroInput):
    return AuthController.registrar(payload)

@router.post("/login")
def login(payload: LoginInput):
    return AuthController.login(payload)