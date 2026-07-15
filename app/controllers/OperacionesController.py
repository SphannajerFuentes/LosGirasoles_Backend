from fastapi import APIRouter, Depends
from app.core.base_controller import BaseController
from app.core.excepciones import ReglaNegocioError, NoEncontradoError
from app.core.security import RoleChecker, get_current_user
from app.models.GestionModel import (
    SalidaMedicamentoRequest, SalidaResponse, MovimientoDetalleResponse,
    KardexKardexResponse, KardexRegistroResponse
)
from datetime import date, timedelta

router = APIRouter(prefix="/api/v1/operations", tags=["Operaciones Inventario"])

# REGLA APLICADA: Tuplas inmutables para Constantes del sistema
TIPOS_MOVIMIENTO = (1, 2)  # 1: Ingreso, 2: Salida
MOTIVOS_SALIDA = (1, 2, 3) # 1: Venta, 2: Merma, 3: Vencimiento
ESTADOS_ORDEN = (1, 2)     # 1: Pendiente, 2: Completada

# REGLA APLICADA: Herencia de BaseController
class OperacionesController(BaseController):
    
    def _registrar_salida_logica(self, payload: SalidaMedicamentoRequest, current_user: dict):
        detalles_despacho = []
        medicamentos_validados = {}

        # FASE 1: Validación previa exhaustiva (Evita escrituras si algo va a fallar)
        for item in payload.items:
            respuesta_medicamento = self._db.table("medicamentos").select(
                "id, nombre, stock_actual, stock_maximo, punto_reorden"
            ).eq("id", item.medicamento_id).single().execute()
            
            if not respuesta_medicamento.data:
                raise NoEncontradoError(f"Medicamento ID {item.medicamento_id}")
            
            medicamento = respuesta_medicamento.data
            
            fecha_limite = str(date.today() + timedelta(days=15))

            lotes = (
                self._db.table("lotes")
                .select("id, cantidad_disponible, fecha_caducidad")
                .eq("id_medicamento", item.medicamento_id)
                .gt("cantidad_disponible", 0)
                .gt("fecha_caducidad", fecha_limite)
                .order("fecha_caducidad", desc=False)
                .execute()
            )

            stock_disponible = sum(
                lote["cantidad_disponible"]
                for lote in lotes.data
            )

            if stock_disponible < item.cantidad:
                raise ReglaNegocioError(
                    "No existe stock disponible. Los lotes restantes están próximos a vencer."
                )
            
            # Guardamos en memoria para no volver a consultar en la fase de escritura
            medicamentos_validados[item.medicamento_id] = medicamento

        # FASE 2: Procesamiento y Escritura (FEFO)
        for item in payload.items:
            medicamento = medicamentos_validados[item.medicamento_id]
            
            # Consumir lotes mediante FEFO (First Expired, First Out)
            fecha_limite = str(date.today() + timedelta(days=15))

            lotes_query = (
                self._db.table("lotes")
                .select("id, cantidad_disponible, fecha_caducidad")
                .eq("id_medicamento", item.medicamento_id)
                .gt("cantidad_disponible", 0)
                .gt("fecha_caducidad", fecha_limite)
                .order("fecha_caducidad", desc=False)
                .execute()
            )
            
            cantidad_por_restar = item.cantidad
            
            for lote in lotes_query.data:
                if cantidad_por_restar <= 0: 
                    break
                
                stock_lote = lote["cantidad_disponible"]
                retirado = min(stock_lote, cantidad_por_restar)
                nuevo_stock_lote = stock_lote - retirado
                
                # Actualizar stock del lote
                self._db.table("lotes").update({"cantidad_disponible": nuevo_stock_lote}).eq("id", lote["id"]).execute()
                
                # Registrar movimiento
                movimiento = self._db.table("movimientos_inventarios").insert({
                    "id_usuario": current_user["user_id"],
                    "cantidad": retirado, 
                    "tipo_movimiento": TIPOS_MOVIMIENTO[1], # 2: Salida
                    "motivo_salida": MOTIVOS_SALIDA[0],     # 1: Venta
                    "estado": 1
                }).execute()
                
                # Registrar en Kardex
                self._db.table("kardex").insert({
                    "id_lote": lote["id"], 
                    "id_movimiento_inventario": movimiento.data[0]["id"], 
                    "saldo_actual": nuevo_stock_lote, 
                    "estado": 1
                }).execute()
                
                detalles_despacho.append(MovimientoDetalleResponse(
                    lote_id=lote["id"], 
                    cantidad_retirada=retirado, 
                    fecha_caducidad=str(lote["fecha_caducidad"])
                ))
                cantidad_por_restar -= retirado
            
            # Actualizar el stock global del medicamento
            nuevo_stock = medicamento["stock_actual"] - item.cantidad
            self._db.table("medicamentos").update({"stock_actual": nuevo_stock}).eq("id", item.medicamento_id).execute()
            
            # Motor de Reposición Automática Inteligente
            limite = medicamento["punto_reorden"] if medicamento["punto_reorden"] is not None else 10
            stock_max = medicamento["stock_maximo"] if medicamento["stock_maximo"] is not None else 100
            
            if nuevo_stock <= limite:
                cantidad_a_pedir = stock_max - nuevo_stock
                if cantidad_a_pedir > 0:
                    proveedor_id = 1
                    orden_existente = self._db.table("ordenes_compras") \
                        .select("id") \
                        .eq("id_proveedor", proveedor_id) \
                        .eq("estado_orden", ESTADOS_ORDEN[0]) \
                        .execute()
                    
                    if orden_existente.data:
                        id_orden = orden_existente.data[0]["id"]
                        detalle_existente = self._db.table("detalles_ordenes_compras") \
                            .select("id_medicamento") \
                            .eq("id_orden_compra", id_orden) \
                            .eq("id_medicamento", item.medicamento_id) \
                            .execute()
                        
                        if not detalle_existente.data:
                            self._db.table("detalles_ordenes_compras").insert({
                                "id_orden_compra": id_orden,
                                "id_medicamento": item.medicamento_id,
                                "cantidad": cantidad_a_pedir,
                                "precio_unitario": 0.00
                            }).execute()
                    else:
                        nueva_orden = self._db.table("ordenes_compras").insert({
                            "id_usuario": current_user["user_id"],
                            "id_proveedor": proveedor_id,
                            "estado_orden": ESTADOS_ORDEN[0],
                            "fecha_emision": str(date.today())
                        }).execute()
                        
                        id_orden_generada = nueva_orden.data[0]["id"]
                        
                        self._db.table("detalles_ordenes_compras").insert({
                            "id_orden_compra": id_orden_generada,
                            "id_medicamento": item.medicamento_id,
                            "cantidad": cantidad_a_pedir,
                            "precio_unitario": 0.00
                        }).execute()
        
        return SalidaResponse(message="Despacho exitoso y reposición evaluada.", detalles_despacho=detalles_despacho)

    def _obtener_lotes_fefo_logica(self):
        respuesta = self._db.table("lotes").select("id, numero_lote, cantidad_disponible, fecha_caducidad, medicamentos(nombre)").gt("cantidad_disponible", 0).order("fecha_caducidad", desc=False).execute()
        hoy = date.today()
        # REGLA APLICADA: Lista por comprensión (List Comprehension)
        datos = [
            {
                **lote, 
                "medicamento_nombre": lote["medicamentos"]["nombre"], 
                "dias_para_vencer": (date.fromisoformat(lote["fecha_caducidad"]) - hoy).days, 
                "semaforo": "ROJO" if (date.fromisoformat(lote["fecha_caducidad"]) - hoy).days <= 90 else ("AMARILLO" if (date.fromisoformat(lote["fecha_caducidad"]) - hoy).days <= 180 else "VERDE")
            }
            for lote in respuesta.data
        ]
        return datos

    def _obtener_kardex_medicamento_logica(self, medicamento_id: int):
        med = self._db.table("medicamentos").select("id, nombre, stock_actual").eq("id", medicamento_id).single().execute()
        if not med.data: 
            raise NoEncontradoError("Medicamento")
            
        lotes = self._db.table("lotes").select("id, numero_lote").eq("id_medicamento", medicamento_id).execute()
        lotes_map = {lote["id"]: lote["numero_lote"] for lote in lotes.data} # DICCIONARIO
        
        if not lotes_map:
            return KardexKardexResponse(medicamento_id=med.data["id"], nombre=med.data["nombre"], stock_actual=med.data["stock_actual"], historial=[])
            
        kardex = self._db.table("kardex").select("id, creado_el, saldo_actual, id_lote, id_movimiento_inventario").in_("id_lote", list(lotes_map.keys())).order("creado_el", desc=True).execute()
        
        historial = []
        for reg in kardex.data:
            mov = self._db.table("movimientos_inventarios").select("cantidad, tipo_movimiento").eq("id", reg["id_movimiento_inventario"]).single().execute()
            historial.append(KardexRegistroResponse(
                id=reg["id"], 
                fecha_movimiento=reg["creado_el"], 
                tipo_movimiento="SALIDA" if mov.data["tipo_movimiento"] == TIPOS_MOVIMIENTO[1] else "INGRESO", 
                cantidad=mov.data["cantidad"], 
                lote_codigo=lotes_map.get(reg["id_lote"]), 
                motivo=f"Saldo: {reg['saldo_actual']}"
            ))
            
        return KardexKardexResponse(medicamento_id=med.data["id"], nombre=med.data["nombre"], stock_actual=med.data["stock_actual"], historial=historial)

    def _verificar_alertas_logica(self):
        alertas = []
        meds = self._db.table("medicamentos").select("id, nombre, stock_actual, punto_reorden").execute()
        
        # REGLA APLICADA: Comprensión de listas iterando con nombres claros
        alertas.extend([
            {"id": f"stock-{m['id']}", "medicamento": m["nombre"], "tipo": "critico", "mensaje": f"Stock bajo: {m['stock_actual']} uds."}
            for m in meds.data if m["stock_actual"] <= (m["punto_reorden"] or 10)
        ])
        
        ordenes = self._db.table("ordenes_compras").select("id").eq("estado_orden", ESTADOS_ORDEN[0]).execute()
        alertas.extend([
            {"id": f"auto-{o['id']}", "medicamento": "Pedido Pendiente", "tipo": "advertencia", "mensaje": f"Orden de compra N°{o['id']} pendiente."}
            for o in ordenes.data
        ])
        
        return alertas
        
    def _obtener_kpis_logica(self):
        meds = self._db.table("medicamentos").select("stock_actual").execute()
        stock_total = sum(m["stock_actual"] for m in meds.data if m["stock_actual"])
        
        hoy_str = str(date.today())
        movs_hoy = self._db.table("movimientos_inventarios").select("cantidad, creado_el").eq("tipo_movimiento", TIPOS_MOVIMIENTO[1]).execute()
        ventas_hoy_cantidad = sum(m["cantidad"] for m in movs_hoy.data if m["creado_el"].startswith(hoy_str))
        
        limite_fecha = str(date.today() + timedelta(days=90))
        lotes_vencen = self._db.table("lotes").select("id").gt("cantidad_disponible", 0).lte("fecha_caducidad", limite_fecha).execute()
        lotes_por_vencer = len(lotes_vencen.data) if lotes_vencen.data else 0
        
        ordenes = self._db.table("ordenes_compras").select("id").eq("estado_orden", ESTADOS_ORDEN[1]).execute()
        ordenes_recibidas = len(ordenes.data) if ordenes.data else 0
        
        return {
            "stock_total": stock_total, 
            "ventas_hoy": ventas_hoy_cantidad, 
            "lotes_por_vencer": lotes_por_vencer, 
            "ordenes_recibidas": ordenes_recibidas
        }

    # REGLA APLICADA: Métodos públicos actúan como "Wrappers" usando el Manejador Centralizado de Errores
    def registrar_salida(self, payload: SalidaMedicamentoRequest, current_user: dict):
        return self._safe_execute(self._registrar_salida_logica, payload, current_user)

    def obtener_lotes_fefo(self):
        return self._safe_execute(self._obtener_lotes_fefo_logica)

    def obtener_kardex_medicamento(self, medicamento_id: int):
        return self._safe_execute(self._obtener_kardex_medicamento_logica, medicamento_id)

    def verificar_alertas(self):
        return self._safe_execute(self._verificar_alertas_logica)

    def obtener_kpis(self):
        return self._safe_execute(self._obtener_kpis_logica)


# INSTANCIACIÓN DE LA CLASE (Reemplaza el uso estático)
operaciones_ctrl = OperacionesController()

# --- ENDPOINTS ---
@router.post("/salida", dependencies=[Depends(RoleChecker(allowed_roles=[1, 3]))])
def post_salida(payload: SalidaMedicamentoRequest, user: dict = Depends(get_current_user)):
    return operaciones_ctrl.registrar_salida(payload, user)

@router.get("/lotes/fefo", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_lotes(): 
    return operaciones_ctrl.obtener_lotes_fefo()

@router.get("/kardex/{medicamento_id}", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_kardex(medicamento_id: int): 
    return operaciones_ctrl.obtener_kardex_medicamento(medicamento_id)

@router.get("/alertas", dependencies=[Depends(RoleChecker(allowed_roles=[1, 3]))])
def get_alertas(): 
    return operaciones_ctrl.verificar_alertas()

@router.get("/dashboard/kpis", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_kpis(): 
    return operaciones_ctrl.obtener_kpis()