import pytest
import time as t
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId
from jose import JWTError
from firebase_admin import auth
from fastapi import HTTPException, status
from fastapi.security import SecurityScopes

from app.modules.auth.services.auth import AuthService
from app.modules.auth.services.token import TokenService
from app.modules.auth.schemas.token import Token
from app.modules.user.schemas.user import User
from app.core.utils.error_codes import ErrorCodes

# Mocks de tokens y datos de prueba
mock_access_token = "mock_access_token_valid"
mock_refresh_token = "mock_refresh_token_valid"
mock_firebase_token = "mock_firebase_token_valid"
mock_firebase_token_invalid = "mock_firebase_token_invalid"
mock_firebase_token_no_user = "mock_firebase_token_no_user"
mock_user_id = str(ObjectId())
mock_user_id_2 = str(ObjectId())

mock_user_data = {
    "_id": ObjectId(mock_user_id),
    "email": "test@example.com",
    "password": "$2b$12$hashedpassword",  # Hash de "password123"
    "full_name": "Test User",
    "username": "testuser",
    "uid": "firebase_uid_123",
    "provider": "google",
    "role": "user",
    "created_at": int(t.time())
}

mock_admin_user_data = {
    "_id": ObjectId(mock_user_id_2),
    "email": "admin@example.com",
    "password": "$2b$12$hashedpassword",
    "full_name": "Admin User",
    "username": "adminuser",
    "uid": "firebase_uid_admin",
    "provider": "google",
    "role": "admin",
    "created_at": int(t.time())
}

def mock_verify_firebase_token(token: str):
    """Mock para auth.verify_id_token de Firebase"""
    if token == mock_firebase_token:
        return {
            "uid": mock_user_data["uid"],
            "email": mock_user_data["email"],
            "exp": int(t.time()) + 3600
        }
    elif token == mock_firebase_token_no_user:
        return {
            "uid": "non_existent_uid",
            "email": "nouser@example.com",
            "exp": int(t.time()) + 3600
        }
    else:
        raise auth.InvalidIdTokenError("Invalid token")

