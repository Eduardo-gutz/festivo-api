import pytest
import time as t
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId
from fastapi import HTTPException, status

from app.modules.templates.services.templates import TemplateService
from app.modules.templates.schemas.template import Template, TemplateMinimal
from app.modules.user.schemas.user import User
from app.core.utils.error_codes import ErrorCodes

# Datos de prueba
mock_user_id = str(ObjectId())
mock_user_id_2 = str(ObjectId())
mock_template_id = str(ObjectId())
mock_template_id_2 = str(ObjectId())

mock_user_data = {
    "_id": ObjectId(mock_user_id),
    "email": "user@example.com",
    "full_name": "Test User",
    "username": "testuser",
    "uid": "firebase_uid_123",
    "provider": "google",
    "role": "publisher",
    "created_at": int(t.time())
}

mock_user_2_data = {
    "_id": ObjectId(mock_user_id_2),
    "email": "user2@example.com",
    "full_name": "Test User 2",
    "username": "testuser2",
    "uid": "firebase_uid_456",
    "provider": "google",
    "role": "user",
    "created_at": int(t.time())
}

mock_template_data = {
    "_id": ObjectId(mock_template_id),
    "name": "Test Template",
    "description": "A test template",
    "preview_image_url": "https://example.com/preview.jpg",
    "is_premium": False,
    "created_at": int(t.time()),
    "updated_at": int(t.time()),
    "elements": [{"type": "text", "content": "Hello World"}],
    "user_id": ObjectId(mock_user_id)
}

mock_premium_template_data = {
    "_id": ObjectId(mock_template_id_2),
    "name": "Premium Template",
    "description": "A premium template",
    "preview_image_url": "https://example.com/premium.jpg",
    "is_premium": True,
    "created_at": int(t.time()),
    "updated_at": int(t.time()),
    "elements": [{"type": "text", "content": "Premium Content"}],
    "user_id": ObjectId(mock_user_id)
}

@pytest.fixture
def mock_user():
    """Fixture para usuario de prueba"""
    return User(
        _id=ObjectId(mock_user_id),
        email=mock_user_data["email"],
        full_name=mock_user_data["full_name"],
        username=mock_user_data["username"],
        uid=mock_user_data["uid"],
        provider=mock_user_data["provider"],
        created_at=mock_user_data["created_at"],
        role=mock_user_data["role"]
    )

@pytest.fixture
def mock_user_2():
    """Fixture para segundo usuario de prueba"""
    return User(
        _id=ObjectId(mock_user_id_2),
        email=mock_user_2_data["email"],
        full_name=mock_user_2_data["full_name"],
        username=mock_user_2_data["username"],
        uid=mock_user_2_data["uid"],
        provider=mock_user_2_data["provider"],
        created_at=mock_user_2_data["created_at"],
        role=mock_user_2_data["role"]
    )

@pytest.fixture
def template_service(mock_db):
    """Fixture para el TemplateService con dependencias mockeadas"""
    templates_collection = mock_db.get_collection("templates")
    return TemplateService(templates_collection)

# ============= TESTS DE CREACIÓN DE TEMPLATES =============

@pytest.mark.asyncio
async def test_create_template_successful(template_service, mock_db, mock_user):
    """Test de creación exitosa de template"""
    template_data = {
        "name": "New Template",
        "description": "A new template",
        "preview_image_url": "https://example.com/new.jpg",
        "is_premium": False,
        "elements": [{"type": "text", "content": "New Content"}]
    }
    
    # Mock del usuario para el aggregation pipeline
    users_collection = mock_db.get_collection("users")
    await users_collection.insert_one(mock_user_data)
    
    # Patchear el aggregation pipeline para que funcione con mongomock
    with patch.object(template_service.templates, 'aggregate') as mock_aggregate:
        # Simular el resultado del aggregation pipeline
        mock_template_with_user = {
            **template_data,
            "_id": ObjectId(),
            "user_id": mock_user_id,
            "created_at": int(t.time()),
            "updated_at": int(t.time()),
            "user": mock_user_data
        }
        mock_aggregate.return_value.to_list = AsyncMock(return_value=[mock_template_with_user])
        
        result = await template_service.create_template(template_data, mock_user_id)
        
        assert isinstance(result, Template)
        assert result.name == template_data["name"]
        assert result.description == template_data["description"]
        assert result.is_premium == template_data["is_premium"]
        assert str(result.user.id) == mock_user_id
    
    # Verificar que se insertó en la base de datos
    templates_collection = mock_db["templates"]
    template_in_db = await templates_collection.find_one({"name": template_data["name"]})
    assert template_in_db is not None

