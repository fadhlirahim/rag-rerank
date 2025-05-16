import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import setup_logging
from app.main import app as fastapi_app

# Setup test logging
setup_logging()


@pytest.fixture
def app() -> FastAPI:
    """Return the FastAPI app for testing."""
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Return a test client for the FastAPI app."""
    return TestClient(app)
