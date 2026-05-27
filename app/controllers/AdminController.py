from fastapi import APIRouter, Depends, HTTPException
from core.security import RoleChecker, get_current_user
from config.base_datos import supabase
from app.models.GestionModel import UsuarioCreate, ProveedorCreate
import bcrypt

router = APIRouter(prefix="/api/v1/admin", tags=["Administración"])
solo_admin = RoleChecker(allowed_roles=[1])

class AdminController:
    @staticmethod
    def crear_usuario(datos: UsuarioCreate):
        hashed = bcrypt.hashpw(datos.contrasena.encode('utf-8')[:72], bcrypt.gensalt())
        res = supabase.table("usuarios").insert({
            "nombre": datos.nombre,
            "contrasena": hashed.decode('utf-8'),
            "rol": datos.rol
        }).execute()
        return {"mensaje": "Usuario creado por el administrador"}
    
    @staticmethod
    def listar_usuarios():
        # Excluimos la contraseña por seguridad
        res = supabase.table("usuarios").select("id, nombre, rol, estado").execute()
        return res.data

    @staticmethod
    def crear_proveedor(datos: ProveedorCreate):
        res = supabase.table("proveedores").insert({
            "nombre": datos.nombre,
            "contacto": datos.contacto,
            "telefono": datos.telefono
        }).execute()
        return {"mensaje": "Proveedor registrado exitosamente"}
    
    @staticmethod
    def listar_proveedores():
        # Consulta a Supabase para obtener todos los proveedores
        res = supabase.table("proveedores").select("*").eq("estado", 1).execute()
        return res.data

# Endpoints protegidos
@router.post("/usuarios", dependencies=[Depends(solo_admin)])
def registrar_usuario(payload: UsuarioCreate):
    return AdminController.crear_usuario(payload)

@router.post("/proveedores", dependencies=[Depends(solo_admin)])
def registrar_proveedor(payload: ProveedorCreate):
    return AdminController.crear_proveedor(payload)

@router.get("/proveedores", dependencies=[Depends(solo_admin)])
def obtener_proveedores():
    return AdminController.listar_proveedores()

@router.get("/usuarios", dependencies=[Depends(solo_admin)])
def obtener_usuarios():
    return AdminController.listar_usuarios()