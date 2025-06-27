import pytest
import time as t
from unittest.mock import patch, MagicMock
from app.modules.user.services.user import UserService
from app.modules.user.schemas.user import UserCreate, User
from firebase_admin import auth
from app.core.utils.error_codes import ErrorCodes

mock_token_id = "tokenIdTestForUserToTestValid"
mock_token_notUser = "tokenvalidtouserprovidedbutisnotregistred"
mock_token_email = "tokenvalidtouserbutuserisregisteredwithanothermethod"

mock_user = {
    "email": "user.test@gmail.com",
    "uid": "0987654321"
}

def mock_verify_token(tokenId: str):
    if tokenId == mock_token_id:
        return {
        "email": mock_user["email"],
        "uid": mock_user["uid"],
        "exp": int(t.time()) + 3600
    }
        
    
    if tokenId == mock_token_notUser:
        return {
            "email": "user.notRegistered@gmail.com",
            "uid": mock_user["uid"],
            "exp": int(t.time()) + 3600
        }
    
    if tokenId == mock_token_email:
        return {
            "email": mock_user["email"],
            "uid": mock_user["uid"],
            "exp": int(t.time()) + 3600
        }

    raise ValueError("Invalid token")

@pytest.mark.asyncio
async def test_user_creation(monkeypatch, mock_db):
    """Test que verifica la creación de usuarios"""
    monkeypatch.setattr(
        auth,
        "verify_id_token",
        mock_verify_token
    )
    users_collection = mock_db.get_collection("users")
    user_service = UserService(users_collection)
        
    user_data = UserCreate(
        email=mock_user["email"],
        full_name="Test User",
        token=mock_token_id,
        provider="password",
        username="testuser"
    )
        
    result = await user_service.create_user(user_data)
    
    user_in_db = await users_collection.find_one({"email": mock_user["email"]})

    assert user_in_db is not None
    assert user_in_db["full_name"] == "Test User"
    assert user_in_db["uid"] == mock_user["uid"]
    
    assert isinstance(result, User)
    assert result.email == mock_user["email"]
    assert result.full_name == "Test User"

@pytest.mark.asyncio
async def test_user_creation_invalid_email(monkeypatch, mock_db):
    """Test que verifica el rechazo de emails inválidos"""
    monkeypatch.setattr(
        auth,
        "verify_id_token",
        mock_verify_token
    )
    users_collection = mock_db.get_collection("users")
    user_service = UserService(users_collection)
    
    user_data = UserCreate(
        email="invalid-email",
        full_name="Test User",
        token=mock_token_id,
        provider="password",
        username="testuser"
    )
    with pytest.raises(Exception) as excinfo:
        await user_service.create_user(user_data)
    
    assert ErrorCodes.INVALID_EMAIL in str(excinfo.value)
    
@pytest.mark.asyncio
async def test_user_creation_duplicate_email(monkeypatch, mock_db):
    """Test que verifica que no se pueda registrar un email que ya está registrado"""
    monkeypatch.setattr(
        auth,
        "verify_id_token",
        mock_verify_token
    )
    users_collection = mock_db.get_collection("users")
    user_service = UserService(users_collection)
    
    user_data_1 = UserCreate(
        email=mock_user["email"],
        full_name="Test User 1",
        token=mock_token_id,
        provider="password",
        username="testuser1"
    )
    
    await user_service.create_user(user_data_1)
    
    user_data_2 = UserCreate(
        email=mock_user["email"],
        full_name="Test User 2",
        token=mock_token_id,
        provider="password",
        username="testuser2"
    )
    
    with pytest.raises(Exception) as excinfo:
        await user_service.create_user(user_data_2)
    
    assert ErrorCodes.EMAIL_ALREADY_REGISTERED in str(excinfo.value)
    
    users_in_db = await users_collection.find({"email": mock_user["email"]}).to_list(length=None)
    assert len(users_in_db) == 1
    assert users_in_db[0]["full_name"] == "Test User 1"
    
@pytest.mark.asyncio
async def test_user_creation_invalid_token(monkeypatch, mock_db):
    """Test que verifica que la creación de usuario falle con un token inválido"""
    monkeypatch.setattr(
        auth,
        "verify_id_token",
        mock_verify_token
    )
    users_collection = mock_db.get_collection("users")
    user_service = UserService(users_collection)
    
    user_data = UserCreate(
        email=mock_user["email"],
        full_name="Test User",
        token="invalid_token_that_will_fail",
        provider="google",
        username="testuser"
    )
    
    with pytest.raises(Exception) as excinfo:
        await user_service.create_user(user_data)
    
    assert ErrorCodes.INVALID_TOKEN in str(excinfo.value)
    
    user_in_db = await users_collection.find_one({"email": mock_user["email"]})
    assert user_in_db is None
    
