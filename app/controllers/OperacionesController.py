from fastapi import APIRouter, Depends, HTTPException
from config.base_datos import supabase
from core.security import RoleChecker, get_current_user
from app.models.GestionModel import (
    SalidaMedicamentoRequest, SalidaResponse, MovimientoDetalleResponse,
    KardexKardexResponse, KardexRegistroResponse, AlertaStockResponse
)
from typing import List
from datetime import date

router = APIRouter(prefix="/api/v1/operations", tags=["Operaciones Inventario"])

# Mapeos estándar
TIPO_SALIDA = 2 
MOTIVO_VENTA = 1

class OperacionesController:
    
    @staticmethod
    def registrar_salida(payload: SalidaMedicamentoRequest, current_user: dict):
        detalles_despacho = []
        
        for item in payload.items:
            # 1. Obtener datos del medicamento
            med = supabase.table("medicamentos").select(
                "id, nombre, stock_actual, stock_maximo, punto_reorden"
            ).eq("id", item.medicamento_id).single().execute()
            
            if not med.data:
                raise HTTPException(status_code=404, detail="Medicamento no encontrado")
            
            medicamento = med.data
            
            if medicamento["stock_actual"] < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {medicamento['nombre']}")
            
            # 2. Consumir lotes mediante método FEFO
            lotes_query = supabase.table("lotes").select("id, cantidad_disponible, fecha_caducidad") \
                .eq("id_medicamento", item.medicamento_id).gt("cantidad_disponible", 0) \
                .order("fecha_caducidad", desc=False).execute()
            
            cantidad_por_restar = item.cantidad
            for lote in lotes_query.data:
                if cantidad_por_restar <= 0: break
                
                stock_lote = lote["cantidad_disponible"]
                retirado = min(stock_lote, cantidad_por_restar)
                
                supabase.table("lotes").update({"cantidad_disponible": stock_lote - retirado}).eq("id", lote["id"]).execute()
                
                # Registrar el movimiento de salida
                mov = supabase.table("movimientos_inventarios").insert({
                    "id_usuario": current_user["user_id"],
                    "cantidad": retirado, 
                    "tipo_movimiento": TIPO_SALIDA, 
                    "motivo_salida": MOTIVO_VENTA, 
                    "estado": 1
                }).execute()
                
                # Registrar en el Kardex
                supabase.table("kardex").insert({
                    "id_lote": lote["id"], 
                    "id_movimiento_inventario": mov.data[0]["id"], 
                    "saldo_actual": stock_lote - retirado, 
                    "estado": 1
                }).execute()
                
                detalles_despacho.append(MovimientoDetalleResponse(
                    lote_id=lote["id"], cantidad_retirada=retirado, fecha_caducidad=str(lote["fecha_caducidad"])
                ))
                cantidad_por_restar -= retirado
            
            # 3. Actualizar el stock global del medicamento
            nuevo_stock = medicamento["stock_actual"] - item.cantidad
            supabase.table("medicamentos").update({"stock_actual": nuevo_stock}).eq("id", item.medicamento_id).execute()
            
            # 4. Motor de Reposición Automática Inteligente (Cabecera + Detalle)
            limite = medicamento["punto_reorden"] if medicamento["punto_reorden"] is not None else 10
            stock_max = medicamento["stock_maximo"] if medicamento["stock_maximo"] is not None else 100
            
            if nuevo_stock <= limite:
                # Calculamos exactamente cuánto falta para llegar al tope máximo
                cantidad_a_pedir = stock_max - nuevo_stock
                
                if cantidad_a_pedir > 0:
                    proveedor_id = 1  # Proveedor asignado por defecto temporalmente
                    
                    # Buscamos si ya existe una orden de compra pendiente para este proveedor
                    orden_existente = supabase.table("ordenes_compras") \
                        .select("id") \
                        .eq("id_proveedor", proveedor_id) \
                        .eq("estado_orden", 1) \
                        .execute()
                    
                    if orden_existente.data:
                        id_orden = orden_existente.data[0]["id"]
                        
                        # Si la orden ya existe, verificamos si este medicamento ya está en los detalles
                        detalle_existente = supabase.table("detalles_ordenes_compras") \
                            .select("id") \
                            .eq("id_orden_compra", id_orden) \
                            .eq("id_medicamento", item.medicamento_id) \
                            .execute()
                        
                        # Si no está en los detalles, lo agregamos a la orden pendiente actual
                        if not detalle_existente.data:
                            supabase.table("detalles_ordenes_compras").insert({
                                "id_orden_compra": id_orden,
                                "id_medicamento": item.medicamento_id,
                                "cantidad": cantidad_a_pedir,
                                "precio_unitario": 0.00  # Se actualizará al recepcionar o cotizar
                            }).execute()
                    else:
                        # Si no hay ninguna orden pendiente para el proveedor, creamos la Cabecera
                        nueva_orden = supabase.table("ordenes_compras").insert({
                            "id_usuario": current_user["user_id"],
                            "id_proveedor": proveedor_id,
                            "estado_orden": 1,
                            "fecha_emision": str(date.today())
                        }).execute()
                        
                        id_orden_generada = nueva_orden.data[0]["id"]
                        
                        # Inserción obligatoria del Detalle del producto faltante
                        supabase.table("detalles_ordenes_compras").insert({
                            "id_orden_compra": id_orden_generada,
                            "id_medicamento": item.medicamento_id,
                            "cantidad": cantidad_a_pedir,
                            "precio_unitario": 0.00
                        }).execute()
        
        return SalidaResponse(message="Despacho exitoso y reposición automática estructurada.", detalles_despacho=detalles_despacho)

    @staticmethod
    def obtener_lotes_fefo():
        response = supabase.table("lotes").select("id, numero_lote, cantidad_disponible, fecha_caducidad, medicamentos(nombre)").gt("cantidad_disponible", 0).order("fecha_caducidad", desc=False).execute()
        datos = []
        hoy = date.today()
        for l in response.data:
            fecha_cad = date.fromisoformat(l["fecha_caducidad"])
            dias = (fecha_cad - hoy).days
            semaforo = "ROJO" if dias <= 90 else "AMARILLO" if dias <= 180 else "VERDE"
            datos.append({**l, "medicamento_nombre": l["medicamentos"]["nombre"], "dias_para_vencer": dias, "semaforo": semaforo})
        return datos

    @staticmethod
    def obtener_kardex_medicamento(medicamento_id: int):
        med = supabase.table("medicamentos").select("id, nombre, stock_actual").eq("id", medicamento_id).single().execute()
        if not med.data: raise HTTPException(status_code=404, detail="No encontrado")
        lotes = supabase.table("lotes").select("id, numero_lote").eq("id_medicamento", medicamento_id).execute()
        lotes_map = {l["id"]: l["numero_lote"] for l in lotes.data}
        if not lotes_map:
            return KardexKardexResponse(medicamento_id=med.data["id"], nombre=med.data["nombre"], stock_actual=med.data["stock_actual"], historial=[])
        kardex = supabase.table("kardex").select("id, creado_el, saldo_actual, id_lote, id_movimiento_inventario").in_("id_lote", list(lotes_map.keys())).order("creado_el", desc=True).execute()
        historial = []
        for k in kardex.data:
            mov = supabase.table("movimientos_inventarios").select("cantidad, tipo_movimiento").eq("id", k["id_movimiento_inventario"]).single().execute()
            historial.append(KardexRegistroResponse(id=k["id"], fecha_movimiento=k["creado_el"], tipo_movimiento="SALIDA" if mov.data["tipo_movimiento"]==2 else "INGRESO", cantidad=mov.data["cantidad"], lote_codigo=lotes_map.get(k["id_lote"]), motivo=f"Saldo: {k['saldo_actual']}"))
        return KardexKardexResponse(medicamento_id=med.data["id"], nombre=med.data["nombre"], stock_actual=med.data["stock_actual"], historial=historial)

    @staticmethod
    def verificar_alertas():
        alertas = []
        meds = supabase.table("medicamentos").select("id, nombre, stock_actual, punto_reorden").execute()
        for m in meds.data:
            limite = m["punto_reorden"] or 10
            if m["stock_actual"] <= limite:
                alertas.append({"id": f"stock-{m['id']}", "medicamento": m["nombre"], "tipo": "critico", "mensaje": f"Stock bajo: {m['stock_actual']} uds."})
        
        ordenes = supabase.table("ordenes_compras").select("id").eq("estado_orden", 1).execute()
        for o in ordenes.data:
            alertas.append({"id": f"auto-{o['id']}", "medicamento": "Pedido Pendiente", "tipo": "advertencia", "mensaje": f"Orden de compra N°{o['id']} pendiente."})
        return alertas
        
    @staticmethod
    def obtener_kpis():
        try:
            meds = supabase.table("medicamentos").select("stock_actual").execute()
            stock_total = sum(m["stock_actual"] for m in meds.data if m["stock_actual"])
            hoy_str = str(date.today())
            movs_hoy = supabase.table("movimientos_inventarios").select("cantidad, creado_el").eq("tipo_movimiento", 2).execute()
            ventas_hoy_cantidad = sum(m["cantidad"] for m in movs_hoy.data if m["creado_el"].startswith(hoy_str))
            from datetime import timedelta
            limite_fecha = str(date.today() + timedelta(days=90))
            lotes_vencen = supabase.table("lotes").select("id").gt("cantidad_disponible", 0).lte("fecha_caducidad", limite_fecha).execute()
            lotes_por_vencer = len(lotes_vencen.data) if lotes_vencen.data else 0
            ordenes = supabase.table("ordenes_compras").select("id").eq("estado_orden", 2).execute()
            ordenes_recibidas = len(ordenes.data) if ordenes.data else 0
            return {"stock_total": stock_total, "ventas_hoy": ventas_hoy_cantidad, "lotes_por_vencer": lotes_por_vencer, "ordenes_recibidas": ordenes_recibidas}
        except Exception as e:
            return {"stock_total": 0, "ventas_hoy": 0, "lotes_por_vencer": 0, "ordenes_recibidas": 0}

# --- ENDPOINTS ---
@router.post("/salida", dependencies=[Depends(RoleChecker(allowed_roles=[1, 3]))])
def post_salida(payload: SalidaMedicamentoRequest, user: dict = Depends(get_current_user)):
    return OperacionesController.registrar_salida(payload, user)

@router.get("/lotes/fefo", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_lotes(): return OperacionesController.obtener_lotes_fefo()

@router.get("/kardex/{medicamento_id}", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_kardex(medicamento_id: int): return OperacionesController.obtener_kardex_medicamento(medicamento_id)

@router.get("/alertas", dependencies=[Depends(RoleChecker(allowed_roles=[1, 3]))])
def get_alertas(): return OperacionesController.verificar_alertas()

@router.get("/dashboard/kpis", dependencies=[Depends(RoleChecker(allowed_roles=[1, 2, 3]))])
def get_kpis(): return OperacionesController.obtener_kpis()