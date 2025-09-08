from enum import Enum
from typing import List, Dict


class PermissionModule(str, Enum):
    """System modules"""
    USERS = "users"
    PRODUCTS = "products"
    WAREHOUSES = "warehouses"
    INVENTORY = "inventory"
    SALES = "sales"
    CUSTOMERS = "customers"
    TRANSFERS = "transfers"
    INCIDENTS = "incidents"
    FINANCES = "finances"
    REPORTS = "reports"
    AUDIT = "audit"
    CONFIGURATION = "configuration"


class PermissionAction(str, Enum):
    """Available actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"


class SystemRole(str, Enum):
    """Predefined system roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    SALESPERSON = "salesperson"
    WAREHOUSE_KEEPER = "warehouse_keeper"
    CASHIER = "cashier"
    AUDITOR = "auditor"


# Permission definition by role
PERMISSIONS_BY_ROLE: Dict[str, List[str]] = {
    SystemRole.SUPER_ADMIN: [
        "*"  # Total access
    ],
    
    SystemRole.ADMIN: [
        f"{PermissionModule.USERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.USERS}.{PermissionAction.READ}",
        f"{PermissionModule.USERS}.{PermissionAction.UPDATE}",
        f"{PermissionModule.USERS}.{PermissionAction.DELETE}",
        
        f"{PermissionModule.PRODUCTS}.{PermissionAction.CREATE}",
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        f"{PermissionModule.PRODUCTS}.{PermissionAction.UPDATE}",
        f"{PermissionModule.PRODUCTS}.{PermissionAction.DELETE}",
        
        f"{PermissionModule.WAREHOUSES}.{PermissionAction.CREATE}",
        f"{PermissionModule.WAREHOUSES}.{PermissionAction.READ}",
        f"{PermissionModule.WAREHOUSES}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.INVENTORY}.{PermissionAction.READ}",
        f"{PermissionModule.INVENTORY}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.SALES}.{PermissionAction.READ}",
        f"{PermissionModule.SALES}.{PermissionAction.EXPORT}",
        
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.READ}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.TRANSFERS}.{PermissionAction.READ}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.APPROVE}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.REJECT}",
        
        f"{PermissionModule.INCIDENTS}.{PermissionAction.READ}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.FINANCES}.{PermissionAction.READ}",
        f"{PermissionModule.FINANCES}.{PermissionAction.APPROVE}",
        
        f"{PermissionModule.REPORTS}.{PermissionAction.READ}",
        f"{PermissionModule.REPORTS}.{PermissionAction.EXPORT}",
        
        f"{PermissionModule.AUDIT}.{PermissionAction.READ}",
        
        f"{PermissionModule.CONFIGURATION}.{PermissionAction.READ}",
        f"{PermissionModule.CONFIGURATION}.{PermissionAction.UPDATE}",
    ],
    
    SystemRole.MANAGER: [
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        f"{PermissionModule.PRODUCTS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.WAREHOUSES}.{PermissionAction.READ}",
        
        f"{PermissionModule.INVENTORY}.{PermissionAction.READ}",
        f"{PermissionModule.INVENTORY}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.SALES}.{PermissionAction.READ}",
        f"{PermissionModule.SALES}.{PermissionAction.EXPORT}",
        
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.READ}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.TRANSFERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.READ}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.APPROVE}",
        
        f"{PermissionModule.INCIDENTS}.{PermissionAction.CREATE}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.READ}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.FINANCES}.{PermissionAction.CREATE}",
        f"{PermissionModule.FINANCES}.{PermissionAction.READ}",
        
        f"{PermissionModule.REPORTS}.{PermissionAction.READ}",
        f"{PermissionModule.REPORTS}.{PermissionAction.EXPORT}",
    ],
    
    SystemRole.SALESPERSON: [
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        
        f"{PermissionModule.INVENTORY}.{PermissionAction.READ}",
        
        f"{PermissionModule.SALES}.{PermissionAction.CREATE}",
        f"{PermissionModule.SALES}.{PermissionAction.READ}",
        
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.READ}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.INCIDENTS}.{PermissionAction.CREATE}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.READ}",
    ],
    
    SystemRole.WAREHOUSE_KEEPER: [
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        
        f"{PermissionModule.INVENTORY}.{PermissionAction.READ}",
        f"{PermissionModule.INVENTORY}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.TRANSFERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.READ}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.UPDATE}",
        
        f"{PermissionModule.INCIDENTS}.{PermissionAction.CREATE}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.READ}",
    ],
    
    SystemRole.CASHIER: [
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        
        f"{PermissionModule.SALES}.{PermissionAction.CREATE}",
        f"{PermissionModule.SALES}.{PermissionAction.READ}",
        
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.CREATE}",
        f"{PermissionModule.CUSTOMERS}.{PermissionAction.READ}",
        
        f"{PermissionModule.FINANCES}.{PermissionAction.CREATE}",
        f"{PermissionModule.FINANCES}.{PermissionAction.READ}",
    ],
    
    SystemRole.AUDITOR: [
        f"{PermissionModule.USERS}.{PermissionAction.READ}",
        f"{PermissionModule.PRODUCTS}.{PermissionAction.READ}",
        f"{PermissionModule.INVENTORY}.{PermissionAction.READ}",
        f"{PermissionModule.SALES}.{PermissionAction.READ}",
        f"{PermissionModule.SALES}.{PermissionAction.EXPORT}",
        f"{PermissionModule.TRANSFERS}.{PermissionAction.READ}",
        f"{PermissionModule.INCIDENTS}.{PermissionAction.READ}",
        f"{PermissionModule.FINANCES}.{PermissionAction.READ}",
        f"{PermissionModule.FINANCES}.{PermissionAction.EXPORT}",
        f"{PermissionModule.REPORTS}.{PermissionAction.READ}",
        f"{PermissionModule.REPORTS}.{PermissionAction.EXPORT}",
        f"{PermissionModule.AUDIT}.{PermissionAction.READ}",
        f"{PermissionModule.AUDIT}.{PermissionAction.EXPORT}",
    ],
}


def has_permission(user_roles: List[str], required_permission: str) -> bool:
    """Check if user has a specific permission"""
    
    # Check if any role has total access
    for role in user_roles:
        role_permissions = PERMISSIONS_BY_ROLE.get(role, [])
        if "*" in role_permissions:
            return True
    
    # Check specific permission
    for role in user_roles:
        role_permissions = PERMISSIONS_BY_ROLE.get(role, [])
        if required_permission in role_permissions:
            return True
    
    return False


def get_user_permissions(user_roles: List[str]) -> List[str]:
    """Get all user permissions based on their roles"""
    permissions = set()
    
    for role in user_roles:
        role_permissions = PERMISSIONS_BY_ROLE.get(role, [])
        permissions.update(role_permissions)
    
    return list(permissions)