class MockTokenService:
    """Mock del TokenService"""
    
    async def create_tokens(self, user_id: str, email: str) -> Token:
        return Token(
            access_token=mock_access_token,
            refresh_token=mock_refresh_token,
            token_type="bearer"
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        if refresh_token == mock_refresh_token:
            return Token(
                access_token="new_access_token",
                refresh_token="new_refresh_token",
                token_type="bearer"
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=ErrorCodes.INVALID_TOKEN
            )
    
    def decode_token(self, token: str) -> dict:
        if token == mock_access_token:
            return {
                "sub": mock_user_id,
                "email": mock_user_data["email"],
                "exp": int(t.time()) + 3600
            }
        elif token == "admin_token":
            return {
                "sub": mock_user_id_2,
                "email": mock_admin_user_data["email"],
                "exp": int(t.time()) + 3600
            }
        else:
            raise JWTError("Invalid token")

@pytest.fixture
def mock_token_service():
    """Fixture para el mock del TokenService"""
    return MockTokenService()

@pytest.fixture
def auth_service(mock_db, mock_token_service):
    """Fixture para el AuthService con dependencias mockeadas"""
    users_collection = mock_db.get_collection("users")
    return AuthService(users_collection, mock_token_service)

# ============= TESTS DE LOGIN CON FIREBASE =============

@pytest.mark.asyncio
async def test_login_with_firebase_successful(auth_service, mock_db, monkeypatch):
    """Test de login exitoso con Firebase"""
    monkeypatch.setattr(auth, "verify_id_token", mock_verify_firebase_token)
    
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    result = await auth_service.login_with_firebase(mock_firebase_token)
    
    assert isinstance(result, Token)
    assert result.access_token == mock_access_token
    assert result.refresh_token == mock_refresh_token

@pytest.mark.asyncio
async def test_login_with_firebase_invalid_token(auth_service, monkeypatch):
    """Test de login con token de Firebase inválido"""
    monkeypatch.setattr(auth, "verify_id_token", mock_verify_firebase_token)
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.login_with_firebase(mock_firebase_token_invalid)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_login_with_firebase_user_not_found(auth_service, monkeypatch):
    """Test de login con Firebase cuando el usuario no existe en la BD"""
    monkeypatch.setattr(auth, "verify_id_token", mock_verify_firebase_token)
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.login_with_firebase(mock_firebase_token_no_user)
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_EMAIL in str(excinfo.value.detail)

# ============= TESTS DE REFRESH TOKEN =============

@pytest.mark.asyncio
async def test_refresh_token_successful(auth_service):
    """Test de refresh token exitoso"""
    result = await auth_service.refresh_token(mock_refresh_token)
    
    assert isinstance(result, Token)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"

@pytest.mark.asyncio
async def test_refresh_token_invalid(auth_service):
    """Test de refresh token con token inválido"""
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.refresh_token("invalid_refresh_token")
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

# ============= TESTS DE GET USER BY TOKEN =============

@pytest.mark.asyncio
async def test_get_user_by_token_successful(auth_service, mock_db):
    """Test de obtener usuario por token exitoso"""
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    result = await auth_service.getUserByToken(mock_access_token)
    
    assert isinstance(result, User)
    assert result.email == mock_user_data["email"]
    assert result.full_name == mock_user_data["full_name"]
    assert str(result.id) == mock_user_id

@pytest.mark.asyncio
async def test_get_user_by_token_no_token(auth_service):
    """Test de obtener usuario sin token"""
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.getUserByToken(None)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_CREDENTIALS in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_user_by_token_invalid_token(auth_service):
    """Test de obtener usuario con token inválido"""
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.getUserByToken("invalid_token")
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_CREDENTIALS in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_user_by_token_user_not_found(auth_service):
    """Test de obtener usuario cuando el usuario del token no existe en BD"""
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.getUserByToken(mock_access_token)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_CREDENTIALS in str(excinfo.value.detail)

# ============= TESTS DE VERIFY USER CON SCOPES =============

@pytest.mark.asyncio
async def test_verify_user_no_scopes(auth_service, mock_db):
    """Test de verificar usuario sin scopes requeridos"""
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    security_scopes = SecurityScopes(scopes=[])
    result = await auth_service.verify_user(security_scopes, mock_access_token)
    
    assert isinstance(result, User)
    assert result.email == mock_user_data["email"]

@pytest.mark.asyncio
async def test_verify_user_with_valid_scopes(auth_service, mock_db):
    """Test de verificar usuario con scopes válidos"""
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    security_scopes = SecurityScopes(scopes=["user"])
    result = await auth_service.verify_user(security_scopes, mock_access_token)
    
    assert isinstance(result, User)
    assert result.role == "user"

@pytest.mark.asyncio
async def test_verify_user_with_admin_scopes(auth_service, mock_db):
    """Test de verificar usuario admin con scopes de admin"""
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_admin_user_data)
    
    security_scopes = SecurityScopes(scopes=["admin"])
    result = await auth_service.verify_user(security_scopes, "admin_token")
    
    assert isinstance(result, User)
    assert result.role == "admin"

@pytest.mark.asyncio
async def test_verify_user_insufficient_permissions(auth_service, mock_db):
    """Test de verificar usuario con permisos insuficientes"""
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    security_scopes = SecurityScopes(scopes=["admin"])
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.verify_user(security_scopes, mock_access_token)
    
    assert excinfo.value.status_code == 403
    assert ErrorCodes.NOT_AUTHORIZED in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_verify_user_invalid_token(auth_service):
    """Test de verificar usuario con token inválido"""
    security_scopes = SecurityScopes(scopes=["user"])
    
    with pytest.raises(HTTPException) as excinfo:
        await auth_service.verify_user(security_scopes, "invalid_token")
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_CREDENTIALS in str(excinfo.value.detail)
