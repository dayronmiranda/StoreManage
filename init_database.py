
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.user import User, Role, Permission, Token
from app.models.product import Product, Category, UnitOfMeasure, PriceHistory
from app.models.sales import Sale, Customer, PaymentMethod, SaleDetail, Invoice
from app.models.warehouses import Warehouse
from app.models.inventories import Inventory, InventoryMovement
from app.models.transfers import Transfer, TransferDetail, GoodsInTransit
from app.models.audits import EventLog, AccessLog, SystemLog
from app.models.incidents import IncidentType, IncidentDetail, IncidentEvidence, Incident
from app.models.financials import ExpenseCategory, OperationalExpense, CashCut, CashMovement
from app.core.security import get_password_hash


async def init_db():
    """Initialize the database, create collections and an admin user."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    database = client.storedb

    await init_beanie(
        database=database,
        document_models=[
            User, Role, Permission, Token,
            Product, Category, UnitOfMeasure,
            Sale, Customer, PaymentMethod, Invoice,
            Warehouse,
            Inventory, InventoryMovement,
            Transfer, GoodsInTransit,
            EventLog, AccessLog, SystemLog,
            IncidentType, Incident, 
            ExpenseCategory, OperationalExpense, CashCut, CashMovement
        ]
    )

    # Create a default admin user
    admin_user = await User.find_one(User.username == "admin")
    if not admin_user:
        hashed_password = get_password_hash("adminpassword")
        admin_user = User(
            username="admin",
            password=hashed_password,
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            is_active=True,
            roles=["admin"]
        )
        await admin_user.insert()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(init_db())
