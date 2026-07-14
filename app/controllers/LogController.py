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

    respuesta = (
        supabase
        .table("movimientos_inventarios")
        .select(
            """
            id,
            id_usuario,
            cantidad,
            tipo_movimiento,
            motivo_salida,
            creado_el
            """
        )
        .order("creado_el", desc=True)
        .execute()
    )

    logs = []

    for movimiento in respuesta.data:

        logs.append({
            "usuario": movimiento["id_usuario"],
            "tipo_movimiento": (
                "INGRESO"
                if movimiento["tipo_movimiento"] == 1
                else "SALIDA"
            ),
            "cantidad": movimiento["cantidad"],
            "motivo": movimiento["motivo_salida"],
            "fecha": movimiento["creado_el"]
        })

    return logs