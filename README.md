# Estructura del Backend (Python + FastAPI)

```text
logistica-backend/
├── .env                    # Variables de entorno (Credenciales de Supabase)
├── .gitignore              # Excluye carpetas basura como venv/ y archivos .env
├── requirements.txt        # Archivo de dependencias del proyecto
└── app/
    ├── __init__.py
    ├── main.py             # Punto de entrada de la aplicación y configuración de CORS
    ├── core/               # CAPA DE CONFIGURACIÓN Y SEGURIDAD GLOBAL
    │   ├── config.py       # Validaciones de variables de entorno mediante Pydantic
    │   └── security.py     # REQ-015: Middleware/Inyección para validar JWT de Supabase
    ├── db/                 # CAPA DE CONEXIÓN A BASE DE DATOS
    │   └── supabase.py     # Inicialización del cliente global de Supabase
    ├── interfaces/          # CONTRATOS / ABSTRACCIONES (Principio D de SOLID)
    │   ├── ingresos_repository.py # Interfaz para insertar lotes y modificar stock
    │   └── salidas_repository.py  # Interfaz para consulta FIFO de lotes y rebajas
    ├── repositories/        # IMPLEMENTACIÓN DE ACCESO A DATOS (Principio O de SOLID)
    │   ├── supabase_ingresos.py # Código SQL/RPC o SDK de Supabase para REQ-011
    │   └── supabase_salidas.py  # Código para traer lotes ordenados por caducidad (REQ-013)
    ├── schemas/             # CAPA DE VALIDACIÓN DE ENTRADA/SALIDA (Molding de datos)
    │   ├── ingresos.py     # Validadores Pydantic para el REQ-011 (Lote, cantidad, estado)
    │   └── salidas.py      # Validadores Pydantic para el REQ-013 (Venta, medicamento, cantidad)
    ├── routers/            # CAPA DE ENTRADA (Controladores / Rutas HTTP)
    │   ├── v1/
    │   │   ├── ingresos.py # REQ-011: Endpoint POST /api/v1/ingresos
    │   │   └── salidas.py  # REQ-013: Endpoint POST /api/v1/salidas
    └── services/           # CAPA DE REGLAS DE NEGOCIO (El "cerebro" del sistema)
        ├── ingresos_service.py # Lógica de validación física "DAÑADO"/"APTO" (REQ-011)
        ├── caducidad_service.py # REQ-012: Lógica de semaforización (Verde, Amarillo, Rojo)
        ├── salidas_service.py  # REQ-013: Lógica transaccional de descuento por FIFO
        └── alertas_service.py  # REQ-014: Evaluar niveles de stock e insertar alertas
```
