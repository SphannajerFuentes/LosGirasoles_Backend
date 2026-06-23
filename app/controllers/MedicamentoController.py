from fastapi import APIRouter, Depends
from app.core.security import RoleChecker
from app.core.base_controller import BaseController
from app.models.MedicamentoModel import MedicamentoCreate

router = APIRouter(prefix="/api/v1/medicamentos", tags=["Medicamentos"])
solo_admin = RoleChecker(allowed_roles=[1])

class MedicamentoController(BaseController):
    
    def _listar_todos_logica(self):
        res = self._db.table("medicamentos").select("*").execute()
        return res.data

    def _registrar_logica(self, datos: MedicamentoCreate):
        self._db.table("medicamentos").insert(datos.dict()).execute()
        return {"mensaje": "Medicamento registrado en catálogo"}

    def listar_todos(self):
        return self._safe_execute(self._listar_todos_logica)
        
    def registrar(self, datos: MedicamentoCreate):
        return self._safe_execute(self._registrar_logica, datos)

medicamento_ctrl = MedicamentoController()

@router.get("/")
def listar_medicamentos():
    return medicamento_ctrl.listar_todos()

@router.post("/", dependencies=[Depends(solo_admin)])
def crear_medicamento(payload: MedicamentoCreate):
    return medicamento_ctrl.registrar(payload)