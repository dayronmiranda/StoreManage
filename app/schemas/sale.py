from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Schemas para Cliente
class CustomerBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: Optional[str] = None
    document_type: Optional[str] = Field(None, pattern="^(id_card|nit|passport)$")
    document_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True
    birth_date: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|Other)$")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = None
    document_type: Optional[str] = Field(None, pattern="^(id_card|nit|passport)$")
    document_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    birth_date: Optional[datetime] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|Other)$")


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    registration_date: datetime


class CustomerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    code: str
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool


# Schemas para MetodoPago
class PaymentMethodBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=2, max_length=50)
    type: str = Field(..., pattern="^(cash|card|transfer)$")
    is_active: bool = True
    requires_reference: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodResponse(PaymentMethodBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str


# Schemas para DetalleVenta
class SaleDetailBase(BaseModel):
    product_id: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)


class SaleDetailCreate(SaleDetailBase):
    pass


class SaleDetailResponse(SaleDetailBase):
    model_config = ConfigDict(from_attributes=True)
    
    product_code: str
    product_name: str
    subtotal: Decimal
    total: Decimal


# Schemas para Venta
class SaleBase(BaseModel):
    warehouse_id: str
    customer_id: Optional[str] = None
    payment_method_id: str
    details: List[SaleDetailCreate] = Field(..., min_length=1)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    observations: Optional[str] = None
    payment_reference: Optional[str] = None
    amount_received: Optional[Decimal] = Field(None, gt=0)


class SaleCreate(SaleBase):
    pass


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    sale_number: str
    warehouse_id: str
    customer_id: Optional[str] = None
    user_id: str
    payment_method_id: str
    details: List[SaleDetailResponse]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    status: str
    sale_date: datetime
    observations: Optional[str] = None
    payment_reference: Optional[str] = None
    change: Optional[Decimal] = None
    amount_received: Optional[Decimal] = None
    
    # Related information (optional)
    customer_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    payment_method_name: Optional[str] = None
    user_name: Optional[str] = None


class SaleListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    sale_number: str
    sale_date: datetime
    customer_name: Optional[str] = None
    total: Decimal
    status: str
    payment_method_name: Optional[str] = None


# Schemas para Factura
class InvoiceBase(BaseModel):
    sale_id: str
    customer_tax_data: dict
    tax_regime: Optional[str] = None
    cfdi_use: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    invoice_number: str
    issue_date: datetime
    status: str
    xml_sat: Optional[str] = None
    pdf_path: Optional[str] = None