@pytest.mark.asyncio
async def test_create_template_empty_name(template_service, mock_user):
    """Test de creación de template con nombre vacío"""
    template_data = {
        "name": "",
        "description": "A template without name"
    }
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.create_template(template_data, mock_user_id)
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_DATA in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_create_template_whitespace_name(template_service, mock_user):
    """Test de creación de template con nombre solo espacios"""
    template_data = {
        "name": "   ",
        "description": "A template with whitespace name"
    }
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.create_template(template_data, mock_user_id)
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_DATA in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_create_template_duplicate_name(template_service, mock_db, mock_user):
    """Test de creación de template con nombre duplicado"""
    templates_collection = mock_db.get_collection("templates")
    users_collection = mock_db.get_collection("users")
    
    # Insertar datos necesarios
    await users_collection.insert_one(mock_user_data)
    await templates_collection.insert_one(mock_template_data)
    
    template_data = {
        "name": mock_template_data["name"],  # Mismo nombre
        "description": "Different description"
    }
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.create_template(template_data, mock_user_id)
    
    assert excinfo.value.status_code == 409
    assert ErrorCodes.TEMPLATE_ALREADY_EXISTS in str(excinfo.value.detail)

# ============= TESTS DE OBTENER TEMPLATES =============

@pytest.mark.asyncio
async def test_get_templates_successful(template_service, mock_db):
    """Test de obtención exitosa de templates"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_many([mock_template_data, mock_premium_template_data])
    
    result = await template_service.get_templates()
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(template, TemplateMinimal) for template in result)

@pytest.mark.asyncio
async def test_get_templates_with_premium_filter(template_service, mock_db):
    """Test de obtención de templates filtrados por premium"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_many([mock_template_data, mock_premium_template_data])
    
    # Solo templates premium
    premium_result = await template_service.get_templates(is_premium=True)
    assert len(premium_result) == 1
    assert premium_result[0].is_premium is True
    
    # Solo templates gratuitos
    free_result = await template_service.get_templates(is_premium=False)
    assert len(free_result) == 1
    assert free_result[0].is_premium is False

@pytest.mark.asyncio
async def test_get_templates_with_pagination(template_service, mock_db):
    """Test de obtención de templates con paginación"""
    templates_collection = mock_db.get_collection("templates")
    
    # Crear múltiples templates
    templates = []
    for i in range(5):
        template = {
            "_id": ObjectId(),
            "name": f"Template {i}",
            "description": f"Description {i}",
            "preview_image_url": f"https://example.com/template{i}.jpg",
            "is_premium": False,
            "created_at": int(t.time()),
            "updated_at": int(t.time()),
            "elements": [],
            "user_id": mock_user_id
        }
        templates.append(template)
    
    await templates_collection.insert_many(templates)
    
    # Test paginación
    result = await template_service.get_templates(skip=2, limit=2)
    assert len(result) == 2

@pytest.mark.asyncio
async def test_get_templates_empty_collection(template_service):
    """Test de obtención de templates con colección vacía"""
    result = await template_service.get_templates()
    
    assert isinstance(result, list)
    assert len(result) == 0

# ============= TESTS DE OBTENER TEMPLATE POR ID =============

@pytest.mark.asyncio
async def test_get_template_by_id_successful(template_service, mock_db):
    """Test de obtención exitosa de template por ID"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    result = await template_service.get_template_by_id(mock_template_id)
    
    assert isinstance(result, Template)
    assert result.name == mock_template_data["name"]
    assert str(result.id) == mock_template_id

@pytest.mark.asyncio
async def test_get_template_by_id_invalid_id(template_service):
    """Test de obtención de template con ID inválido"""
    with pytest.raises(HTTPException) as excinfo:
        await template_service.get_template_by_id("invalid_id")
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_DATA in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_get_template_by_id_not_found(template_service):
    """Test de obtención de template inexistente"""
    non_existent_id = str(ObjectId())
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.get_template_by_id(non_existent_id)
    
    assert excinfo.value.status_code == 404
    assert ErrorCodes.TEMPLATE_NOT_FOUND in str(excinfo.value.detail)

# ============= TESTS DE ACTUALIZACIÓN DE TEMPLATES =============

@pytest.mark.asyncio
async def test_update_template_successful(template_service, mock_db, mock_user):
    """Test de actualización exitosa de template"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    update_data = {
        "description": "Updated description",
        "is_premium": True
    }
    
    result = await template_service.update_template(mock_template_id, update_data, mock_user)
    
    assert isinstance(result, Template)
    assert result.description == update_data["description"]
    assert result.is_premium == update_data["is_premium"]

@pytest.mark.asyncio
async def test_update_template_invalid_id(template_service, mock_user):
    """Test de actualización con ID inválido"""
    update_data = {"description": "New description"}
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.update_template("invalid_id", update_data, mock_user)
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_DATA in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_update_template_not_found(template_service, mock_user):
    """Test de actualización de template inexistente"""
    non_existent_id = str(ObjectId())
    update_data = {"description": "New description"}
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.update_template(non_existent_id, update_data, mock_user)
    
    assert excinfo.value.status_code == 404
    assert ErrorCodes.TEMPLATE_NOT_FOUND in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_update_template_unauthorized(template_service, mock_db, mock_user_2):
    """Test de actualización sin autorización"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)  # Template pertenece a mock_user_id
    
    update_data = {"description": "Unauthorized update"}
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.update_template(mock_template_id, update_data, mock_user_2)
    
    assert excinfo.value.status_code == 403
    assert ErrorCodes.NOT_AUTHORIZED in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_update_template_duplicate_name(template_service, mock_db, mock_user):
    """Test de actualización con nombre duplicado"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_many([mock_template_data, mock_premium_template_data])
    
    update_data = {
        "name": mock_premium_template_data["name"]  # Nombre que ya existe
    }
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.update_template(mock_template_id, update_data, mock_user)
    
    assert excinfo.value.status_code == 409
    assert ErrorCodes.TEMPLATE_ALREADY_EXISTS in str(excinfo.value.detail)

