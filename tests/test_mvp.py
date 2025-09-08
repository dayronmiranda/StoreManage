#!/usr/bin/env python3
"""
Script de prueba simple para verificar la funcionalidad básica del MVP
"""

from app.core.security import verify_password, get_password_hash

def test_password_functions():
    """Test password functions"""
    password = "test123"
    hashed = get_password_hash(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verified: {verify_password(password, hashed)}")
    print(f"Wrong password verified: {verify_password('wrong', hashed)}")

def test_user_schema():
    """Test user schema"""
    try:
        from app.schemas.user import UserLogin
        login = UserLogin(username="test", password="pass")
        print(f"UserLogin created: {login}")
    except Exception as e:
        print(f"Error creating UserLogin: {e}")

def test_config():
    """Test config"""
    try:
        from app.config import settings
        print(f"MongoDB URL: {settings.MONGODB_URL}")
        print(f"Environment: {settings.ENVIRONMENT}")
    except Exception as e:
        print(f"Error loading config: {e}")

if __name__ == "__main__":
    print("=== Testing MVP functionality ===")
    test_password_functions()
    print()
    test_user_schema()
    print()
    test_config()
    print("=== Tests completed ===")