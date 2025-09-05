from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


# Generic schema for paginated responses
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pages: int
    size: int
    has_next: bool
    has_prev: bool


# Schema for pagination parameters
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# Schema for search parameters
class SearchParams(BaseModel):
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


# Schema for date filters
class DateRangeFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Schema for success response
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


# Schema for error response
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    details: Optional[Any] = None


# Schema for file upload
class FileUploadResponse(BaseModel):
    filename: str
    path: str
    size: int
    content_type: str
    uploaded_at: datetime


# Schema for general statistics
class GeneralStatistics(BaseModel):
    total_products: int
    total_warehouses: int
    total_customers: int
    sales_today: int
    sales_month: int
    inventory_value: float


# Schema for inventory reports
class InventoryReport(BaseModel):
    warehouse_id: str
    warehouse_name: str
    total_products: int
    total_value: float
    out_of_stock_products: int
    minimum_stock_products: int


# Schema for sales reports
class SalesReport(BaseModel):
    date: datetime
    total_sales: int
    total_value: float
    average_ticket: float
    best_selling_product: Optional[str] = None


# Schema for stock validation
class StockValidation(BaseModel):
    product_id: str
    warehouse_id: str
    requested_quantity: float
    available_quantity: float
    sufficient: bool


# Schema for notifications
class Notification(BaseModel):
    type: str  # info/warning/error/success
    title: str
    message: str
    date: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False