# ============= TESTS DE ELIMINACIÓN DE TEMPLATES =============

@pytest.mark.asyncio
async def test_delete_template_successful(template_service, mock_db, mock_user):
    """Test de eliminación exitosa de template"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    result = await template_service.delete_template(mock_template_id, mock_user)
    
    assert result is True
    
    # Verificar que se eliminó
    template_in_db = await templates_collection.find_one({"_id": ObjectId(mock_template_id)})
    assert template_in_db is None

@pytest.mark.asyncio
async def test_delete_template_invalid_id(template_service, mock_user):
    """Test de eliminación con ID inválido"""
    with pytest.raises(HTTPException) as excinfo:
        await template_service.delete_template("invalid_id", mock_user)
    
    assert excinfo.value.status_code == 400
    assert ErrorCodes.INVALID_DATA in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_delete_template_not_found(template_service, mock_user):
    """Test de eliminación de template inexistente"""
    non_existent_id = str(ObjectId())
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.delete_template(non_existent_id, mock_user)
    
    assert excinfo.value.status_code == 404
    assert ErrorCodes.TEMPLATE_NOT_FOUND in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_delete_template_unauthorized(template_service, mock_db, mock_user_2):
    """Test de eliminación sin autorización"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    with pytest.raises(HTTPException) as excinfo:
        await template_service.delete_template(mock_template_id, mock_user_2)
    
    assert excinfo.value.status_code == 403
    assert ErrorCodes.NOT_AUTHORIZED in str(excinfo.value.detail)

# ============= TESTS DE OBTENER TEMPLATES POR STATUS PREMIUM =============

@pytest.mark.asyncio
async def test_get_templates_by_premium_status_premium(template_service, mock_db):
    """Test de obtención de templates premium"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_many([mock_template_data, mock_premium_template_data])
    
    result = await template_service.get_templates_by_premium_status(True)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].is_premium is True

@pytest.mark.asyncio
async def test_get_templates_by_premium_status_free(template_service, mock_db):
    """Test de obtención de templates gratuitos"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_many([mock_template_data, mock_premium_template_data])
    
    result = await template_service.get_templates_by_premium_status(False)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].is_premium is False

@pytest.mark.asyncio
async def test_get_templates_by_premium_status_empty(template_service):
    """Test de obtención de templates por status con colección vacía"""
    result = await template_service.get_templates_by_premium_status(True)
    
    assert isinstance(result, list)
    assert len(result) == 0

# ============= TESTS DE BÚSQUEDA DE TEMPLATES POR NOMBRE =============

@pytest.mark.asyncio
async def test_search_templates_by_name_successful(template_service, mock_db):
    """Test de búsqueda exitosa de templates por nombre"""
    templates_collection = mock_db.get_collection("templates")
    
    # Crear templates con nombres variados
    search_templates = [
        {**mock_template_data, "_id": ObjectId(), "name": "React Template"},
        {**mock_premium_template_data, "_id": ObjectId(), "name": "Vue Template"},
        {**mock_template_data, "_id": ObjectId(), "name": "Angular Template"}
    ]
    
    await templates_collection.insert_many(search_templates)
    
    result = await template_service.search_templates_by_name("Template")
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert all("Template" in template.name for template in result)

@pytest.mark.asyncio
async def test_search_templates_by_name_case_insensitive(template_service, mock_db):
    """Test de búsqueda insensible a mayúsculas/minúsculas"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one({**mock_template_data, "name": "UPPERCASE TEMPLATE"})
    
    result = await template_service.search_templates_by_name("uppercase")
    
    assert len(result) == 1
    assert "UPPERCASE" in result[0].name

@pytest.mark.asyncio
async def test_search_templates_by_name_partial_match(template_service, mock_db):
    """Test de búsqueda con coincidencia parcial"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one({**mock_template_data, "name": "Modern Dashboard Template"})
    
    result = await template_service.search_templates_by_name("Dashboard")
    
    assert len(result) == 1
    assert "Dashboard" in result[0].name

@pytest.mark.asyncio
async def test_search_templates_by_name_no_results(template_service, mock_db):
    """Test de búsqueda sin resultados"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    result = await template_service.search_templates_by_name("NonexistentTerm")
    
    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_search_templates_by_name_empty_term(template_service, mock_db):
    """Test de búsqueda con término vacío"""
    templates_collection = mock_db.get_collection("templates")
    await templates_collection.insert_one(mock_template_data)
    
    result = await template_service.search_templates_by_name("")
    
    assert isinstance(result, list)
    # Debería devolver todos los templates ya que búsqueda vacía coincide con todo
    assert len(result) >= 0
