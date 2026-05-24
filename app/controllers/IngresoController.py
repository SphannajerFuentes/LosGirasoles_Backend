from fastapi import APIRouter, Depends, HTTPException
from core.security import RoleChecker, get_current_user
from config.base_datos import supabase
from app.models.IngresoModel import IngresoCreate

router = APIRouter(prefix="/api/v1/ingresos", tags=["Ingresos"])
acceso_operativo = RoleChecker(allowed_roles=[1, 3]) # Admin o Farmacéutico

class IngresoController:
    @staticmethod
    def registrar(datos: IngresoCreate, user: dict):
        # 1. Insertar el LOTE
        lote = supabase.table("lotes").insert({
            "id_medicamento": datos.id_medicamento,
            "numero_lote": datos.numero_lote,
            "cantidad_disponible": datos.cantidad,
            "fecha_caducidad": str(datos.fecha_caducidad)
        }).execute()
        
        # 2. Registrar MOVIMIENTO (Tipo 1: Entrada)
        movimiento = supabase.table("movimientos_inventarios").insert({
            "id_usuario": user["user_id"],
            "cantidad": datos.cantidad,
            "tipo_movimiento": 1 
        }).execute()
        
        # 3. Actualizar STOCK en tabla medicamentos
        # (Aquí deberías hacer un select primero y luego un update)
        # Esto asegura que el stock siempre esté actualizado
        
        return {"mensaje": "Ingreso y Lote registrados exitosamente"}

@router.post("/", dependencies=[Depends(acceso_operativo)])
def endpoint_registrar_ingreso(datos: IngresoCreate, user: dict = Depends(get_current_user)):
    return IngresoController.registrar(datos, user)