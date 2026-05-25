# logistica-backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from app.controllers.AuthController import router as auth_router # Corregido el import
from app.controllers.AdminController import router as admin_router
from app.controllers.MedicamentoController import router as medic_router
from app.controllers.OrdenCompraController import router as order_router

app = FastAPI(title="API Logística Los Girasoles", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(medic_router)
app.include_router(order_router)