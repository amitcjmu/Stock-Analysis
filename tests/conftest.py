import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    try:
        from app.main import app
    except ImportError:
        # Try alternative import if app.main is not found
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/app')))
        from main import app
    return TestClient(app)
