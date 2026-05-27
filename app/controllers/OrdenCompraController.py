from fastapi import APIRouter, Depends, HTTPException
from core.security import RoleChecker, get_current_user
from config.base_datos import supabase
from app.models.OrdenCompraModel import OrdenCompraCreate, RecepcionOrdenCreate  # Importamos el nuevo modelo
from datetime import date

router = APIRouter(prefix="/api/v1/ordenes-compras", tags=["Órdenes de Compra"])

# Permisos específicos según tu matriz de roles
solo_admin = RoleChecker(allowed_roles=[1])
acceso_recepcion = RoleChecker(allowed_roles=[1, 2]) # 1: Admin, 2: Almacenero

class OrdenCompraController:
    
    @staticmethod
    def generar_orden(datos: OrdenCompraCreate, user: dict):
        try:
            # 1. Insertar Cabecera (Tabla ordenes_compras)
            orden = supabase.table("ordenes_compras").insert({
                "id_usuario": user["user_id"], 
                "id_proveedor": datos.id_proveedor,
                "fecha_emision": str(datos.fecha_emision),
                "estado_orden": 1 # 1: Pendiente
            }).execute()

            id_orden_generada = orden.data[0]["id"]

            # 2. Insertar Detalles (Tabla detalles_ordenes_compras)
            detalles_insert = []
            for detalle in datos.detalles:
                detalles_insert.append({
                    "id_orden_compra": id_orden_generada,
                    "id_medicamento": detalle.id_medicamento,
                    "cantidad": detalle.cantidad,
                    "precio_unitario": detalle.precio_unitario
                })
            
            supabase.table("detalles_ordenes_compras").insert(detalles_insert).execute()

            return {
                "mensaje": "Orden de compra generada exitosamente", 
                "id_orden": id_orden_generada
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al generar la orden de compra")

    @staticmethod
    def recepcionar_orden(id_orden: int, datos: dict, user: dict): # Usamos dict para simplificar el payload flexible
        operaciones_realizadas = {"lotes": [], "movimientos": [], "incidencias": []}
        
        try:
            # 1. Obtener ID del proveedor de esta orden para la incidencia
            orden_info = supabase.table("ordenes_compras").select("id_proveedor").eq("id", id_orden).single().execute()
            if not orden_info.data:
                raise Exception("Orden no encontrada.")
            id_proveedor = orden_info.data["id_proveedor"]

            hubo_incidencia = False
            todo_cero = True

            # 2. Procesar cada detalle
            for detalle in datos["detalles"]:
                cant_pedida = detalle["cantidad_pedida"]
                cant_recibida = detalle["cantidad_recibida"]
                diferencia = cant_pedida - cant_recibida

                # A. Si se recibió algo bueno, entra al inventario
                if cant_recibida > 0:
                    todo_cero = False
                    # Insertar Lote
                    lote_res = supabase.table("lotes").insert({
                        "id_medicamento": detalle["id_medicamento"],
                        "numero_lote": detalle["numero_lote"],
                        "cantidad_disponible": cant_recibida,
                        "fecha_caducidad": str(detalle["fecha_caducidad"]),
                        "estado_fisico": 1,
                        "semaforo": 1
                    }).execute()
                    operaciones_realizadas["lotes"].append(lote_res.data[0]["id"])

                    # Registrar Movimiento
                    mov_res = supabase.table("movimientos_inventarios").insert({
                        "id_usuario": user["user_id"],
                        "cantidad": cant_recibida,
                        "tipo_movimiento": 1 # Entrada
                    }).execute()
                    operaciones_realizadas["movimientos"].append(mov_res.data[0]["id"])

                    # Actualizar Stock Global
                    med = supabase.table("medicamentos").select("stock_actual").eq("id", detalle["id_medicamento"]).single().execute()
                    nuevo_stock = med.data["stock_actual"] + cant_recibida
                    supabase.table("medicamentos").update({"stock_actual": nuevo_stock}).eq("id", detalle["id_medicamento"]).execute()

                # B. Si hubo faltante o producto dañado, generar Incidencia Automática
                if diferencia > 0:
                    hubo_incidencia = True
                    motivo = detalle.get("tipo_incidencia", 2) # Por defecto 2 (Faltante) si no envían nada
                    desc = f"Discrepancia en recepción: Se pidieron {cant_pedida}, se recibieron {cant_recibida}. Diferencia: {diferencia} uds."
                    
                    inc_res = supabase.table("incidencias").insert({
                        "id_orden_compra": id_orden,
                        "id_proveedor": id_proveedor,
                        "descripcion": desc,
                        "tipo": motivo,
                        "estado_incidencia": 1
                    }).execute()
                    operaciones_realizadas["incidencias"].append(inc_res.data[0]["id"])

            # 3. Determinar el estado final de la orden
            nuevo_estado_orden = 4 if todo_cero else (3 if hubo_incidencia else 2)

            supabase.table("ordenes_compras").update({
                "estado_orden": nuevo_estado_orden,
                "fecha_entrega": str(date.today())
            }).eq("id", id_orden).execute()

            return {
                "mensaje": "Recepción procesada.", 
                "estado_final": nuevo_estado_orden,
                "incidencias_generadas": hubo_incidencia
            }

        except Exception as e:
            # Lógica de reversión (Rollback manual)
            for mov_id in operaciones_realizadas["movimientos"]:
                supabase.table("movimientos_inventarios").delete().eq("id", mov_id).execute()
            for lote_id in operaciones_realizadas["lotes"]:
                supabase.table("lotes").delete().eq("id", lote_id).execute()
            for inc_id in operaciones_realizadas["incidencias"]:
                supabase.table("incidencias").delete().eq("id", inc_id).execute()
            
            raise HTTPException(status_code=500, detail=f"Fallo crítico: {str(e)}")
        
    @staticmethod
    def listar_ordenes():
        try:
            # AÑADIMOS .eq("estado_orden", 1) AQUÍ para que solo traiga las pendientes
            response = supabase.table("ordenes_compras") \
                .select("id, id_proveedor, fecha_emision, estado_orden, proveedores(nombre)") \
                .eq("estado_orden", 1) \
                .execute()
            
            datos = [
                {
                    "id": o["id"],
                    "proveedor_nombre": o["proveedores"]["nombre"] if o["proveedores"] else "N/A",
                    "proveedor_id": o["id_proveedor"],
                    "estado": o["estado_orden"]
                } for o in response.data
            ]
            return datos
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error al obtener órdenes")

    @staticmethod
    def listar_detalle(id_orden: int):
        try:
            # Traemos los detalles unidos con la información del medicamento
            # Nota: Asegúrate de que el nombre de la relación 'medicamentos' 
            # en el select coincida con cómo está en tu configuración de Supabase
            response = supabase.table("detalles_ordenes_compras") \
                .select("*, medicamentos(nombre)") \
                .eq("id_orden_compra", id_orden) \
                .execute()
            
            # Formateamos la respuesta para el frontend
            datos = [
                {
                    "id_medicamento": d["id_medicamento"],
                    "medicamento_nombre": d["medicamentos"]["nombre"] if d["medicamentos"] else "Desconocido",
                    "cantidad": d["cantidad"],
                    "precio_unitario": d["precio_unitario"]
                } for d in response.data
            ]
            return datos
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener detalle de orden: {str(e)}") 
        
         

# --- ENDPOINTS ---

@router.get("/", dependencies=[Depends(acceso_recepcion)])
def obtener_ordenes(estado: int = 1): # Por defecto trae las pendientes
    return OrdenCompraController.listar_ordenes()

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_orden(payload: OrdenCompraCreate, user: dict = Depends(get_current_user)):
    return OrdenCompraController.generar_orden(payload, user)

# CORRECCIÓN: Cambiamos 'RecepcionOrdenCreate' por 'dict' para aceptar el payload flexible con incidencias
@router.put("/{id_orden}/recepcionar", dependencies=[Depends(acceso_recepcion)])
def recepcionar_orden_compra(id_orden: int, payload: dict, user: dict = Depends(get_current_user)):
    return OrdenCompraController.recepcionar_orden(id_orden, payload, user)

@router.get("/{id_orden}/detalle", dependencies=[Depends(acceso_recepcion)])
def obtener_detalle_orden(id_orden: int):
    return OrdenCompraController.listar_detalle(id_orden)