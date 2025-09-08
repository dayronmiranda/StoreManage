from typing import Optional, List, Any
from datetime import datetime
from dataclasses import dataclass


# Generic schema for paginated responses
@dataclass
class PaginatedResponse:
    items: List[Any]
    total: int
    page: int
    pages: int
    size: int
    has_next: bool
    has_prev: bool


# Schema for pagination parameters
@dataclass
class PaginationParams:
    page: int = 1
    size: int = 20


# Schema for search parameters
@dataclass
class SearchParams:
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"


# Schema for date filters
@dataclass
class DateRangeFilter:
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Schema for success response
@dataclass
class SuccessResponse:
    success: bool
    message: str
    data: Optional[Any] = None


# Schema for error response
@dataclass
class ErrorResponse:
    success: bool
    error: str
    message: str
    details: Optional[Any] = None


# Schema for file upload
@dataclass
class FileUploadResponse:
    filename: str
    path: str
    size: int
    content_type: str
    uploaded_at: datetime


# Schema for general statistics
@dataclass
class GeneralStatistics:
    total_products: int
    total_warehouses: int
    total_customers: int
    sales_today: int
    sales_month: int
    inventory_value: float


# Schema for inventory reports
@dataclass
class InventoryReport:
    warehouse_id: str
    warehouse_name: str
    total_products: int
    total_value: float
    out_of_stock_products: int
    minimum_stock_products: int


# Schema for sales reports
@dataclass
class SalesReport:
    date: datetime
    total_sales: int
    total_value: float
    average_ticket: float
    best_selling_product: Optional[str] = None


# Schema for stock validation
@dataclass
class StockValidation:
    product_id: str
    warehouse_id: str
    requested_quantity: float
    available_quantity: float
    sufficient: bool


# Schema for notifications
@dataclass
class Notification:
    type: str  # info/warning/error/success
    title: str
    message: str
    date: datetime
    read: bool = False