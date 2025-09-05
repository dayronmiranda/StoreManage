from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from datetime import datetime, timedelta

from app.models.sale import Sale, Customer, PaymentMethod
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.sale import (
    SaleCreate,
    SaleResponse,
    SaleListResponse,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    PaymentMethodCreate,
    PaymentMethodResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.services.sale_service import SaleService
from app.utils.generators import generate_customer_code

router = APIRouter(prefix="/sales", tags=["Sales"])


# SALES ENDPOINTS
@router.get("", response_model=PaginatedResponse[SaleListResponse])
async def list_sales(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    payment_method_id: Optional[str] = Query(None, description="Filter by payment method"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_active_user)
):
    """List sales with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if warehouse_id:
        query_params["warehouse_id"] = warehouse_id
    
    if customer_id:
        query_params["customer_id"] = customer_id
    
    if payment_method_id:
        query_params["payment_method_id"] = payment_method_id
    
    if status:
        query_params["status"] = status
    
    # Date filter
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query_params["sale_date"] = date_query
    
    # Aggregation pipeline to get related information
    pipeline = [
        {"$match": query_params},
        {"$sort": {"sale_date": -1}},
        {
            "$lookup": {
                "from": "customers",
                "localField": "customer_id",
                "foreignField": "_id",
                "as": "customer"
            }
        },
        {
            "$lookup": {
                "from": "payment_methods",
                "localField": "payment_method_id",
                "foreignField": "_id",
                "as": "payment_method"
            }
        }
    ]
    
    # Get total
    total_pipeline = pipeline + [{"$count": "total"}]
    total_result = await Sale.aggregate(total_pipeline).to_list()
    total_sales = total_result[0]["total"] if total_result else 0
    
    # Pagination
    skip = (pagination.page - 1) * pagination.size
    pipeline.extend([
        {"$skip": skip},
        {"$limit": pagination.size}
    ])
    
    # Execute aggregation
    sales = await Sale.aggregate(pipeline).to_list()
    
    # Convert to response
    sale_responses = []
    for sale in sales:
        customer = sale.get("customer", [{}])[0] if sale.get("customer") else {}
        payment_method = sale.get("payment_method", [{}])[0] if sale.get("payment_method") else {}
        
        customer_name = None
        if customer:
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        
        sale_responses.append(SaleListResponse(
            id=str(sale["_id"]),
            sale_number=sale["sale_number"],
            sale_date=sale["sale_date"],
            customer_name=customer_name,
            total=sale["total"],
            status=sale["status"],
            payment_method_name=payment_method.get("name")
        ))
    
    total_pages = (total_sales + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=sale_responses,
        total=total_sales,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new sale"""
    
    try:
        # Create sale using the service
        sale = await SaleService.create_sale(sale_data, str(current_user.id))
        
        # Get related information for the response
        warehouse = await Warehouse.get(sale.warehouse_id)
        customer = await Customer.get(sale.customer_id) if sale.customer_id else None
        payment_method = await PaymentMethod.get(sale.payment_method_id)
        
        return SaleResponse(
            id=str(sale.id),
            sale_number=sale.sale_number,
            warehouse_id=sale.warehouse_id,
            customer_id=sale.customer_id,
            user_id=sale.user_id,
            payment_method_id=sale.payment_method_id,
            details=sale.details,
            subtotal=sale.subtotal,
            discount=sale.discount,
            tax=sale.tax,
            total=sale.total,
            status=sale.status,
            sale_date=sale.sale_date,
            observations=sale.observations,
            payment_reference=sale.payment_reference,
            change=sale.change,
            amount_received=sale.amount_received,
            customer_name=f"{customer.first_name} {customer.last_name}".strip() if customer else None,
            warehouse_name=warehouse.name if warehouse else None,
            payment_method_name=payment_method.name if payment_method else None,
            user_name=f"{current_user.first_name} {current_user.last_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sale: {str(e)}"
        )


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get sale by ID"""
    
    try:
        sale = await Sale.get(PydanticObjectId(sale_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Get related information
    warehouse = await Warehouse.get(sale.warehouse_id)
    customer = await Customer.get(sale.customer_id) if sale.customer_id else None
    payment_method = await PaymentMethod.get(sale.payment_method_id)
    user = await User.get(sale.user_id)
    
    return SaleResponse(
        id=str(sale.id),
        sale_number=sale.sale_number,
        warehouse_id=sale.warehouse_id,
        customer_id=sale.customer_id,
        user_id=sale.user_id,
        payment_method_id=sale.payment_method_id,
        details=sale.details,
        subtotal=sale.subtotal,
        discount=sale.discount,
        tax=sale.tax,
        total=sale.total,
        status=sale.status,
        sale_date=sale.sale_date,
        observations=sale.observations,
        payment_reference=sale.payment_reference,
        change=sale.change,
        amount_received=sale.amount_received,
        customer_name=f"{customer.first_name} {customer.last_name}".strip() if customer else None,
        warehouse_name=warehouse.name if warehouse else None,
        payment_method_name=payment_method.name if payment_method else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None
    )


@router.patch("/{sale_id}/cancel")
async def cancel_sale(
    sale_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel sale and restore stock"""
    
    try:
        sale = await SaleService.cancel_sale(sale_id, str(current_user.id))
        return {"message": "Sale canceled successfully", "sale_number": sale.sale_number}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error canceling sale: {str(e)}"
        )


