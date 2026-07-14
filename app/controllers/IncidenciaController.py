from fastapi import APIRouter, Depends
from app.core.security import RoleChecker, get_current_user
from app.core.base_controller import BaseController
from app.models.IncidenciaModel import IncidenciaCreate

router = APIRouter(prefix="/api/v1/incidencias", tags=["Incidencias"])
acceso_reporte = RoleChecker(allowed_roles=[1, 2])

# TUPLAS de estado inmutables
ESTADOS_INCIDENCIA = (1, 2) # 1: Abierta, 2: Resuelta
ESTADOS_ORDEN = (4,) # 4: Con Incidencia

class IncidenciaController(BaseController):
    
    def _reportar_logica(self, datos: IncidenciaCreate, user: dict):
        incidencia = self._db.table("incidencias").insert({
            "id_orden_compra": datos.id_orden_compra,
            "id_proveedor": datos.id_proveedor,
            "descripcion": datos.descripcion,
            "tipo": datos.tipo,
            "estado_incidencia": ESTADOS_INCIDENCIA[0]
        }).execute()

        self._db.table("ordenes_compras").update({
            "estado_orden": ESTADOS_ORDEN[0]
        }).eq("id", datos.id_orden_compra).execute()

        return {
            "mensaje": "Incidencia reportada y vinculada a la orden de compra.",
            "id_incidencia": incidencia.data[0]["id"]
        }
        
    def _listar_incidencias_logica(self):
        response = self._db.table("incidencias").select(
            "id, id_orden_compra, descripcion, tipo, estado_incidencia, creado_el, proveedores(nombre)"
        ).order("creado_el", desc=True).execute()
        
        # Comprensión de listas limpia
        return [
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

    def _resolver_incidencia_logica(self, id_incidencia: int):
        self._db.table("incidencias").update({"estado_incidencia": ESTADOS_INCIDENCIA[1]}).eq("id", id_incidencia).execute()
        return {"mensaje": "Incidencia marcada como resuelta."}

    # Métodos Públicos
    def reportar(self, datos: IncidenciaCreate, user: dict):
        return self._safe_execute(self._reportar_logica, datos, user)
        
    def listar_incidencias(self):
        return self._safe_execute(self._listar_incidencias_logica)
        
    def resolver_incidencia(self, id_incidencia: int):
        return self._safe_execute(self._resolver_incidencia_logica, id_incidencia)

incidencia_ctrl = IncidenciaController()

@router.get("/", dependencies=[Depends(acceso_reporte)])
def obtener_incidencias():
    return incidencia_ctrl.listar_incidencias()

@router.put("/{id_incidencia}/resolver", dependencies=[Depends(acceso_reporte)])
def resolver(id_incidencia: int):
    return incidencia_ctrl.resolver_incidencia(id_incidencia)

@router.post("/", dependencies=[Depends(acceso_reporte)])
def reportar_incidencia(payload: IncidenciaCreate, user: dict = Depends(get_current_user)):
    return incidencia_ctrl.reportar(payload, user)