from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global MongoDB client
client: AsyncIOMotorClient = None


async def connect_to_mongo():
    """Create MongoDB connection"""
    global client
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Verify connection
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {settings.MONGODB_URL}")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def init_db():
    """Initialize database and Beanie models"""
    try:
        # Import all models here to avoid circular imports
        from app.models.user import User, Token, Permission, Role
        from app.models.product import Product, Category, UnitOfMeasure
        from app.models.warehouses import Warehouse
        from app.models.inventories import Inventory, InventoryMovement
        from app.models.sales import Sale, Customer, PaymentMethod, Invoice
        from app.models.transfers import Transfer, GoodsInTransit
        from app.models.incidents import Incident, IncidentType
        from app.models.financials import OperationalExpense, ExpenseCategory, CashCut
        from app.models.audits import EventLog, AccessLog
        
        # Connect to MongoDB
        await connect_to_mongo()
        
        # Initialize Beanie with all models
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                # Authentication
                User,
                Token,
                Permission,
                Role,
                
                # Products
                Product,
                Category,
                UnitOfMeasure,
                
                # Warehouses
                Warehouse,
                
                # Inventory
                Inventory,
                InventoryMovement,
                
                # Sales
                Sale,
                Customer,
                PaymentMethod,
                Invoice,
                
                # Transfers
                Transfer,
                GoodsInTransit,
                
                # Incidents
                Incident,
                IncidentType,
                
                # Financial
                OperationalExpense,
                ExpenseCategory,
                CashCut,
                
                # Audit
                EventLog,
                AccessLog,
            ]
        )
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def get_database():
    """Get database instance"""
    return client[settings.DATABASE_NAME]