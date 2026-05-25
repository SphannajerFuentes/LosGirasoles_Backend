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
    def recepcionar_orden(id_orden: int, datos: RecepcionOrdenCreate, user: dict):
        try:
            # 1. Actualizar estado de la Orden de Compra a 2 (Recibido)
            supabase.table("ordenes_compras").update({
                "estado_orden": 2,
                "fecha_entrega": str(date.today())
            }).eq("id", id_orden).execute()

            # 2. Procesar cada medicamento que está llegando físicamente
            for detalle in datos.detalles:
                
                # A. Insertar el Lote en la BD (Semaforo 1: Verde por defecto)
                lote = supabase.table("lotes").insert({
                    "id_medicamento": detalle.id_medicamento,
                    "numero_lote": detalle.numero_lote,
                    "cantidad_disponible": detalle.cantidad_recibida,
                    "fecha_caducidad": str(detalle.fecha_caducidad),
                    "estado_fisico": 1, # 1: Apto
                    "semaforo": 1       # 1: Verde
                }).execute()

                # B. Registrar el movimiento en el Inventario (1: Entrada)
                supabase.table("movimientos_inventarios").insert({
                    "id_usuario": user["user_id"], # Quién recibe la mercadería (Almacenero o Admin)
                    "cantidad": detalle.cantidad_recibida,
                    "tipo_movimiento": 1 # 1: Entrada
                }).execute()

                # C. Actualizar el stock actual en la tabla de medicamentos
                medicamento_data = supabase.table("medicamentos").select("stock_actual").eq("id", detalle.id_medicamento).single().execute()
                
                if medicamento_data.data:
                    stock_previo = medicamento_data.data["stock_actual"] or 0
                    nuevo_stock = stock_previo + detalle.cantidad_recibida
                    
                    supabase.table("medicamentos").update({
                        "stock_actual": nuevo_stock
                    }).eq("id", detalle.id_medicamento).execute()

            return {"mensaje": f"Orden de compra N° {id_orden} recepcionada correctamente. Stock y lotes actualizados."}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error en la recepción de la orden: {str(e)}")
    @staticmethod
    def listar_ordenes():
        try:
            # Traemos las órdenes incluyendo el nombre del proveedor mediante un join
            # Asegúrate de que en Supabase tengas la relación configurada o el select correcto
            response = supabase.table("ordenes_compras") \
                .select("id, id_proveedor, fecha_emision, estado_orden, proveedores(nombre)") \
                .execute()
            
            # Formateamos un poco la respuesta para que sea fácil de consumir en el frontend
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

# --- ENDPOINTS ---

@router.get("/", dependencies=[Depends(acceso_recepcion)])
def obtener_ordenes():
    return OrdenCompraController.listar_ordenes()

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_orden(payload: OrdenCompraCreate, user: dict = Depends(get_current_user)):
    return OrdenCompraController.generar_orden(payload, user)

# NUEVO ENDPOINT: Cambia el estado de la orden y registra los lotes entrantes
@router.put("/{id_orden}/recepcionar", dependencies=[Depends(acceso_recepcion)])
def recepcionar_orden_compra(id_orden: int, payload: RecepcionOrdenCreate, user: dict = Depends(get_current_user)):
    return OrdenCompraController.recepcionar_orden(id_orden, payload, user)