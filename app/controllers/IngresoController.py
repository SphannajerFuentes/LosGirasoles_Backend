from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user, RoleChecker

router = APIRouter(prefix="/api/v1/ingresos", tags=["Ingresos"])

# Solo Administradores y Farmacéuticos pueden registrar ingresos
admin_or_farmaceutico = RoleChecker(allowed_roles=[1, 3])

class IngresoController:
    
    @staticmethod
    def registrarIngreso(datos: dict, user: dict = Depends(admin_or_farmaceutico)):
        """
        El endpoint está protegido. Si el usuario no tiene rol 
        admin o farmaceutico, el sistema lanza automáticamente un 403.
        """
        try:
            # Aquí va tu lógica de negocio (Modelo)
            return {"mensaje": f"Ingreso registrado por usuario {user['user_id']}"}
        except Exception as e:
            # Manejo de excepciones según el punto 3 de tu guía
            raise HTTPException(status_code=500, detail="Error interno procesando ingreso")

@router.post("/")
def endpoint_registrar_ingreso(datos: dict, user: dict = Depends(admin_or_farmaceutico)):
    return IngresoController.registrarIngreso(datos, user)