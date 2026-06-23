from fastapi import APIRouter, Depends
from app.core.security import RoleChecker, get_current_user
from app.core.base_controller import BaseController
from app.core.excepciones import NoEncontradoError, ReglaNegocioError
from app.models.OrdenCompraModel import OrdenCompraCreate
from datetime import date

router = APIRouter(prefix="/api/v1/ordenes-compras", tags=["Órdenes de Compra"])

solo_admin = RoleChecker(allowed_roles=[1])
acceso_recepcion = RoleChecker(allowed_roles=[1, 2])

ESTADOS_ORDEN = (1, 2, 3, 4) # 1: Pendiente, 2: OK, 3: Incidencia, 4: Cancelada
TIPO_MOVIMIENTO = (1,) # 1: Entrada

class OrdenCompraController(BaseController):
    
    def _generar_orden_logica(self, datos: OrdenCompraCreate, user: dict):
        orden = self._db.table("ordenes_compras").insert({
            "id_usuario": user["user_id"], 
            "id_proveedor": datos.id_proveedor,
            "fecha_emision": str(datos.fecha_emision),
            "estado_orden": ESTADOS_ORDEN[0]
        }).execute()

        id_orden_generada = orden.data[0]["id"]

        # Comprensión de listas para preparación rápida en memoria
        detalles_insert = [
            {
                "id_orden_compra": id_orden_generada,
                "id_medicamento": detalle.id_medicamento,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario
            } for detalle in datos.detalles
        ]
        self._db.table("detalles_ordenes_compras").insert(detalles_insert).execute()

        return {"mensaje": "Orden de compra generada exitosamente", "id_orden": id_orden_generada}

    def _recepcionar_orden_logica(self, id_orden: int, datos: dict, user: dict):
        operaciones_realizadas = {"lotes": [], "movimientos": [], "incidencias": []}
        
        try:
            orden_info = self._db.table("ordenes_compras").select("id_proveedor").eq("id", id_orden).single().execute()
            if not orden_info.data:
                raise NoEncontradoError("Orden de compra")
                
            id_proveedor = orden_info.data["id_proveedor"]
            hubo_incidencia = False
            todo_cero = True

            for detalle in datos["detalles"]:
                cant_pedida = detalle["cantidad_pedida"]
                cant_recibida = detalle["cantidad_recibida"]
                diferencia = cant_pedida - cant_recibida

                if cant_recibida > 0:
                    todo_cero = False
                    lote_res = self._db.table("lotes").insert({
                        "id_medicamento": detalle["id_medicamento"],
                        "numero_lote": detalle["numero_lote"],
                        "cantidad_disponible": cant_recibida,
                        "fecha_caducidad": str(detalle["fecha_caducidad"]),
                        "estado_fisico": 1,
                        "semaforo": 1
                    }).execute()
                    operaciones_realizadas["lotes"].append(lote_res.data[0]["id"])

                    mov_res = self._db.table("movimientos_inventarios").insert({
                        "id_usuario": user["user_id"],
                        "cantidad": cant_recibida,
                        "tipo_movimiento": TIPO_MOVIMIENTO[0]
                    }).execute()
                    operaciones_realizadas["movimientos"].append(mov_res.data[0]["id"])

                    med = self._db.table("medicamentos").select("stock_actual").eq("id", detalle["id_medicamento"]).single().execute()
                    nuevo_stock = med.data["stock_actual"] + cant_recibida
                    self._db.table("medicamentos").update({"stock_actual": nuevo_stock}).eq("id", detalle["id_medicamento"]).execute()

                if diferencia > 0:
                    hubo_incidencia = True
                    motivo = detalle.get("tipo_incidencia", 2)
                    desc = f"Discrepancia: Pedidos {cant_pedida}, Recibidos {cant_recibida}. Faltante: {diferencia} uds."
                    
                    inc_res = self._db.table("incidencias").insert({
                        "id_orden_compra": id_orden,
                        "id_proveedor": id_proveedor,
                        "descripcion": desc,
                        "tipo": motivo,
                        "estado_incidencia": 1
                    }).execute()
                    operaciones_realizadas["incidencias"].append(inc_res.data[0]["id"])

            nuevo_estado_orden = ESTADOS_ORDEN[3] if todo_cero else (ESTADOS_ORDEN[2] if hubo_incidencia else ESTADOS_ORDEN[1])

            self._db.table("ordenes_compras").update({
                "estado_orden": nuevo_estado_orden,
                "fecha_entrega": str(date.today())
            }).eq("id", id_orden).execute()

            return {"mensaje": "Recepción procesada.", "estado_final": nuevo_estado_orden, "incidencias_generadas": hubo_incidencia}

        except Exception as e:
            # Control de transacciones manual encapsulado
            for mov_id in operaciones_realizadas["movimientos"]:
                self._db.table("movimientos_inventarios").delete().eq("id", mov_id).execute()
            for lote_id in operaciones_realizadas["lotes"]:
                self._db.table("lotes").delete().eq("id", lote_id).execute()
            for inc_id in operaciones_realizadas["incidencias"]:
                self._db.table("incidencias").delete().eq("id", inc_id).execute()
            
            # Lanzamos para que _safe_execute atrape el problema grave
            raise ReglaNegocioError(f"Fallo crítico en recepción. Operación revertida. Detalle: {str(e)}")

    def _listar_ordenes_logica(self):
        response = self._db.table("ordenes_compras").select("id, id_proveedor, fecha_emision, estado_orden, proveedores(nombre)").eq("estado_orden", 1).execute()
        return [
            {
                "id": o["id"],
                "proveedor_nombre": o["proveedores"]["nombre"] if o["proveedores"] else "N/A",
                "proveedor_id": o["id_proveedor"],
                "estado": o["estado_orden"]
            } for o in response.data
        ]

    def _listar_detalle_logica(self, id_orden: int):
        response = self._db.table("detalles_ordenes_compras").select("*, medicamentos(nombre)").eq("id_orden_compra", id_orden).execute()
        return [
            {
                "id_medicamento": d["id_medicamento"],
                "medicamento_nombre": d["medicamentos"]["nombre"] if d["medicamentos"] else "Desconocido",
                "cantidad": d["cantidad"],
                "precio_unitario": d["precio_unitario"]
            } for d in response.data
        ]

    # Wrappers de Ejecución Segura
    def generar_orden(self, datos: OrdenCompraCreate, user: dict):
        return self._safe_execute(self._generar_orden_logica, datos, user)

    def recepcionar_orden(self, id_orden: int, datos: dict, user: dict):
        return self._safe_execute(self._recepcionar_orden_logica, id_orden, datos, user)

    def listar_ordenes(self):
        return self._safe_execute(self._listar_ordenes_logica)

    def listar_detalle(self, id_orden: int):
        return self._safe_execute(self._listar_detalle_logica, id_orden)

orden_ctrl = OrdenCompraController()

@router.get("/", dependencies=[Depends(acceso_recepcion)])
def obtener_ordenes(estado: int = 1):
    return orden_ctrl.listar_ordenes()

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_orden(payload: OrdenCompraCreate, user: dict = Depends(get_current_user)):
    return orden_ctrl.generar_orden(payload, user)

@router.put("/{id_orden}/recepcionar", dependencies=[Depends(acceso_recepcion)])
def recepcionar_orden_compra(id_orden: int, payload: dict, user: dict = Depends(get_current_user)):
    return orden_ctrl.recepcionar_orden(id_orden, payload, user)

@router.get("/{id_orden}/detalle", dependencies=[Depends(acceso_recepcion)])
def obtener_detalle_orden(id_orden: int):
    return orden_ctrl.listar_detalle(id_orden)