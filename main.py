from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from app.core.excepciones import configurar_manejadores_errores

# Importación de enrutadores
from app.controllers.AuthController import router as auth_router 
from app.controllers.AdminController import router as admin_router
from app.controllers.MedicamentoController import router as medic_router
from app.controllers.OrdenCompraController import router as order_router
from app.controllers.IncidenciaController import router as incidencia_router
from app.controllers.OperacionesController import router as router_lotes

app = FastAPI(title="API Logística Los Girasoles", version="2.0.0")

# Activamos el manejador global de errores que creamos usando Herencia
configurar_manejadores_errores(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://farmacialosgardines-pi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(medic_router)
app.include_router(order_router)
app.include_router(incidencia_router)
app.include_router(router_lotes)