from fastapi import APIRouter, Depends
from core.security import RoleChecker
from config.base_datos import supabase
from app.models.MedicamentoModel import MedicamentoCreate

router = APIRouter(prefix="/api/v1/medicamentos", tags=["Medicamentos"])
solo_admin = RoleChecker(allowed_roles=[1])

class MedicamentoController:
    @staticmethod
    def registrar(datos: MedicamentoCreate):
        res = supabase.table("medicamentos").insert(datos.dict()).execute()
        return {"mensaje": "Medicamento registrado en catálogo"}

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_medicamento(payload: MedicamentoCreate):
    return MedicamentoController.registrar(payload)