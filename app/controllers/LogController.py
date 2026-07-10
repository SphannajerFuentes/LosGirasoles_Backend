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

    respuesta = supabase.table("movimientos_inventarios") \
        .select("*") \
        .order("creado_el", desc=True) \
        .execute()

    return respuesta.data