@router.get("/reports/daily-sales")
async def daily_sales_report(
    warehouse_id: str = Query(..., description="Warehouse ID"),
    date: Optional[datetime] = Query(None, description="Date (defaults to today)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily sales report"""
    
    if not date:
        date = datetime.now()
    
    try:
        report = await SaleService.calculate_daily_total_sales(warehouse_id, date)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/reports/best-selling-products")
async def best_selling_products(
    warehouse_id: str = Query(..., description="Warehouse ID"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    limit: int = Query(10, description="Number of products to show"),
    current_user: User = Depends(get_current_active_user)
):
    """Get best-selling products in a period"""
    
    try:
        products = await SaleService.get_best_selling_products(
            warehouse_id, start_date, end_date, limit
        )
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


# CUSTOMER ENDPOINTS
@router.get("/customers/", response_model=PaginatedResponse[CustomerListResponse])
async def list_customers(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name, last name or document"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List customers with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if search:
        query_params["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"document_number": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    if active is not None:
        query_params["is_active"] = active
    
    # Get total
    total_customers = await Customer.find(query_params).count()
    
    # Get paginated customers
    skip = (pagination.page - 1) * pagination.size
    customer_list = await Customer.find(query_params).skip(skip).limit(pagination.size).to_list()
    
    # Convert to response
    customer_responses = [
        CustomerListResponse(
            id=str(customer.id),
            code=customer.code,
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone=customer.phone,
            is_active=customer.is_active
        )
        for customer in customer_list
    ]
    
    total_pages = (total_customers + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=customer_responses,
        total=total_customers,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("/customers/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new customer"""
    
    # Verify that code does not exist
    existing_customer = await Customer.find_one({"code": customer_data.code})
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer code already exists"
        )
    
    # Verify document if provided
    if customer_data.document_number:
        existing_doc = await Customer.find_one({"document_number": customer_data.document_number})
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document number already exists"
            )
    
    # Create customer
    customer = Customer(
        code=customer_data.code.upper(),
        first_name=customer_data.first_name,
        last_name=customer_data.last_name,
        document_type=customer_data.document_type,
        document_number=customer_data.document_number,
        email=customer_data.email,
        phone=customer_data.phone,
        address=customer_data.address,
        is_active=customer_data.is_active,
        birth_date=customer_data.birth_date,
        gender=customer_data.gender
    )
    
    await customer.insert()
    
    return CustomerResponse(
        id=str(customer.id),
        code=customer.code,
        first_name=customer.first_name,
        last_name=customer.last_name,
        document_type=customer.document_type,
        document_number=customer.document_number,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        is_active=customer.is_active,
        birth_date=customer.birth_date,
        gender=customer.gender,
        registration_date=customer.registration_date
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get customer by ID"""
    
    try:
        customer = await Customer.get(PydanticObjectId(customer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return CustomerResponse(
        id=str(customer.id),
        code=customer.code,
        first_name=customer.first_name,
        last_name=customer.last_name,
        document_type=customer.document_type,
        document_number=customer.document_number,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        is_active=customer.is_active,
        birth_date=customer.birth_date,
        gender=customer.gender,
        registration_date=customer.registration_date
    )


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update customer"""
    
    try:
        customer = await Customer.get(PydanticObjectId(customer_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Verify code if provided
    if customer_data.code and customer_data.code != customer.code:
        existing_customer = await Customer.find_one({"code": customer_data.code})
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer code already exists"
            )
    
    # Verify document if provided
    if (customer_data.document_number and 
        customer_data.document_number != customer.document_number):
        existing_doc = await Customer.find_one({"document_number": customer_data.document_number})
        if existing_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document number already exists"
            )
    
    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "code" and value:
            setattr(customer, field, value.upper())
        else:
            setattr(customer, field, value)
    
    await customer.save()
    
    return CustomerResponse(
        id=str(customer.id),
        code=customer.code,
        first_name=customer.first_name,
        last_name=customer.last_name,
        document_type=customer.document_type,
        document_number=customer.document_number,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        is_active=customer.is_active,
        birth_date=customer.birth_date,
        gender=customer.gender,
        registration_date=customer.registration_date
    )


# PAYMENT METHOD ENDPOINTS
@router.get("/payment-methods/", response_model=List[PaymentMethodResponse])
async def list_payment_methods(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List payment methods"""
    
    query_params = {}
    if active is not None:
        query_params["is_active"] = active
    
    payment_methods = await PaymentMethod.find(query_params).to_list()
    
    return [
        PaymentMethodResponse(
            id=str(method.id),
            code=method.code,
            name=method.name,
            type=method.type,
            is_active=method.is_active,
            requires_reference=method.requires_reference
        )
        for method in payment_methods
    ]


@router.post("/payment-methods/", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new payment method"""
    
    # Verify that code does not exist
    existing_payment_method = await PaymentMethod.find_one({"code": payment_method_data.code})
    if existing_payment_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method code already exists"
        )
    
    # Create payment method
    payment_method = PaymentMethod(
        code=payment_method_data.code.upper(),
        name=payment_method_data.name,
        type=payment_method_data.type,
        is_active=payment_method_data.is_active,
        requires_reference=payment_method_data.requires_reference
    )
    
    await payment_method.insert()
    
    return PaymentMethodResponse(
        id=str(payment_method.id),
        code=payment_method.code,
        name=payment_method.name,
        type=payment_method.type,
        is_active=payment_method.is_active,
        requires_reference=payment_method.requires_reference
    )
