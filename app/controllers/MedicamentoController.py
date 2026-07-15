from fastapi import APIRouter, Depends
from app.core.security import RoleChecker
from app.core.base_controller import BaseController
from app.models.MedicamentoModel import MedicamentoCreate

router = APIRouter(prefix="/api/v1/medicamentos", tags=["Medicamentos"])
solo_admin = RoleChecker(allowed_roles=[1])

class MedicamentoController(BaseController):
    
    def _listar_todos_logica(self):

        fecha_limite = str(date.today() + timedelta(days=15))

        medicamentos = (
            self._db.table("medicamentos")
            .select("*")
            .execute()
        )

        resultado = []

        for medicamento in medicamentos.data:

            lotes = (
                self._db.table("lotes")
                .select("cantidad_disponible")
                .eq("id_medicamento", medicamento["id"])
                .gt("cantidad_disponible", 0)
                .gt("fecha_caducidad", fecha_limite)
                .execute()
            )

            stock_valido = sum(
                lote["cantidad_disponible"]
                for lote in lotes.data
            )

            if stock_valido > 0:

                medicamento["stock_actual"] = stock_valido

                resultado.append(medicamento)

        return resultado

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