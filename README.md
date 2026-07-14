# Documentación del Backend - Sistema Farmacia Los Girasoles 🌻

Esta API RESTful está desarrollada en Python utilizando el framework **FastAPI** y el patrón arquitectónico **MVC (Modelo-Vista-Controlador)** adaptado para backend (Modelos, Controladores y Rutas). La base de datos es **PostgreSQL** gestionada a través de **Supabase**.

## 🏗️ 1. Estructura del Proyecto (Patrón MVC)

El proyecto sigue el principio de **Responsabilidad Única (SOLID)**, separando la validación de datos, la lógica de negocio y la configuración central.

```text
LOSGIRASOLES-BACKEND/
├── app/
│   ├── controllers/      # Lógica de negocio y definición de endpoints (Rutas)
│   │   ├── AdminController.py       # Gestión de usuarios y proveedores
│   │   ├── AuthController.py        # Login y generación de tokens
│   │   ├── IncidenciaController.py  # Reporte de problemas con mercadería
│   │   ├── IngresoController.py     # (Opcional/Integrado en Recepción)
│   │   ├── MedicamentoController.py # Catálogo general de productos
│   │   └── OrdenCompraController.py # Generación y recepción de órdenes
│   └── models/           # Esquemas Pydantic para validación de datos (Input/Output)
│       ├── AuthModel.py
│       ├── GestionModel.py
│       ├── IncidenciaModel.py
│       ├── IngresoModel.py
│       ├── MedicamentoModel.py
│       └── OrdenCompraModel.py
├── config/               # Conexiones externas
│   ├── base_datos.py     # Cliente de inicialización de Supabase
│   └── config.py         # Carga de variables de entorno
├── core/                 # Utilidades núcleo del sistema
│   └── security.py       # RoleChecker, verificación de JWT y contraseñas
├── .env                  # Credenciales y secretos (No subir a Git)
├── main.py               # Punto de entrada y registro de routers
└── requirements.txt      # Dependencias del proyecto
```
## Usuarios con password
Todo los usuarios tiene esa contraseña:

contraseña :123456

## ⚙️ 2. Dependencias del Sistema

El proyecto requiere la instalación de las siguientes librerías base incluidas en el archivo `requirements.txt`:

* **`fastapi`** ⚡ Framework web moderno y rápido para construir la API.
* **`uvicorn`** 🚀 Servidor ASGI de alto rendimiento para desarrollo y producción.
* **`pydantic`** 🛡️ Validación estricta de datos utilizando tipado nativo de Python.
* **`supabase`** 🗄️ Cliente oficial de Python para la integración con PostgreSQL.
* **`python-dotenv`** 🔑 Gestión segura de variables de entorno mediante archivos `.env`.
* **`bcrypt`** 🔒 Algoritmo de hash seguro para la protección de contraseñas.
* **`pyjwt`** 🎫 Generación y validación de tokens estructurados para la autenticación.

---

## 📜 3. Reglas de Negocio y Desarrollo

Cualquier contribución al código debe respetar estrictamente los siguientes lineamientos arquitectónicos y de negocio para superar la evaluación:

### 👤 Control de Acceso Basado en Roles (RBAC)
El sistema gestiona tres niveles de acceso específicos:
* **Rol 1 (Administrador):** Acceso total. Gestión de catálogos, usuarios, proveedores y compras.
* **Rol 2 (Almacenero):** Operador logístico. Recepción de órdenes (creación de lotes) y reporte de incidencias.
* **Rol 3 (Farmacéutico):** Operador de mostrador. Registro de salidas (ventas) y consulta de stock actual.

> 🛠️ **Regla Técnica de Inyección:** Todo endpoint que requiera protección de identidad DEBE implementar la dependencia de validación de la siguiente manera:
> ```python
> Depends(RoleChecker(allowed_roles=[1, 2]))
> ```

### 🧱 Arquitectura de Datos e Inventario
1. **Separación de Conceptos:** 
   * **Medicamento:** Registro maestro y estático del catálogo. No se elimina del sistema, solo cambia su estado lógico.
   * **Lote:** Existencia física real y cuantificable en el almacén asociada a una fecha de caducidad.
2. **Atomicidad Transaccional:** Cualquier movimiento de inventario (ingreso o salida) debe impactar de forma obligatoria y simultánea en **3 tablas**:
   * Crear/Editar el registro en `lotes`.
   * Registrar la traza en `movimientos_inventarios`.
   * Actualizar el campo `stock_actual` en la tabla `medicamentos`.
3. **Lógica de Despacho FIFO (First-In, First-Out):** 
   * La lógica de salida para ventas debe priorizar de forma automatizada el descuento de stock de aquellos lotes cuya `fecha_caducidad` sea la más próxima a vencer.

---

## 🎯 4. Matriz de Historias de Usuario (HU) y Endpoints

Mapa de ruta global y estado de cobertura de la API del sistema.


| ID | Módulo | Historia de Usuario (HU) | Método | Endpoint REST | Roles | Estado |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: |
| **HU01** | 🔒 Administración | **Autenticación:** Inicio de sesión seguro. | `POST` | `/api/v1/auth/login` | 1, 2, 3 | 🟩 `Completado` |
| **HU02** | 🔒 Administración | **Gestión de Personal:** Alta de usuarios. | `POST` | `/api/v1/admin/usuarios` | 1 | 🟩 `Completado` |
| **HU03** | 🔒 Administración | **Gestión de Proveedores:** Registro de empresas. | `POST` | `/api/v1/admin/proveedores` | 1 | 🟩 `Completado` |
| **HU04** | 📦 Catálogo | **Alta de Medicamentos:** Nuevos productos en catálogo. | `POST` | `/api/v1/medicamentos/` | 1 | 🟩 `Completado` |
| **HU05** | 📦 Catálogo | **Órdenes de Compra:** Generación de pedidos. | `POST` | `/api/v1/ordenes-compras/` | 1 | 🟩 `Completado` |
| **HU06** | 🚛 Logística | **Recepción de Mercadería:** Lotes y stock. | `PUT` | `/api/v1/ordenes-compras/{id}/recepcionar` | 1, 2 | 🟩 `Completado` |
| **HU07** | 🚛 Logística | **Incidencias:** Reportar productos dañados/faltantes. | `POST` | `/api/v1/incidencias/` | 1, 2 | 🟩 `Completado` |
| **HU08** | ⏳ Operaciones | **Registro de Salidas:** Ventas bajo criterio FIFO. | `POST` | `/api/v1/operaciones/salida` | 1, 3 | 🟨 `Pendiente` |
| **HU09** | ⏳ Operaciones | **Consulta de Kardex:** Historial y saldo residual. | `GET` | `/api/v1/operaciones/kardex/{id}` | 1, 2, 3 | 🟨 `Pendiente` |
| **HU10** | ⏳ Operaciones | **Alertas de Stock:** Cruce de punto de reorden. | `GET` | `/api/v1/operaciones/alertas` | 1, 3 | 🟨 `Pendiente` |

