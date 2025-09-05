from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from beanie import PydanticObjectId
from datetime import datetime

from app.models.product import Product, Category, UnitOfMeasure, PriceHistory
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    PriceChange,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    UnitOfMeasureCreate,
    UnitOfMeasureUpdate,
    UnitOfMeasureResponse
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.core.dependencies import get_current_active_user
from app.utils.validators import validate_product_code, validate_price

router = APIRouter(prefix="/products", tags=["Products"])


# PRODUCT ENDPOINTS
@router.get("", response_model=PaginatedResponse[ProductListResponse])
async def list_products(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name or code"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List products with pagination and filters"""
    
    # Build query
    query_params = {}
    
    if search:
        query_params["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    if category_id:
        query_params["category_id"] = category_id
    
    if active is not None:
        query_params["is_active"] = active
    
    # Get total
    total_products = await Product.find(query_params).count()
    
    # Get paginated products
    skip = (pagination.page - 1) * pagination.size
    product_list = await Product.find(query_params).skip(skip).limit(pagination.size).to_list()
    
    # Convert to response with category and unit information
    product_responses = []
    for product_item in product_list:
        # Get category
        category_item = await Category.get(product_item.category_id) if product_item.category_id else None
        unit_item = await UnitOfMeasure.get(product_item.unit_of_measure_id) if product_item.unit_of_measure_id else None
        
        product_responses.append(ProductListResponse(
            id=str(product_item.id),
            code=product_item.code,
            name=product_item.name,
            current_price=product_item.current_price,
            is_active=product_item.is_active,
            category=category_item.name if category_item else None,
            unit_of_measure=unit_item.abbreviation if unit_item else None
        ))
    
    total_pages = (total_products + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=product_responses,
        total=total_products,
        page=pagination.page,
        pages=total_pages,
        size=pagination.size,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new product"""
    
    # Validate code
    if not validate_product_code(product_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code format"
        )
    
    # Verify code doesn't exist
    existing_product = await Product.find_one({"code": product_data.code})
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product code already exists"
        )
    
    # Validate price
    if not validate_price(product_data.current_price):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid price"
        )
    
    # Verify category exists
    category = await Category.get(product_data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Verify unit of measure exists
    unit = await UnitOfMeasure.get(product_data.unit_of_measure_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit of measure not found"
        )
    
    # Create product
    product = Product(
        code=product_data.code.upper(),
        name=product_data.name,
        description=product_data.description,
        category_id=product_data.category_id,
        unit_of_measure_id=product_data.unit_of_measure_id,
        current_price=product_data.current_price,
        cost=product_data.cost,
        is_active=product_data.is_active,
        min_stock=product_data.min_stock,
        max_stock=product_data.max_stock
    )
    
    await product.insert()
    
    return ProductResponse(
        id=str(product.id),
        code=product.code,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        unit_of_measure_id=product.unit_of_measure_id,
        current_price=product.current_price,
        cost=product.cost,
        is_active=product.is_active,
        min_stock=product.min_stock,
        max_stock=product.max_stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
        image_path=product.image_path,
        price_history=product.price_history
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get product by ID"""
    
    try:
        product = await Product.get(PydanticObjectId(product_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse(
        id=str(product.id),
        code=product.code,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        unit_of_measure_id=product.unit_of_measure_id,
        current_price=product.current_price,
        cost=product.cost,
        is_active=product.is_active,
        min_stock=product.min_stock,
        max_stock=product.max_stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
        image_path=product.image_path,
        price_history=product.price_history
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update product"""
    
    try:
        product = await Product.get(PydanticObjectId(product_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Validate code if provided
    if product_data.code and not validate_product_code(product_data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code format"
        )
    
    # Verify code doesn't exist in another product
    if product_data.code and product_data.code != product.code:
        existing_product = await Product.find_one({"code": product_data.code})
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product code already exists"
            )
    
    # Validate price if provided
    if product_data.current_price and not validate_price(product_data.current_price):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid price"
        )
    
    # Verify category if provided
    if product_data.category_id:
        category = await Category.get(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
    
    # Verify unit of measure if provided
    if product_data.unit_of_measure_id:
        unit = await UnitOfMeasure.get(product_data.unit_of_measure_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit of measure not found"
            )
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "code" and value:
            setattr(product, field, value.upper())
        else:
            setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    await product.save()
    
    return ProductResponse(
        id=str(product.id),
        code=product.code,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        unit_of_measure_id=product.unit_of_measure_id,
        current_price=product.current_price,
        cost=product.cost,
        is_active=product.is_active,
        min_stock=product.min_stock,
        max_stock=product.max_stock,
        created_at=product.created_at,
        updated_at=product.updated_at,
        image_path=product.image_path,
        price_history=product.price_history
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete product (deactivate)"""
    
    try:
        product = await Product.get(PydanticObjectId(product_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Deactivate product instead of deleting
    product.is_active = False
    await product.save()
    
    return {"message": "Product deleted successfully"}


@router.post("/{product_id}/change-price")
async def change_product_price(
    product_id: str,
    price_change: PriceChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change product price and register in history"""
    
    try:
        product = await Product.get(PydanticObjectId(product_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Validate new price
    if not validate_price(price_change.new_price):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid price"
        )
    
    # Create history entry
    history_entry = PriceHistory(
        previous_price=product.current_price,
        new_price=price_change.new_price,
        user_id=str(current_user.id),
        reason=price_change.reason
    )
    
    # Update price and add to history
    product.current_price = price_change.new_price
    product.price_history.append(history_entry)
    product.updated_at = datetime.utcnow()
    
    await product.save()
    
    return {"message": "Price updated successfully"}


# CATEGORY ENDPOINTS
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List categories"""
    
    query = {}
    if active is not None:
        query["is_active"] = active
    
    categories = await Category.find(query).to_list()
    
    return [
        CategoryResponse(
            id=str(category.id),
            name=category.name,
            description=category.description,
            parent_category_id=category.parent_category_id,
            is_active=category.is_active,
            created_at=category.created_at
        )
        for category in categories
    ]


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new category"""
    
    # Verify name doesn't exist
    existing_category = await Category.find_one({"name": category_data.name})
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists"
        )
    
    # Create category
    category = Category(
        name=category_data.name,
        description=category_data.description,
        parent_category_id=category_data.parent_category_id,
        is_active=category_data.is_active
    )
    
    await category.insert()
    
    return CategoryResponse(
        id=str(category.id),
        name=category.name,
        description=category.description,
        parent_category_id=category.parent_category_id,
        is_active=category.is_active,
        created_at=category.created_at
    )


# UNIT OF MEASURE ENDPOINTS
@router.get("/units-of-measure", response_model=List[UnitOfMeasureResponse])
async def list_units_of_measure(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """List units of measure"""
    
    query = {}
    if active is not None:
        query["is_active"] = active
    
    units = await UnitOfMeasure.find(query).to_list()
    
    return [
        UnitOfMeasureResponse(
            id=str(unit.id),
            name=unit.name,
            abbreviation=unit.abbreviation,
            is_active=unit.is_active
        )
        for unit in units
    ]


@router.post("/units-of-measure", response_model=UnitOfMeasureResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_of_measure(
    unit_data: UnitOfMeasureCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new unit of measure"""
    
    # Verify name doesn't exist
    existing_unit = await UnitOfMeasure.find_one({"name": unit_data.name})
    if existing_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unit of measure name already exists"
        )
    
    # Verify abbreviation doesn't exist
    existing_abbrev = await UnitOfMeasure.find_one({"abbreviation": unit_data.abbreviation})
    if existing_abbrev:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Abbreviation already exists"
        )
    
    # Create unit of measure
    unit = UnitOfMeasure(
        name=unit_data.name,
        abbreviation=unit_data.abbreviation.upper(),
        is_active=unit_data.is_active
    )
    
    await unit.insert()
    
    return UnitOfMeasureResponse(
        id=str(unit.id),
        name=unit.name,
        abbreviation=unit.abbreviation,
        is_active=unit.is_active
    )
