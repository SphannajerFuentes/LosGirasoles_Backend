from fastapi import APIRouter, Depends
from app.core.security import RoleChecker
from app.core.base_controller import BaseController
from app.core.excepciones import ReglaNegocioError
from app.models.GestionModel import UsuarioCreate, ProveedorCreate
import bcrypt

router = APIRouter(prefix="/api/v1/admin", tags=["Administración"])
solo_admin = RoleChecker(allowed_roles=[1])

class AdminController(BaseController):
    
    def _crear_usuario_logica(self, datos: UsuarioCreate):
        hashed = bcrypt.hashpw(datos.contrasena.encode('utf-8')[:72], bcrypt.gensalt())
        self._db.table("usuarios").insert({
            "nombre": datos.nombre,
            "contrasena": hashed.decode('utf-8'),
            "rol": datos.rol
        }).execute()
        return {"mensaje": "Usuario creado por el administrador"}
    
    def _listar_usuarios_logica(self):
        res = self._db.table("usuarios").select("id, nombre, rol, estado").execute()
        return res.data

    def _crear_proveedor_logica(self, datos: ProveedorCreate):
        self._db.table("proveedores").insert({
            "nombre": datos.nombre,
            "contacto": datos.contacto,
            "telefono": datos.telefono
        }).execute()
        return {"mensaje": "Proveedor registrado exitosamente"}
    
    def _listar_proveedores_logica(self):
        res = self._db.table("proveedores").select("*").eq("estado", 1).execute()
        return res.data

    # Métodos públicos
    def crear_usuario(self, datos: UsuarioCreate):
        return self._safe_execute(self._crear_usuario_logica, datos)

    def listar_usuarios(self):
        return self._safe_execute(self._listar_usuarios_logica)

    def crear_proveedor(self, datos: ProveedorCreate):
        return self._safe_execute(self._crear_proveedor_logica, datos)

    def listar_proveedores(self):
        return self._safe_execute(self._listar_proveedores_logica)

admin_ctrl = AdminController()

@router.post("/usuarios", dependencies=[Depends(solo_admin)])
def registrar_usuario(payload: UsuarioCreate):
    return admin_ctrl.crear_usuario(payload)

@router.post("/proveedores", dependencies=[Depends(solo_admin)])
def registrar_proveedor(payload: ProveedorCreate):
    return admin_ctrl.crear_proveedor(payload)

@router.get("/proveedores", dependencies=[Depends(solo_admin)])
def obtener_proveedores():
    return admin_ctrl.listar_proveedores()

@router.get("/usuarios", dependencies=[Depends(solo_admin)])
def obtener_usuarios():
    return admin_ctrl.listar_usuarios()