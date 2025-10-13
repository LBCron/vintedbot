import pytest
from backend.db import create_tables


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables before running tests"""
    create_tables()
    yield
