import pytest
from contextlib import nullcontext as does_not_raise
from lecture_4.demo_service.api.main import create_app

def test_create_app():
    with does_not_raise():
        app = create_app()
        assert app is not None
        assert app.state is not None