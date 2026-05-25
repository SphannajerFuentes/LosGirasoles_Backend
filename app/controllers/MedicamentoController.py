from fastapi import APIRouter, Depends
from core.security import RoleChecker
from config.base_datos import supabase
from app.models.MedicamentoModel import MedicamentoCreate

router = APIRouter(prefix="/api/v1/medicamentos", tags=["Medicamentos"])
solo_admin = RoleChecker(allowed_roles=[1])

class MedicamentoController:
    # Este es el método que te faltaba
    @staticmethod
    def listar_todos():
        res = supabase.table("medicamentos").select("*").execute()
        return res.data

    @staticmethod
    def registrar(datos: MedicamentoCreate):
        res = supabase.table("medicamentos").insert(datos.dict()).execute()
        return {"mensaje": "Medicamento registrado en catálogo"}

# Ahora que el método existe dentro de la clase, puedes llamar al endpoint:
@router.get("/")
def listar_medicamentos():
    return MedicamentoController.listar_todos()

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_medicamento(payload: MedicamentoCreate):
    return MedicamentoController.registrar(payload)