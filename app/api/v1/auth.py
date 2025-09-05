from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.user import User, Token as TokenModel
from app.models.audits import AccessLog
from app.schemas.user import (
    Token, 
    UserLogin, 
    UserResponse, 
    RefreshTokenRequest, 
    VerifyTokenRequest, 
    TokenVerifyResponse
)
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    verify_token
)
from app.core.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Iniciar sesión y obtener tokens"""
    
    # Buscar usuario
    user = await User.find_one({"username": form_data.username})
    
    # Log de intento de acceso
    access_log = AccessLog(
        attemptedUsername=form_data.username,
        ipAddress="127.0.0.1",  # TODO: Obtener IP real del request
        accessType="login",
        successful=False
    )
    
    if not user:
        access_log.failureReason = "Usuario no encontrado"
        await access_log.insert()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    if not user.is_active:
        access_log.userId = str(user.id)
        access_log.failureReason = "Usuario inactivo"
        await access_log.insert()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    if not verify_password(form_data.password, user.password):
        access_log.userId = str(user.id)
        access_log.failureReason = "Contraseña incorrecta"
        await access_log.insert()
        
        # Incrementar intentos fallidos
        user.failed_login_attempts += 1
        await user.save()
        
        # Bloquear usuario después de 5 intentos
        if user.failed_login_attempts >= 5:
            user.is_active = False
            await user.save()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario bloqueado por múltiples intentos fallidos"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Login exitoso
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Guardar tokens en base de datos
    access_token_doc = TokenModel(
        user_id=str(user.id),
        token=access_token,
        type="access",
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    await access_token_doc.insert()
    
    refresh_token_doc = TokenModel(
        user_id=str(user.id),
        token=refresh_token,
        type="refresh",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    await refresh_token_doc.insert()
    
    # Actualizar usuario
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    await user.save()
    
    # Log exitoso
    access_log.userId = str(user.id)
    access_log.successful = True
    await access_log.insert()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """Renovar token de acceso usando refresh token"""
    
    # Verificar refresh token
    user_id = verify_token(request.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido"
        )
    
    # Verificar que el token existe en la base de datos
    token_doc = await TokenModel.find_one({
        "token": request.refresh_token,
        "type": "refresh",
        "is_active": True
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh no válido"
        )
    
    # Verificar que no haya expirado
    if token_doc.expires_at < datetime.utcnow():
        token_doc.is_active = False
        await token_doc.save()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh expirado"
        )
    
    # Verificar usuario
    user = await User.get(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido"
        )
    
    # Desactivar tokens antiguos primero
    await TokenModel.find({"user_id": user_id, "is_active": True}).update({"$set": {"is_active": False}})
    
    # Crear nuevos tokens
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)
    
    # Guardar nuevos tokens
    new_access_token_doc = TokenModel(
        user_id=user_id,
        token=new_access_token,
        type="access",
        expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    await new_access_token_doc.insert()
    
    new_refresh_token_doc = TokenModel(
        user_id=user_id,
        token=new_refresh_token,
        type="refresh",
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    await new_refresh_token_doc.insert()
    
    # Log de refresh
    access_log = AccessLog(
        userId=user_id,
        attemptedUsername=user.username,
        ipAddress="127.0.0.1",  # TODO: Obtener IP real
        accessType="token_refresh",
        successful=True
    )
    await access_log.insert()
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Cerrar sesión y desactivar tokens"""
    
    # Desactivar todos los tokens del usuario
    await TokenModel.find({"user_id": str(current_user.id)}).update({"$set": {"is_active": False}})
    
    # Log de logout
    access_log = AccessLog(
        userId=str(current_user.id),
        attemptedUsername=current_user.username,
        ipAddress="127.0.0.1",  # TODO: Obtener IP real
        accessType="logout",
        successful=True
    )
    await access_log.insert()
    
    return {"message": "Sesión cerrada exitosamente"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        roles=current_user.roles,
        allowed_warehouses=current_user.allowed_warehouses,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        failed_login_attempts=current_user.failed_login_attempts
    )


@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_access_token(request: VerifyTokenRequest):
    """Verificar si un token es válido"""
    user_id = verify_token(request.token, "access")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Verificar que el token existe en la base de datos
    token_doc = await TokenModel.find_one({
        "token": request.token,
        "type": "access",
        "is_active": True
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido"
        )
    
    # Verificar que no haya expirado
    if token_doc.expires_at < datetime.utcnow():
        token_doc.is_active = False
        await token_doc.save()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    
    return TokenVerifyResponse(valid=True, user_id=user_id)