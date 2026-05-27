from fastapi import APIRouter, Depends, HTTPException
from core.security import RoleChecker, get_current_user
from config.base_datos import supabase
from app.models.IncidenciaModel import IncidenciaCreate

router = APIRouter(prefix="/api/v1/incidencias", tags=["Incidencias"])

# Tanto Admin (1) como Almacenero (2) pueden reportar que algo llegó mal
acceso_reporte = RoleChecker(allowed_roles=[1, 2])

class IncidenciaController:
    @staticmethod
    def reportar(datos: IncidenciaCreate, user: dict):
        try:
            # 1. Registrar el problema en la tabla incidencias
            incidencia = supabase.table("incidencias").insert({
                "id_orden_compra": datos.id_orden_compra,
                "id_proveedor": datos.id_proveedor,
                "descripcion": datos.descripcion,
                "tipo": datos.tipo,
                "estado_incidencia": 1 # 1: Abierta
            }).execute()

            # 2. Cambiar el estado de la Orden de Compra a 4 (Incidencia)
            supabase.table("ordenes_compras").update({
                "estado_orden": 4
            }).eq("id", datos.id_orden_compra).execute()

            return {
                "mensaje": "Incidencia reportada y vinculada a la orden de compra.",
                "id_incidencia": incidencia.data[0]["id"]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al reportar la incidencia")
        
    @staticmethod
    def listar_incidencias():
        try:
            # Traemos las incidencias con información de la orden y el proveedor
            response = supabase.table("incidencias") \
                .select("id, id_orden_compra, descripcion, tipo, estado_incidencia, creado_el, proveedores(nombre)") \
                .order("creado_el", desc=True) \
                .execute()
            
            datos = [
                {
                    "id": i["id"],
                    "orden_id": i["id_orden_compra"],
                    "proveedor": i["proveedores"]["nombre"] if i["proveedores"] else "N/A",
                    "descripcion": i["descripcion"],
                    "tipo": i["tipo"],
                    "estado": i["estado_incidencia"],
                    "fecha": i["creado_el"]
                } for i in response.data
            ]
            return datos
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al listar incidencias")

    @staticmethod
    def resolver_incidencia(id_incidencia: int):
        try:
            # Cambia el estado a "Resuelta" (estado_incidencia = 2)
            supabase.table("incidencias").update({"estado_incidencia": 2}).eq("id", id_incidencia).execute()
            return {"mensaje": "Incidencia marcada como resuelta."}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al resolver la incidencia")

# --- ENDPOINTS ---
@router.get("/", dependencies=[Depends(acceso_reporte)])
def obtener_incidencias():
    return IncidenciaController.listar_incidencias()

@router.put("/{id_incidencia}/resolver", dependencies=[Depends(acceso_reporte)])
def resolver(id_incidencia: int):
    return IncidenciaController.resolver_incidencia(id_incidencia)

@router.post("/", dependencies=[Depends(acceso_reporte)])
def reportar_incidencia(payload: IncidenciaCreate, user: dict = Depends(get_current_user)):
    return IncidenciaController.reportar(payload, user)