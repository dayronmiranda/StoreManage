# StoreManage - Sistema de Gestión API

Un sistema de gestión simplificado para almacenes, diseñado como MVP (Minimum Viable Product).

## 📁 Estructura del Proyecto

```
📦 StoreManage/
├── 📄 requirements.txt          # Dependencias del proyecto
├── 📄 README.md                 # Documentación del proyecto
├── 📄 .env                      # Variables de entorno
├── 📄 .env.example              # Ejemplo de variables de entorno
├── 📄 .gitignore                # Archivos ignorados por Git
├── 📁 src/                      # Código fuente principal
│   ├── 📄 __init__.py
│   ├── 📄 main.py               # Punto de entrada de FastAPI
│   ├── 📁 config/               # Configuración del sistema
│   │   ├── 📄 __init__.py
│   │   ├── 📄 settings.py       # Configuración general
│   │   └── 📄 database.py       # Configuración de base de datos
│   ├── 📁 auth/                 # Módulo de autenticación
│   │   ├── 📄 __init__.py
│   │   ├── 📄 routes.py         # Endpoints de autenticación
│   │   ├── 📄 security.py       # Funciones de seguridad
│   │   ├── 📄 dependencies.py   # Dependencias de autenticación
│   │   └── 📄 permissions.py    # Sistema de permisos
│   ├── 📁 models/               # Modelos de datos
│   │   ├── 📄 __init__.py
│   │   ├── 📄 user.py           # Modelo de usuario
│   │   └── 📄 audit.py          # Modelo de auditoría
│   └── 📁 schemas/              # Esquemas de datos
│       ├── 📄 __init__.py
│       ├── 📄 user.py           # Esquemas de usuario
│       └── 📄 common.py         # Esquemas comunes
├── 📁 tests/                    # Pruebas del sistema
│   ├── 📄 __init__.py
│   └── 📄 test_mvp.py           # Pruebas básicas
├── 📁 scripts/                  # Scripts de utilidad
│   └── 📄 run.py                # Script para ejecutar la aplicación
└── 📁 uploads/                  # Archivos subidos
    └── 📄 .gitkeep
```

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Ejecutar la aplicación
```bash
# Opción 1: Usando el script
python scripts/run.py

# Opción 2: Directamente
python -m src.main
```

### 4. Acceder a la documentación
- **API Docs**: http://localhost:8000/api/docs
- **API Redoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Características

### ✅ Autenticación Simplificada
- Login básico con username/password
- Sin tokens JWT complejos
- Sistema de auditoría de accesos

### ✅ Arquitectura Limpia
- Separación clara de responsabilidades
- Estructura modular
- Código fácil de mantener

### ✅ Base de Datos
- MongoDB con Beanie ODM
- Modelos simplificados
- Configuración flexible

## 📊 API Endpoints

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/logout` - Cerrar sesión
- `GET /api/v1/auth/me` - Información del usuario

### Sistema
- `GET /health` - Estado del sistema
- `GET /` - Información general

## 🛠️ Desarrollo

### Estructura de Desarrollo Recomendada
```
# Mantener la estructura src/ para el código fuente
# Usar tests/ para todas las pruebas
# Usar scripts/ para utilidades de desarrollo
```

### Próximas Funcionalidades
- Gestión de productos
- Control de inventario
- Gestión de almacenes
- Reportes y estadísticas

## 📝 Notas

- **MVP Focus**: Sistema diseñado para ser simple y funcional
- **Sin Pydantic**: Usa dataclasses nativas de Python
- **Autenticación Básica**: Sin JWT tokens para simplicidad
- **Base de Datos**: MongoDB con configuración mínima

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Desarrollado como MVP para demostración de arquitectura limpia y código mantenible.**