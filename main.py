# logistica-backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from app.controllers.AuthController import router as auth_router # Corregido el import
from app.controllers.IngresoController import router as ingreso_router

app = FastAPI(title="API Logística Los Girasoles", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingreso_router)