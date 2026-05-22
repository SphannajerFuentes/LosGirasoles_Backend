# logistica-backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from app.db.supabase import supabase

# 1. IMPORTA TU ROUTER DE AUTENTICACIÓN
from app.routers.v1.auth import router as auth_router

app = FastAPI(
    title="Sistema de Logística e Inventario Farmacéutico",
    version="1.0.0"
)

# 2. Definimos qué direcciones de Frontend tienen permiso de consultar la API
origins = [
    "http://localhost:5173",    # Dirección por defecto de Vite / React
    "http://127.0.0.1:5173",   # Variante local común
]

# 3. Activamos el puente de seguridad en la aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       
    allow_credentials=True,     
    allow_methods=["*"],         
    allow_headers=["*"],         
)

# 4. REGISTRA EL ROUTER DE AUTENTICACIÓN AQUÍ
# Esto unirá el prefijo "/auth" del router con la app, creando la ruta "/auth/login"
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"status": "API de Logística operando correctamente"}

@app.get("/test-conexion")
def probar_supabase():
    try:
        respuesta = supabase.table("medicamento").select("*").limit(5).execute()
        return {
            "conexion_exitosa": True,
            "datos_muestra": respuesta.data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al conectar con Supabase: {str(e)}"
        )