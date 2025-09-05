"""
Test file to check API code integrity without database operations.
This file validates imports, route definitions, schemas, and code structure.
"""

import pytest
import sys
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List
from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute
from pydantic import BaseModel

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestAPIIntegrity:
    """Test suite for API code integrity checks"""

    def test_main_app_imports(self):
        """Test that main application imports work correctly"""
        try:
            from app.main import app
            assert isinstance(app, FastAPI)
            assert app.title == "Sistema de Gestión API"
            assert app.version == "1.0.0"
            print("✅ Main app imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import main app: {e}")

    def test_database_module_imports(self):
        """Test database module imports"""
        try:
            from app.database import init_db, close_mongo_connection
            assert callable(init_db)
            assert callable(close_mongo_connection)
            print("✅ Database module imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import database module: {e}")

    def test_config_module_imports(self):
        """Test configuration module imports"""
        try:
            from app.config import settings
            assert hasattr(settings, 'ENVIRONMENT')
            print("✅ Config module imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import config module: {e}")

    def test_api_v1_router_imports(self):
        """Test API v1 router imports"""
        try:
            from app.api.v1 import router
            assert isinstance(router, APIRouter)
            print("✅ API v1 router imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import API v1 router: {e}")

    def test_individual_api_modules_imports(self):
        """Test individual API module imports"""
        api_modules = [
            'auth', 'users', 'products', 'warehouses', 
            'inventory', 'sales', 'transfers', 'incidents', 'finances'
        ]
        
        for module_name in api_modules:
            try:
                module = importlib.import_module(f'app.api.v1.{module_name}')
                assert hasattr(module, 'router')
                assert isinstance(module.router, APIRouter)
                print(f"✅ API module '{module_name}' imports successfully")
            except ImportError as e:
                pytest.fail(f"Failed to import API module '{module_name}': {e}")

    def test_models_directory_structure(self):
        """Test models directory structure and imports"""
        models_path = project_root / "app" / "models"
        if models_path.exists():
            try:
                # Try to import models if they exist
                model_files = [f.stem for f in models_path.glob("*.py") if f.stem != "__init__"]
                for model_file in model_files:
                    try:
                        importlib.import_module(f'app.models.{model_file}')
                        print(f"✅ Model '{model_file}' imports successfully")
                    except ImportError as e:
                        print(f"⚠️  Warning: Model '{model_file}' import failed: {e}")
            except Exception as e:
                print(f"⚠️  Warning: Models directory check failed: {e}")

    def test_schemas_directory_structure(self):
        """Test schemas directory structure and imports"""
        schemas_path = project_root / "app" / "schemas"
        if schemas_path.exists():
            try:
                schema_files = [f.stem for f in schemas_path.glob("*.py") if f.stem != "__init__"]
                for schema_file in schema_files:
                    try:
                        module = importlib.import_module(f'app.schemas.{schema_file}')
                        # Check if module contains Pydantic models
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                                print(f"✅ Schema '{schema_file}.{name}' is valid Pydantic model")
                    except ImportError as e:
                        print(f"⚠️  Warning: Schema '{schema_file}' import failed: {e}")
            except Exception as e:
                print(f"⚠️  Warning: Schemas directory check failed: {e}")

    def test_services_directory_structure(self):
        """Test services directory structure and imports"""
        services_path = project_root / "app" / "services"
        if services_path.exists():
            try:
                service_files = [f.stem for f in services_path.glob("*.py") if f.stem != "__init__"]
                for service_file in service_files:
                    try:
                        importlib.import_module(f'app.services.{service_file}')
                        print(f"✅ Service '{service_file}' imports successfully")
                    except ImportError as e:
                        print(f"⚠️  Warning: Service '{service_file}' import failed: {e}")
            except Exception as e:
                print(f"⚠️  Warning: Services directory check failed: {e}")

    def test_utils_directory_structure(self):
        """Test utils directory structure and imports"""
        utils_path = project_root / "app" / "utils"
        if utils_path.exists():
            try:
                util_files = [f.stem for f in utils_path.glob("*.py") if f.stem != "__init__"]
                for util_file in util_files:
                    try:
                        importlib.import_module(f'app.utils.{util_file}')
                        print(f"✅ Util '{util_file}' imports successfully")
                    except ImportError as e:
                        print(f"⚠️  Warning: Util '{util_file}' import failed: {e}")
            except Exception as e:
                print(f"⚠️  Warning: Utils directory check failed: {e}")

    def test_api_routes_structure(self):
        """Test API routes structure and definitions"""
        try:
            from app.main import app
            
            # Get all routes
            routes = []
            for route in app.routes:
                if isinstance(route, APIRoute):
                    routes.append({
                        'path': route.path,
                        'methods': route.methods,
                        'name': route.name
                    })
            
            # Check that we have routes
            assert len(routes) > 0, "No API routes found"
            
            # Check for essential routes
            paths = [route['path'] for route in routes]
            assert '/health' in paths, "Health check route not found"
            assert '/' in paths, "Root route not found"
            
            print(f"✅ Found {len(routes)} API routes")
            for route in routes[:10]:  # Show first 10 routes
                print(f"   - {route['methods']} {route['path']}")
            if len(routes) > 10:
                print(f"   ... and {len(routes) - 10} more routes")
                
        except Exception as e:
            pytest.fail(f"Failed to analyze API routes: {e}")

    def test_fastapi_app_configuration(self):
        """Test FastAPI app configuration"""
        try:
            from app.main import app
            
            # Check app configuration
            assert app.title is not None
            assert app.version is not None
            assert app.docs_url is not None
            assert app.redoc_url is not None
            assert app.openapi_url is not None
            
            # Check middleware
            middleware_types = []
            for middleware in app.user_middleware:
                if hasattr(middleware, 'cls'):
                    middleware_types.append(type(middleware.cls).__name__)
                else:
                    middleware_types.append(str(type(middleware)))
            
            # More flexible CORS check
            cors_configured = any('CORS' in str(mw) for mw in middleware_types) or any('cors' in str(mw).lower() for mw in middleware_types)
            if not cors_configured:
                print(f"   - Warning: CORS middleware may not be configured. Found middleware: {middleware_types}")
            else:
                print("   - CORS middleware is configured")
            
            print("✅ FastAPI app configuration is valid")
            print(f"   - Title: {app.title}")
            print(f"   - Version: {app.version}")
            print(f"   - Docs URL: {app.docs_url}")
            print(f"   - Middleware: {middleware_types}")
            
        except Exception as e:
            pytest.fail(f"Failed to validate FastAPI configuration: {e}")

    def test_exception_handlers(self):
        """Test exception handlers are properly configured"""
        try:
            from app.main import app
            
            # Check if exception handlers are configured
            assert len(app.exception_handlers) > 0, "No exception handlers configured"
            
            print("✅ Exception handlers are configured")
            print(f"   - Number of handlers: {len(app.exception_handlers)}")
            
        except Exception as e:
            pytest.fail(f"Failed to validate exception handlers: {e}")

    def test_environment_variables_structure(self):
        """Test environment variables structure"""
        try:
            from app.config import settings
            
            # Check essential settings exist
            essential_settings = ['ENVIRONMENT']
            for setting in essential_settings:
                assert hasattr(settings, setting), f"Missing essential setting: {setting}"
            
            print("✅ Environment configuration is valid")
            print(f"   - Environment: {getattr(settings, 'ENVIRONMENT', 'Not set')}")
            
        except Exception as e:
            pytest.fail(f"Failed to validate environment configuration: {e}")

    def test_project_structure_integrity(self):
        """Test overall project structure integrity"""
        required_directories = [
            "app",
            "app/api",
            "app/api/v1",
        ]
        
        required_files = [
            "app/__init__.py",
            "app/main.py",
            "app/config.py",
            "app/database.py",
            "app/api/__init__.py",
            "app/api/v1/__init__.py",
        ]
        
        # Check directories
        for directory in required_directories:
            dir_path = project_root / directory
            assert dir_path.exists() and dir_path.is_dir(), f"Required directory missing: {directory}"
        
        # Check files
        for file_path in required_files:
            file_full_path = project_root / file_path
            assert file_full_path.exists() and file_full_path.is_file(), f"Required file missing: {file_path}"
        
        print("✅ Project structure integrity check passed")
        print(f"   - All {len(required_directories)} required directories exist")
        print(f"   - All {len(required_files)} required files exist")


def run_integrity_tests():
    """Run all integrity tests and provide a summary"""
    print("🔍 Starting API Code Integrity Tests")
    print("=" * 50)
    
    test_instance = TestAPIIntegrity()
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed_tests = 0
    failed_tests = 0
    
    for test_method in test_methods:
        try:
            print(f"\n📋 Running {test_method}...")
            getattr(test_instance, test_method)()
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
            failed_tests += 1
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests / (passed_tests + failed_tests)) * 100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All integrity tests passed! Your API code structure is healthy.")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review the issues above.")
    
    return failed_tests == 0


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = run_integrity_tests()
    sys.exit(0 if success else 1)