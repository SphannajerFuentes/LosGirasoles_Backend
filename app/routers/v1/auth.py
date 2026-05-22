# logistica-backend/app/routers/v1/auth.py
from fastapi import APIRouter
from app.schemas.auth import LoginInput
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(payload: LoginInput):
    return AuthService.iniciar_sesion(payload)