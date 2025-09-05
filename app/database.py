from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente MongoDB global
client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Crear conexión a MongoDB"""
    global client
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Verificar conexión
        await client.admin.command('ping')
        logger.info(f"Conectado a MongoDB: {settings.MONGODB_URL}")
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
        logger.info("Conexión a MongoDB cerrada")


async def init_db():
    """Inicializar base de datos y modelos Beanie"""
    try:
        # Import all models here to avoid circular imports
        from app.models.user import User, Token
        from app.models.product import Product, Category, UnitOfMeasure
        from app.models.warehouses import Warehouse
        from app.models.inventories import Inventory, InventoryMovement
        from app.models.sales import Sale, Customer, PaymentMethod, Invoice
        from app.models.transfers import Transfer, GoodsInTransit
        from app.models.incidents import Incidencia, TipoIncidencia
        from app.models.financial import GastoOperativo, CategoriaGasto, CorteCaja
        from app.models.audit import LogEvento, LogAcceso
        
        # Conectar a MongoDB
        await connect_to_mongo()
        
        # Inicializar Beanie con todos los modelos
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                # Autenticación
                Usuario,
                Token,
                
                # Productos
                Producto,
                Categoria,
                UnidadMedida,
                
                # Almacenes
                Almacen,
                
                # Inventario
                Inventario,
                MovimientoInventario,
                
                # Ventas
                Venta,
                Cliente,
                MetodoPago,
                Factura,
                
                # Transferencias
                Transferencia,
                TransitoMercancia,
                
                # Incidencias
                Incidencia,
                TipoIncidencia,
                
                # Financiero
                GastoOperativo,
                CategoriaGasto,
                CorteCaja,
                
                # Auditoría
                LogEvento,
                LogAcceso,
            ]
        )
        
        logger.info("Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise


def get_database():
    """Obtener instancia de la base de datos"""
    return client[settings.DATABASE_NAME]