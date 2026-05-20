# logistica-backend/app/main.py
from fastapi import FastAPI, HTTPException
from app.db.supabase import supabase  # Importamos el cliente que creamos en el paso anterior

app = FastAPI(
    title="Sistema de Logística e Inventario Farmacéutico",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"status": "API de Logística operando correctamente"}

# Endpoint de prueba para verificar que conectó a Supabase
@app.get("/test-conexion")
def probar_supabase():
    try:
        # Intentamos leer la tabla 'medicamento' que creaste con el script SQL
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
