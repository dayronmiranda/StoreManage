from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Form

from src.models.user import User
from src.models.audit import AccessLog
from src.auth.security import verify_password

router = APIRouter(tags=["Authentication"])


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Iniciar sesión simple con username y password"""

    # Buscar usuario
    user = await User.find_one({"username": username})

    # Log de intento de acceso
    access_log = AccessLog(
        attemptedUsername=username,
        ipAddress="127.0.0.1",
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

    if not verify_password(password, user.password):
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
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    await user.save()

    # Log exitoso
    access_log.userId = str(user.id)
    access_log.successful = True
    await access_log.insert()

    return {
        "message": "Login exitoso",
        "user_id": str(user.id),
        "username": user.username
    }


@router.get("/me")
async def get_current_user_info():
    """Obtener información del usuario actual - simplificado"""
    # Para MVP, devolver usuario dummy o requerir autenticación básica
    return {"message": "Funcionalidad simplificada para MVP"}


@router.post("/logout")
async def logout():
    """Cerrar sesión - simplificado"""
    return {"message": "Sesión cerrada exitosamente"}