from datetime import datetime as dt
from contextlib import nullcontext as does_not_raise

from pydantic import SecretStr, ValidationError

import pytest

from lecture_4.demo_service.core.users import (
    UserInfo, 
    UserRole, 
    UserEntity, 
    UserService,
    password_is_longer_than_8
)

@pytest.fixture
def valid_user_info():
    return UserInfo(
        username="john_doe",
        name="John Doe",
        birthdate=dt(1990, 1, 1),
        role=UserRole.USER,
        password=SecretStr("securepassword")
    )

@pytest.fixture
def invalid_password_user_info():
    return UserInfo(
        username="jane_doe",
        name="Jane Doe",
        birthdate=dt(1991, 2, 2),
        role=UserRole.USER,
        password=SecretStr("short")
    )


@pytest.fixture
def empty_user_service():
    return UserService(password_validators=[password_is_longer_than_8])

@pytest.fixture
def non_empty_user_service(valid_user_info):
    user_service = UserService(password_validators=[password_is_longer_than_8])
    user_service.register(valid_user_info)
    return user_service

@pytest.mark.parametrize(
    ("user_info", "expectation"),
    [
        # Test case 1: Valid user info
        (
            {
                "username": "john_doe",
                "name": "John Doe",
                "birthdate": dt(1990, 1, 1),
                "role": UserRole.USER,
                "password": SecretStr("securepassword")
            },
            does_not_raise()
        ),

        # Test case 2: Missing required field 'username'
        (
            {
                "name": "John Doe",
                "birthdate": dt(1990, 1, 1),
                "role": UserRole.USER,
                "password": SecretStr("securepassword")
            },
            pytest.raises(ValidationError)
        ),

        (
            {
                "username": "john_doe",
                "name": "John Doe",
                "birthdate": "1990-01-01",
                "role": UserRole.USER,
                "password": SecretStr("securepassword")
            },
            does_not_raise(),
        ),
        # Test case 3: Invalid birthdate format
        (
            {
                "username": "john_doe",
                "name": "John Doe",
                "birthdate": "01/01/1990",
                "role": UserRole.USER,
                "password": SecretStr("securepassword")
            },
            pytest.raises(ValidationError),
        ),
        # Test case 4: Invalid role type
        (
            {
                "username": "john_doe",
                "name": "John Doe",
                "birthdate": dt(1990, 1, 1),
                "role": "invalid_role",  # Should be a UserRole enum
                "password": SecretStr("securepassword")
            },
            pytest.raises(ValueError)
        ),
    ]
)
def test_user_info_initialization(user_info, expectation):
    with expectation:
        UserInfo(**user_info)

def test_user_entity_attributes(valid_user_info):
    user_entity = UserEntity(uid=1, info=valid_user_info)

    assert user_entity.uid == 1
    assert user_entity.info == valid_user_info
    assert user_entity.info.username == "john_doe"
    assert user_entity.info.name == "John Doe"
    assert user_entity.info.birthdate == dt(1990, 1, 1)
    assert user_entity.info.role == UserRole.USER
    assert user_entity.info.password.get_secret_value() == "securepassword"


@pytest.mark.parametrize(
    ("user_info", "user_service", "expectation"),
    [
        # Test case 1: Valid user registration
        ("valid_user_info", "empty_user_service", does_not_raise()),

        # Test case 2: Username already taken
        ("valid_user_info", "non_empty_user_service", pytest.raises(ValueError)),

        # Test case 3: Invalid password
        ("invalid_password_user_info", "empty_user_service", pytest.raises(ValueError)),
    ]
)
def test_register(user_info, user_service, expectation, request):
    # Replace fixture names with actual objects in args
    user_info = request.getfixturevalue(user_info)
    user_service = request.getfixturevalue(user_service)

    with expectation:
        user_service.register(user_info)

@pytest.mark.parametrize(
    ("username", "success"),
    [
        # Test case 1: User exists
        ("john_doe", True),

        # Test case 2: User does not exist
        ("nonexistent_user", False),
    ]
)
def test_get_by_username(username, success, request):
    # Register a user for subsequent tests
    user_service = request.getfixturevalue("non_empty_user_service")
    user = user_service.get_by_username(username)

    assert (user is not None) == success

    if success:
        assert user.info.username == username

@pytest.mark.parametrize(
    ("uid", "success"),
    [
        # Test case 1: User exists
        (1, True),

        # Test case 2: User does not exist
        (999, False),
    ]
)
def test_get_by_id(request, uid, success):
    # Register a user for subsequent tests
    user_service = request.getfixturevalue("non_empty_user_service")

    user = user_service.get_by_id(uid)

    assert (user is not None) == success

@pytest.mark.parametrize(
    ("user_id", "expectation"),
    [
        # Test case 1: Grant admin to existing user
        (1, does_not_raise()),

        # Test case 2: Grant admin to non-existent user
        (999, pytest.raises(ValueError)),
    ]
)
def test_grant_admin(request, user_id, expectation):
    # Register a user for subsequent tests
    user_service = request.getfixturevalue("non_empty_user_service")

    with expectation:
        user_service.grant_admin(user_id)