import uuid
import random
from datetime import datetime
from typing import Optional


async def generate_sale_number() -> str:
    """Generate unique sale number"""
    from app.models.sales import Sale
    
    while True:
        # Generate number: VTA- + 8 digits
        number = random.randint(10000000, 99999999)
        sale_number = f"VTA-{number:08d}"
        
        # Verify it doesn't exist
        existing = await Sale.find_one({"sale_number": sale_number})
        if not existing:
            return sale_number


async def generate_transfer_number() -> str:
    """Generate unique transfer number"""
    from app.models.transfers import Transfer
    
    while True:
        # Generate number: TRF- + 8 digits
        number = random.randint(10000000, 99999999)
        transfer_number = f"TRF-{number:08d}"
        
        # Verify it doesn't exist
        existing = await Transfer.find_one({"transfer_number": transfer_number})
        if not existing:
            return transfer_number


async def generate_incident_number() -> str:
    """Generate unique incident number"""
    from app.models.incidents import Incident
    
    while True:
        # Generate number: INC- + 8 digits
        number = random.randint(10000000, 99999999)
        incident_number = f"INC-{number:08d}"
        
        # Verify it doesn't exist
        existing = await Incident.find_one({"incident_number": incident_number})
        if not existing:
            return incident_number


async def generate_invoice_number() -> str:
    """Generate unique invoice number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8].upper()
    return f"FAC-{timestamp}-{random_part}"


async def generate_customer_code() -> str:
    """Generate unique customer code"""
    from app.models.sales import Customer
    
    while True:
        # Generate code: CLI- + 6 digits
        number = random.randint(100000, 999999)
        code = f"CLI-{number:06d}"
        
        # Verify it doesn't exist
        existing = await Customer.find_one({"code": code})
        if not existing:
            return code


async def generate_product_code() -> str:
    """Generate unique product code"""
    from app.models.product import Product
    
    while True:
        # Generate code: PROD- + 8 digits
        number = random.randint(10000000, 99999999)
        code = f"PROD-{number:08d}"
        
        # Verify it doesn't exist
        existing = await Product.find_one({"code": code})
        if not existing:
            return code


async def generate_warehouse_code() -> str:
    """Generate unique warehouse code"""
    timestamp = datetime.now().strftime("%Y%m")
    random_part = str(uuid.uuid4())[:4].upper()
    return f"ALM-{timestamp}-{random_part}"


def generate_temporary_token() -> str:
    """Generate temporary token for operations"""
    return str(uuid.uuid4()).replace("-", "").upper()


def generate_payment_reference() -> str:
    """Generate payment reference"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:6].upper()
    return f"PAY-{timestamp}-{random_part}"


async def generate_movement_number() -> str:
    """Generate unique inventory movement number"""
    from app.models.inventories import InventoryMovement
    
    while True:
        # Generate number: MOV- + 8 digits
        number = random.randint(10000000, 99999999)
        movement_number = f"MOV-{number:08d}"
        
        # Verify it doesn't exist
        existing = await InventoryMovement.find_one({"movement_number": movement_number})
        if not existing:
            return movement_number