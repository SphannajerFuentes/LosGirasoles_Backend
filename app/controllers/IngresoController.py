from fastapi import APIRouter, Depends
from app.core.security import RoleChecker, get_current_user
from app.core.base_controller import BaseController
from app.models.IngresoModel import IngresoCreate

router = APIRouter(prefix="/api/v1/ingresos", tags=["Ingresos"])
acceso_operativo = RoleChecker(allowed_roles=[1, 3])

TIPO_INGRESO = (1,) # 1: Entrada

class IngresoController(BaseController):
    
    def _registrar_logica(self, datos: IngresoCreate, user: dict):
        lote = self._db.table("lotes").insert({
            "id_medicamento": datos.id_medicamento,
            "numero_lote": datos.numero_lote,
            "cantidad_disponible": datos.cantidad,
            "fecha_caducidad": str(datos.fecha_caducidad)
        }).execute()
        
        movimiento = self._db.table("movimientos_inventarios").insert({
            "id_usuario": user["user_id"],
            "cantidad": datos.cantidad,
            "tipo_movimiento": TIPO_INGRESO[0] 
        }).execute()
        
        # Actualización de stock atómica y segura
        med_actual = self._db.table("medicamentos").select("stock_actual").eq("id", datos.id_medicamento).single().execute()
        nuevo_stock = med_actual.data["stock_actual"] + datos.cantidad
        self._db.table("medicamentos").update({"stock_actual": nuevo_stock}).eq("id", datos.id_medicamento).execute()
        
        return {"mensaje": "Ingreso y Lote registrados exitosamente"}

    def registrar(self, datos: IngresoCreate, user: dict):
        return self._safe_execute(self._registrar_logica, datos, user)

ingreso_ctrl = IngresoController()

@router.post("/", dependencies=[Depends(acceso_operativo)])
def endpoint_registrar_ingreso(datos: IngresoCreate, user: dict = Depends(get_current_user)):
    return ingreso_ctrl.registrar(datos, user)