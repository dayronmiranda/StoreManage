from fastapi import APIRouter

from app.api.v1 import auth, users, products, warehouses, inventory, sales, transfers, incidents, finances

# Create main router for v1
router = APIRouter()

# Include all routers
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(products.router)
router.include_router(warehouses.router)
router.include_router(inventory.router)
router.include_router(sales.router)
router.include_router(transfers.router)
router.include_router(incidents.router)
router.include_router(finances.router)