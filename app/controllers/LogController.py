from fastapi import APIRouter, Depends
from config.base_datos import supabase
from core.security import RoleChecker

router = APIRouter(
    prefix="/logs",
    tags=["Logs"]
)


@router.get("/")
def obtener_logs(
    current_user: dict = Depends(RoleChecker([1]))
):

    logs = []


    # ==========================
    # MOVIMIENTOS INVENTARIO
    # ==========================

    movimientos = (
        supabase
        .table("movimientos_inventarios")
        .select(
            """
            id,
            id_usuario,
            cantidad,
            tipo_movimiento,
            creado_el
            """
        )
        .execute()
    )


    for movimiento in movimientos.data:

        usuario = (
            supabase
            .table("usuarios")
            .select(
                """
                nombre,
                rol
                """
            )
            .eq("id", movimiento["id_usuario"])
            .single()
            .execute()
        )


        datos_usuario = usuario.data if usuario.data else {}


        es_ingreso = movimiento["tipo_movimiento"] == 1


        logs.append({

            "id": movimiento["id"],

            "usuario_id": movimiento["id_usuario"],

            "nombre": datos_usuario.get(
                "nombre",
                "Desconocido"
            ),

            "rol": datos_usuario.get(
                "rol",
                "Desconocido"
            ),

            "accion": (
                "INGRESO_PRODUCTO"
                if es_ingreso
                else "SALIDA_PRODUCTO"
            ),

            "modulo": "Inventario",

            "descripcion": (
                f"Ingreso de {movimiento['cantidad']} unidades"
                if es_ingreso
                else f"Salida de {movimiento['cantidad']} unidades"
            ),

            "estado": "ÉXITO",

            "fecha": movimiento["creado_el"]

        })



    # ==========================
    # ORDENES DE COMPRA
    # ==========================

    ordenes = (
        supabase
        .table("ordenes_compras")
        .select(
            """
            id,
            id_usuario,
            estado_orden,
            fecha_emision
            """
        )
        .execute()
    )


    for orden in ordenes.data:

        usuario = (
            supabase
            .table("usuarios")
            .select(
                """
                nombre,
                rol
                """
            )
            .eq("id", orden["id_usuario"])
            .single()
            .execute()
        )


        datos_usuario = usuario.data if usuario.data else {}


        logs.append({

            "id": f"orden-{orden['id']}",

            "usuario_id": orden["id_usuario"],

            "nombre": datos_usuario.get(
                "nombre",
                "Desconocido"
            ),

            "rol": datos_usuario.get(
                "rol",
                "Desconocido"
            ),

            "accion": "CREAR_PEDIDO",

            "modulo": "Compras",

            "descripcion": (
                f"Creó orden de compra N° {orden['id']}"
            ),

            "estado": "ÉXITO",

            "fecha": orden["fecha_emision"]

        })



    # ==========================
    # INCIDENCIAS (PROVEEDOR)
    # ==========================

    incidencias = (
        supabase
        .table("incidencias")
        .select(
            """
            id,
            id_proveedor,
            descripcion,
            creado_el
            """
        )
        .execute()
    )


    for incidencia in incidencias.data:


        proveedor = (
            supabase
            .table("proveedores")
            .select(
                """
                id,
                nombre
                """
            )
            .eq("id", incidencia["id_proveedor"])
            .single()
            .execute()
        )


        datos_proveedor = (
            proveedor.data
            if proveedor.data
            else {}
        )


        logs.append({

            "id": f"incidencia-{incidencia['id']}",

            "usuario_id": incidencia["id_proveedor"],

            "nombre": datos_proveedor.get(
                "nombre",
                "Proveedor desconocido"
            ),

            "rol": "Proveedor",

            "accion": "REPORTAR_INCIDENCIA",

            "modulo": "Incidencias",

            "descripcion": incidencia["descripcion"],

            "estado": "ÉXITO",

            "fecha": incidencia["creado_el"]

        })



    # ==========================
    # ORDENAR POR FECHA
    # ==========================

    logs.sort(
        key=lambda x: x["fecha"],
        reverse=True
    )


    return logs