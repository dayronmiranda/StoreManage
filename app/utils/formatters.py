"""
Utilities for formatting data
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, Union


def format_price(
    price: Optional[Union[Decimal, float, int]], 
    symbol: str = "$"
) -> str:
    """
    Format price with currency symbol
    
    Args:
        price: Price to format
        symbol: Currency symbol
        
    Returns:
        Formatted price as string
    """
    if price is None:
        price = 0
    
    try:
        # Convert to float for formatting
        price_float = float(price)
        # Format with commas and 2 decimals
        formatted_price = f"{price_float:,.2f}"
        return f"{symbol}{formatted_price}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"


def format_quantity(quantity: Optional[Union[Decimal, float, int]]) -> str:
    """
    Format quantity removing unnecessary decimals
    
    Args:
        quantity: Quantity to format
        
    Returns:
        Formatted quantity as string
    """
    if quantity is None:
        return "0"
    
    try:
        quantity_decimal = Decimal(str(quantity))
        
        # If it's a whole number, don't show decimals
        if quantity_decimal % 1 == 0:
            return f"{int(quantity_decimal):,}"
        else:
            # Show decimals only if necessary
            quantity_str = f"{quantity_decimal:,}"
            return quantity_str
    except (ValueError, TypeError):
        return "0"


def format_date(
    date: Optional[datetime], 
    format_str: str = "%d/%m/%Y"
) -> str:
    """
    Format date according to specified format
    
    Args:
        date: Date to format
        format_str: Date format
        
    Returns:
        Formatted date as string
    """
    if date is None:
        return ""
    
    try:
        return date.strftime(format_str)
    except (ValueError, AttributeError):
        return ""


def format_phone(phone: Optional[str]) -> str:
    """
    Format phone number
    
    Args:
        phone: Phone number
        
    Returns:
        Formatted phone
    """
    if not phone:
        return ""
    
    # Clean phone of non-numeric characters
    numbers = ''.join(filter(str.isdigit, phone))
    
    # If already formatted, return as is
    if any(char in phone for char in ['-', '(', ')', ' ']):
        return phone
    
    # Format according to length
    if len(numbers) == 10:
        return f"({numbers[:3]}) {numbers[3:6]}-{numbers[6:]}"
    elif len(numbers) == 9:
        return f"{numbers[:3]}-{numbers[3:6]}-{numbers[6:]}"
    elif len(numbers) == 8:
        return f"{numbers[:4]}-{numbers[4:]}"
    else:
        return phone


def format_document(
    document: Optional[str], 
    document_type: str
) -> str:
    """
    Format document according to its type
    
    Args:
        document: Document number
        document_type: Document type (id_card, passport, etc.)
        
    Returns:
        Formatted document
    """
    if not document:
        return ""
    
    if document_type == "id_card":
        # Format ID card with dots
        numbers = ''.join(filter(str.isdigit, document))
        if len(numbers) >= 8:
            if len(numbers) == 8:
                return f"{numbers[:2]}.{numbers[2:5]}.{numbers[5:]}"
            elif len(numbers) == 9:
                return f"{numbers[:3]}.{numbers[3:6]}.{numbers[6:]}"
            elif len(numbers) == 10:
                return f"{numbers[:1]}.{numbers[1:4]}.{numbers[4:7]}.{numbers[7:]}"
        return document
    
    elif document_type == "passport":
        # Passport remains as is
        return document
    
    else:
        # Unrecognized type, return as is
        return document


def format_percentage(
    percentage: Optional[Union[Decimal, float]], 
    decimals: int = 2
) -> str:
    """
    Format percentage
    
    Args:
        percentage: Percentage as decimal (0.15 = 15%)
        decimals: Number of decimals to show
        
    Returns:
        Formatted percentage as string
    """
    if percentage is None:
        percentage = 0
    
    try:
        percentage_float = float(percentage) * 100
        return f"{percentage_float:.{decimals}f}%"
    except (ValueError, TypeError):
        return f"0.{'0' * decimals}%"


def format_number(
    number: Optional[Union[int, float, Decimal]], 
    decimals: Optional[int] = None
) -> str:
    """
    Format number with thousands separators
    
    Args:
        number: Number to format
        decimals: Number of decimals (None for automatic)
        
    Returns:
        Formatted number as string
    """
    if number is None:
        return "0"
    
    try:
        if decimals is not None:
            return f"{float(number):,.{decimals}f}"
        else:
            # Automatic: show decimals only if necessary
            if isinstance(number, int) or float(number).is_integer():
                return f"{int(number):,}"
            else:
                return f"{float(number):,}"
    except (ValueError, TypeError):
        return "0"


def format_bytes(bytes_size: int) -> str:
    """
    Format byte size to readable format
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size (e.g., "1.5 MB")
    """
    if bytes_size == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration (e.g., "2h 30m 15s")
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    result = f"{hours}h"
    if remaining_minutes > 0:
        result += f" {remaining_minutes}m"
    if remaining_seconds > 0:
        result += f" {remaining_seconds}s"
    
    return result