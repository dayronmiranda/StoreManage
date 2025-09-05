import re
from typing import Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone format"""
    if not phone:
        return False
    # Accepts formats: +1234567890, 1234567890, (123) 456-7890, etc.
    # But must have at least 7 digits
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    pattern = r'^[\+]?[1-9][\d]{6,15}$'
    return re.match(pattern, clean_phone) is not None


def validate_document(document_number: str, document_type: str) -> bool:
    """Validate document number according to type"""
    if not document_number or not document_type:
        return False
        
    if document_type == "id_card":
        # Basic validation for ID card (numbers only, length)
        return document_number.isdigit() and 6 <= len(document_number) <= 10
    
    elif document_type == "tax_id":
        # Basic validation for NIT
        return document_number.replace("-", "").isdigit()
    
    elif document_type == "passport":
        # Basic validation for passport (alphanumeric)
        return re.match(r'^[A-Z0-9]{6,12}$', document_number.upper()) is not None
    
    return False


def validate_product_code(code: str) -> bool:
    """Validate product code format"""
    if not code:
        return False
    # Allows letters, numbers and hyphens
    pattern = r'^[A-Z0-9\-]{3,20}$'
    return re.match(pattern, code.upper()) is not None


def validate_price(price: Decimal) -> bool:
    """Validate that the price is valid"""
    if price is None:
        return False
    try:
        if isinstance(price, str):
            price = Decimal(price)
        elif not isinstance(price, (Decimal, int, float)):
            return False
        price = Decimal(str(price))
        return price > 0 and price <= Decimal('999999.99')
    except (ValueError, TypeError, InvalidOperation):
        return False


def validate_quantity(quantity: Decimal) -> bool:
    """Validate that the quantity is valid"""
    if quantity is None:
        return False
    try:
        if isinstance(quantity, str):
            quantity = Decimal(quantity)
        elif not isinstance(quantity, (Decimal, int, float)):
            return False
        quantity = Decimal(str(quantity))
        return quantity > 0 and quantity <= Decimal('999999.999')
    except (ValueError, TypeError, InvalidOperation):
        return False


def validate_percentage(percentage: Decimal) -> bool:
    """Validate that the percentage is between 0 and 100"""
    return Decimal('0') <= percentage <= Decimal('100')


def validate_future_date(date: datetime) -> bool:
    """Validate that the date is in the future"""
    return date > datetime.utcnow()


def validate_past_date(date: datetime) -> bool:
    """Validate that the date is in the past"""
    return date <= datetime.utcnow()


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate that the date range is valid"""
    return start_date <= end_date


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra spaces and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def validate_text_length(text: str, min_length: int, max_length: int) -> bool:
    """Validate text length"""
    if not text:
        return min_length == 0
    
    return min_length <= len(text.strip()) <= max_length


def validate_numbers_only(text: str) -> bool:
    """Validate that text contains only numbers"""
    return text.isdigit()


def validate_letters_only(text: str) -> bool:
    """Validate that text contains only letters"""
    return text.replace(" ", "").isalpha()


def validate_alphanumeric(text: str) -> bool:
    """Validate that text is alphanumeric"""
    return text.replace(" ", "").isalnum()


def normalize_code(code: str) -> str:
    """Normalize code (uppercase, no spaces)"""
    return code.upper().strip().replace(" ", "")


def validate_ip(ip: str) -> bool:
    """Validate IP address format"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?:\/\/(?:[-\w.])+(?:\:[0-9]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None


class CustomValidator:
    """Class for custom business validations"""
    
    @staticmethod
    def validate_min_max_stock(min_stock: Optional[Decimal], max_stock: Optional[Decimal]) -> bool:
        """Validate that minimum stock is less than maximum"""
        if min_stock is None or max_stock is None:
            return True
        
        return min_stock <= max_stock
    
    @staticmethod
    def validate_price_cost(price: Decimal, cost: Decimal) -> bool:
        """Validate that price is greater than cost"""
        return price >= cost
    
    @staticmethod
    def validate_sale_discount(discount: Decimal, subtotal: Decimal) -> bool:
        """Validate that discount is not greater than subtotal"""
        return discount <= subtotal
    
    @staticmethod
    def validate_warehouse_capacity(current_capacity: int, max_capacity: Optional[int]) -> bool:
        """Validate warehouse capacity"""
        if max_capacity is None:
            return True
        
        return current_capacity <= max_capacity