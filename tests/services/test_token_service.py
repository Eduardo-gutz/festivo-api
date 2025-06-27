import pytest
import time as t
import uuid
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
from fastapi import HTTPException

from app.modules.auth.services.token import TokenService
from app.modules.auth.schemas.token import Token, TokenPayload
from app.core.utils.error_codes import ErrorCodes

# Constantes de prueba
TEST_SECRET_KEY = "test_secret_key_for_testing_only"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30
TEST_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Datos de prueba
mock_user_id = "507f1f77bcf86cd799439011"
mock_user_email = "test@example.com"
mock_jti_access = str(uuid.uuid4())
mock_jti_refresh = str(uuid.uuid4())

# Tokens de prueba válidos
def create_valid_access_token():
    """Crea un token de acceso válido para pruebas"""
    payload = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "exp": int(t.time()) + (TEST_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        "jti": mock_jti_access
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

def create_valid_refresh_token():
    """Crea un token de refresh válido para pruebas"""
    payload = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "exp": int(t.time()) + (TEST_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
        "jti": mock_jti_refresh
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

def create_expired_refresh_token():
    """Crea un token de refresh expirado para pruebas"""
    payload = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "exp": int(t.time()) - 3600,  # Expirado hace 1 hora
        "jti": mock_jti_refresh
    }
    return jwt.encode(payload, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

def create_invalid_token():
    """Crea un token inválido (con clave incorrecta)"""
    payload = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "exp": int(t.time()) + 3600,
        "jti": mock_jti_access
    }
    return jwt.encode(payload, "wrong_secret_key", algorithm=TEST_ALGORITHM)

@pytest.fixture
def token_service(mock_db):
    """Fixture para el TokenService con dependencias mockeadas"""
    tokens_collection = mock_db.get_collection("tokens")
    revoked_tokens_collection = mock_db.get_collection("revoked_tokens")
    
    service = TokenService(tokens_collection, revoked_tokens_collection)
    # Sobrescribir las constantes para testing
    service.SECRET_KEY = TEST_SECRET_KEY
    service.ALGORITHM = TEST_ALGORITHM
    
    return service

# ============= TESTS DE CREACIÓN DE TOKENS =============

@pytest.mark.asyncio
async def test_create_tokens_successful(token_service):
    """Test de creación exitosa de tokens"""
    with patch('app.modules.auth.services.token.ACCESS_TOKEN_EXPIRE_MINUTES', TEST_ACCESS_TOKEN_EXPIRE_MINUTES), \
         patch('app.modules.auth.services.token.REFRESH_TOKEN_EXPIRE_DAYS', TEST_REFRESH_TOKEN_EXPIRE_DAYS):
        
        result = await token_service.create_tokens(mock_user_id, mock_user_email)
        
        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0
        
        # Verificar que los tokens se pueden decodificar
        access_payload = token_service.decode_token(result.access_token)
        refresh_payload = token_service.decode_token(result.refresh_token)
        
        assert access_payload["sub"] == mock_user_id
        assert access_payload["email"] == mock_user_email
        assert refresh_payload["sub"] == mock_user_id
        assert refresh_payload["email"] == mock_user_email
        
        # Verificar tiempos de expiración
        current_time = int(t.time())
        assert access_payload["exp"] > current_time
        assert refresh_payload["exp"] > current_time
        assert refresh_payload["exp"] > access_payload["exp"]  # Refresh dura más

@pytest.mark.asyncio
async def test_create_tokens_with_empty_user_id(token_service):
    """Test de creación de tokens con user_id vacío"""
    result = await token_service.create_tokens("", mock_user_email)
    
    assert isinstance(result, Token)
    payload = token_service.decode_token(result.access_token)
    assert payload["sub"] == ""

@pytest.mark.asyncio
async def test_create_tokens_with_empty_email(token_service):
    """Test de creación de tokens con email vacío"""
    result = await token_service.create_tokens(mock_user_id, "")
    
    assert isinstance(result, Token)
    payload = token_service.decode_token(result.access_token)
    assert payload["email"] == ""


@pytest.mark.asyncio
async def test_refresh_access_token_successful(token_service):
    """Test de refresh de token exitoso"""
    valid_refresh_token = create_valid_refresh_token()
    
    with patch('app.modules.auth.services.token.ACCESS_TOKEN_EXPIRE_MINUTES', TEST_ACCESS_TOKEN_EXPIRE_MINUTES), \
         patch('app.modules.auth.services.token.REFRESH_TOKEN_EXPIRE_DAYS', TEST_REFRESH_TOKEN_EXPIRE_DAYS):
        
        result = await token_service.refresh_access_token(valid_refresh_token)
        
        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert result.refresh_token is not None
        
        # Verificar que los nuevos tokens contienen la misma información del usuario
        access_payload = token_service.decode_token(result.access_token)
        assert access_payload["sub"] == mock_user_id
        assert access_payload["email"] == mock_user_email

@pytest.mark.asyncio
async def test_refresh_access_token_expired(token_service):
    """Test de refresh con token expirado"""
    expired_refresh_token = create_expired_refresh_token()
    
    with pytest.raises(HTTPException) as excinfo:
        await token_service.refresh_access_token(expired_refresh_token)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_refresh_access_token_invalid(token_service):
    """Test de refresh con token inválido"""
    invalid_refresh_token = create_invalid_token()
    
    with pytest.raises(HTTPException) as excinfo:
        await token_service.refresh_access_token(invalid_refresh_token)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_refresh_access_token_malformed(token_service):
    """Test de refresh con token malformado"""
    malformed_token = "token.malformado.aqui"
    
    with pytest.raises(HTTPException) as excinfo:
        await token_service.refresh_access_token(malformed_token)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_refresh_access_token_missing_sub(token_service):
    """Test de refresh con token sin campo 'sub'"""
    payload_without_sub = {
        "email": mock_user_email,
        "exp": int(t.time()) + 3600,
        "jti": mock_jti_refresh
    }
    token_without_sub = jwt.encode(payload_without_sub, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    with pytest.raises(HTTPException) as excinfo:
        await token_service.refresh_access_token(token_without_sub)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_refresh_access_token_missing_email(token_service):
    """Test de refresh con token sin campo 'email'"""
    payload_without_email = {
        "sub": mock_user_id,
        "exp": int(t.time()) + 3600,
        "jti": mock_jti_refresh
    }
    token_without_email = jwt.encode(payload_without_email, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    with pytest.raises(HTTPException) as excinfo:
        await token_service.refresh_access_token(token_without_email)
    
    assert excinfo.value.status_code == 401
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_refresh_access_token_no_expiration(token_service):
    """Test de refresh con token sin campo 'exp'"""
    payload_without_exp = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "jti": mock_jti_refresh
    }
    token_without_exp = jwt.encode(payload_without_exp, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)
    
    # Sin campo 'exp', no debería fallar por expiración
    with patch('app.modules.auth.services.token.ACCESS_TOKEN_EXPIRE_MINUTES', TEST_ACCESS_TOKEN_EXPIRE_MINUTES), \
         patch('app.modules.auth.services.token.REFRESH_TOKEN_EXPIRE_DAYS', TEST_REFRESH_TOKEN_EXPIRE_DAYS):
        
        result = await token_service.refresh_access_token(token_without_exp)
        assert isinstance(result, Token)

# ============= TESTS DE INTEGRACIÓN =============

@pytest.mark.asyncio
async def test_token_lifecycle(token_service):
    """Test del ciclo completo de vida de un token"""
    with patch('app.modules.auth.services.token.ACCESS_TOKEN_EXPIRE_MINUTES', TEST_ACCESS_TOKEN_EXPIRE_MINUTES), \
         patch('app.modules.auth.services.token.REFRESH_TOKEN_EXPIRE_DAYS', TEST_REFRESH_TOKEN_EXPIRE_DAYS):
        
        # 1. Crear tokens iniciales
        initial_tokens = await token_service.create_tokens(mock_user_id, mock_user_email)
        
        # 2. Verificar que se pueden decodificar
        access_payload = token_service.decode_token(initial_tokens.access_token)
        refresh_payload = token_service.decode_token(initial_tokens.refresh_token)
        
        assert access_payload["sub"] == mock_user_id
        assert refresh_payload["sub"] == mock_user_id
        
        # 3. Usar refresh token para obtener nuevos tokens
        new_tokens = await token_service.refresh_access_token(initial_tokens.refresh_token)
        
        # 4. Verificar que los nuevos tokens son diferentes pero válidos
        assert new_tokens.access_token != initial_tokens.access_token
        assert new_tokens.refresh_token != initial_tokens.refresh_token
        
        new_access_payload = token_service.decode_token(new_tokens.access_token)
        assert new_access_payload["sub"] == mock_user_id
        assert new_access_payload["email"] == mock_user_email
