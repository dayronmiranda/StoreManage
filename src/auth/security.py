# Para MVP, no necesitamos hashing de contraseñas


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify password - for MVP, compare plain text"""
    return plain_password == stored_password


def get_password_hash(password: str) -> str:
    """Generate password hash - for MVP, return plain text"""
    return password