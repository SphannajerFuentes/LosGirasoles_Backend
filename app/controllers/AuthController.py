from fastapi import APIRouter
from core.base_controller import BaseController
from core.excepciones import ReglaNegocioError
from app.models.AuthModel import RegistroInput, LoginInput
import bcrypt
import base64

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

# HERENCIA de BaseController
class AuthController(BaseController):
    
    # Encapsulamiento: Lógica privada pura
    def _registrar_logica(self, datos: RegistroInput):
        password_bytes = datos.contrasena.encode('utf-8')[:72]
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        self._db.table("usuarios").insert({
            "nombre": datos.nombre,
            "contrasena": hashed_password.decode('utf-8'),
            "rol": datos.rol 
        }).execute()
        return {"mensaje": "Usuario registrado exitosamente"}

    def _login_logica(self, datos: LoginInput):
        resultado = self._db.table("usuarios").select("*").eq("nombre", datos.nombre).execute()
        if not resultado.data:
            raise ReglaNegocioError("Credenciales incorrectas", 401)
        
        usuario = resultado.data[0]
        password_bytes = datos.contrasena.encode('utf-8')[:72]
        hashed_db = usuario["contrasena"].encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hashed_db):
            raise ReglaNegocioError("Credenciales incorrectas", 401)
        
        token = base64.b64encode(f"user_{usuario['id']}".encode()).decode()
        return {"accessToken": token, "rol": usuario["rol"], "mensaje": "Login exitoso"}

    # Métodos públicos que usan el enrutador de errores
    def registrar(self, datos: RegistroInput):
        return self._safe_execute(self._registrar_logica, datos)

    def login(self, datos: LoginInput):
        return self._safe_execute(self._login_logica, datos)

# Instanciamos el objeto
auth_ctrl = AuthController()

@router.post("/register")
def register(payload: RegistroInput):
    return auth_ctrl.registrar(payload)

@router.post("/login")
def login(payload: LoginInput):
    return auth_ctrl.login(payload)