from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.usuario import Usuario, Token as TokenModel
from app.models.auditoria import LogAcceso
from app.schemas.usuario import (
    Token, 
    UsuarioLogin, 
    UsuarioResponse, 
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
    user = await Usuario.find_one({"username": form_data.username})
    
    # Log de intento de acceso
    log_acceso = LogAcceso(
        username_intento=form_data.username,
        ip_address="127.0.0.1",  # TODO: Obtener IP real del request
        tipo_acceso="login",
        exitoso=False
    )
    
    if not user:
        log_acceso.motivo_fallo = "Usuario no encontrado"
        await log_acceso.insert()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    if not user.activo:
        log_acceso.usuario_id = str(user.id)
        log_acceso.motivo_fallo = "Usuario inactivo"
        await log_acceso.insert()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    if not verify_password(form_data.password, user.password):
        log_acceso.usuario_id = str(user.id)
        log_acceso.motivo_fallo = "Contraseña incorrecta"
        await log_acceso.insert()
        
        # Incrementar intentos fallidos
        user.intentos_fallidos += 1
        await user.save()
        
        # Bloquear usuario después de 5 intentos
        if user.intentos_fallidos >= 5:
            user.activo = False
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
        usuario_id=str(user.id),
        token=access_token,
        tipo="access",
        fecha_expiracion=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    await access_token_doc.insert()
    
    refresh_token_doc = TokenModel(
        usuario_id=str(user.id),
        token=refresh_token,
        tipo="refresh",
        fecha_expiracion=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    await refresh_token_doc.insert()
    
    # Actualizar usuario
    user.ultimo_acceso = datetime.utcnow()
    user.intentos_fallidos = 0
    await user.save()
    
    # Log exitoso
    log_acceso.usuario_id = str(user.id)
    log_acceso.exitoso = True
    await log_acceso.insert()
    
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
        "tipo": "refresh",
        "activo": True
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh no válido"
        )
    
    # Verificar que no haya expirado
    if token_doc.fecha_expiracion < datetime.utcnow():
        token_doc.activo = False
        await token_doc.save()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh expirado"
        )
    
    # Verificar usuario
    user = await Usuario.get(user_id)
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no válido"
        )
    
    # Desactivar tokens antiguos primero
    await TokenModel.find({"usuario_id": user_id, "activo": True}).update({"$set": {"activo": False}})
    
    # Crear nuevos tokens
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)
    
    # Guardar nuevos tokens
    new_access_token_doc = TokenModel(
        usuario_id=user_id,
        token=new_access_token,
        tipo="access",
        fecha_expiracion=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    await new_access_token_doc.insert()
    
    new_refresh_token_doc = TokenModel(
        usuario_id=user_id,
        token=new_refresh_token,
        tipo="refresh",
        fecha_expiracion=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    await new_refresh_token_doc.insert()
    
    # Log de refresh
    log_acceso = LogAcceso(
        usuario_id=user_id,
        username_intento=user.username,
        ip_address="127.0.0.1",  # TODO: Obtener IP real
        tipo_acceso="token_refresh",
        exitoso=True
    )
    await log_acceso.insert()
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(current_user: Usuario = Depends(get_current_user)):
    """Cerrar sesión y desactivar tokens"""
    
    # Desactivar todos los tokens del usuario
    await TokenModel.find({"usuario_id": str(current_user.id)}).update({"$set": {"activo": False}})
    
    # Log de logout
    log_acceso = LogAcceso(
        usuario_id=str(current_user.id),
        username_intento=current_user.username,
        ip_address="127.0.0.1",  # TODO: Obtener IP real
        tipo_acceso="logout",
        exitoso=True
    )
    await log_acceso.insert()
    
    return {"message": "Sesión cerrada exitosamente"}


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return UsuarioResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        activo=current_user.activo,
        roles=current_user.roles,
        almacenes_permitidos=current_user.almacenes_permitidos,
        fecha_creacion=current_user.fecha_creacion,
        ultimo_acceso=current_user.ultimo_acceso,
        intentos_fallidos=current_user.intentos_fallidos
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
        "tipo": "access",
        "activo": True
    })
    
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido"
        )
    
    # Verificar que no haya expirado
    if token_doc.fecha_expiracion < datetime.utcnow():
        token_doc.activo = False
        await token_doc.save()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    
    return TokenVerifyResponse(valid=True, user_id=user_id)