from http import HTTPStatus
from datetime import datetime

import pytest
import pytest_asyncio
from pydantic import SecretStr

from fastapi.testclient import TestClient
from fastapi import FastAPI

from lecture_4.demo_service.api.users import router
from lecture_4.demo_service.api.utils import initialize, value_error_handler

@pytest.fixture(scope="session")
def app():
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(ValueError, value_error_handler)
    return app


@pytest_asyncio.fixture(scope="session")
async def client(app):
    async with initialize(app):
        yield TestClient(app)

@pytest.fixture
def valid_user_info():
    return {
        "username": "katunilya",
        "name": "Ilya Katun",
        "birthdate": datetime(1990, 1, 1).isoformat(),
        "password": "securepassword1"
    }

@pytest.fixture
def unpromoted_user_info():
    return {
        "username": "katunilya2",
        "name": "Ilya Katun",
        "birthdate": datetime(1990, 1, 1).isoformat(),
        "password": "securepassword1"
    }

@pytest.fixture
def invalid_user_info():
    return {
        "username": "jane_doe",
        "name": "Jane Doe",
        "birthdate": datetime(1991, 2, 2).isoformat(),
        "password": "short"
    }

@pytest.mark.parametrize(
    ("user_info", "expected_status"),
    [
        # Test case 1: Valid user registration
        ("valid_user_info", HTTPStatus.OK),
        ("unpromoted_user_info", HTTPStatus.OK),

        # Test case 2: Invalid password
        (
            "invalid_user_info", 
            HTTPStatus.BAD_REQUEST,
        
        ),

        # Test case 3: Missing required field 'username'
        (
            {
                "name": "John Doe", 
                "birthdate": datetime(1990, 1, 1).isoformat(), 
                "password": "securepassword1"
            }, 
            HTTPStatus.UNPROCESSABLE_ENTITY),

        # Test case 4: Invalid birthdate format
        (
            {
                "username": "john_doe", 
                "name": "John Doe", 
                "birthdate": "1990/01/01", 
                "password": "securepassword1"
            }, 
        HTTPStatus.UNPROCESSABLE_ENTITY),
    ]
)
@pytest.mark.asyncio
async def test_register_user(client, request, user_info, expected_status):
    user_info = (
        request.getfixturevalue(user_info) 
        if isinstance(user_info, str) 
        else user_info
    )
    response = client.post("/user-register", json=user_info)

    assert response.status_code == expected_status

    if expected_status == HTTPStatus.OK:
        data = response.json()
        assert data["username"] == user_info["username"]
        assert data["name"] == user_info["name"]
        assert data["birthdate"] == user_info["birthdate"]
        assert data["role"].upper() == "USER"

@pytest.mark.parametrize(
    ("params", "expected_status"),
    [
        # Test case 1: Get user by ID
        ({"id": 2}, HTTPStatus.OK),

        # Test case 2: Get user by username
        ({"username": "katunilya"}, HTTPStatus.OK),

        # Test case 3: User not found by ID
        ({"id": 999}, HTTPStatus.NOT_FOUND),

        # Test case 4: User not found by username
        ({"username": "nonexistent_user"}, HTTPStatus.NOT_FOUND),

        # Test case 5: Both ID and username provided
        (
            {"id": 2, "username": "katunilya"}, 
            HTTPStatus.BAD_REQUEST, 
        ),

        # Test case 6: Neither ID nor username provided
        (
            {}, 
            HTTPStatus.BAD_REQUEST,
        ),
    ]
)
@pytest.mark.asyncio
async def test_get_user(client, valid_user_info, params, expected_status):
    response = client.post("/user-get", params=params, auth=("admin", "superSecretAdminPassword123"))
    assert response.status_code == expected_status

    if expected_status == HTTPStatus.OK:
        data = response.json()
        assert data["username"] == valid_user_info["username"]
        assert data["name"] == valid_user_info["name"]
        assert data["birthdate"] == valid_user_info["birthdate"]
        assert data["role"].upper() == "USER"

@pytest.mark.parametrize(
    ("user_id", "expected_status"),
    [
        # Test case 1: Promote existing user
        (2, HTTPStatus.OK),

        # Test case 2: Promote non-existent user
        (
            999, 
            HTTPStatus.BAD_REQUEST,
        ),
    ]
)
@pytest.mark.asyncio
async def test_promote_user(client, user_id, expected_status):
    response = client.post("/user-promote", params={"id": user_id}, auth=("admin", "superSecretAdminPassword123"))
    assert response.status_code == expected_status

    if expected_status == HTTPStatus.OK:
        # Verify user is promoted
        response = client.post("/user-get", params={"id": user_id}, auth=("admin", "superSecretAdminPassword123"))
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["role"].upper() == "ADMIN"

@pytest.mark.asyncio
async def test_get_user_unauthorized(client):
    # Try to get user without authentication
    response = client.post("/user-get", params={"id": 1})
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.parametrize(
        ("auth", "status_code"),
        (
            (None, HTTPStatus.UNAUTHORIZED),
            (("admin", "securepassword1"), HTTPStatus.UNAUTHORIZED),
            (("katunilya2", "securepassword1"), HTTPStatus.FORBIDDEN),
        )
)
@pytest.mark.asyncio
async def test_promote_user_unauthorized(client, auth, status_code):
    # Try to promote user without authentication
    response = client.post("/user-promote", params={"id": 1}, auth=auth)
    assert response.status_code == status_code

