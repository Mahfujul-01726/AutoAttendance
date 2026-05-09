"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def models_dir(project_root):
    """Return models directory path."""
    return project_root / "models"


@pytest.fixture(scope="function")
def mock_camera():
    """Mock camera capture object."""
    camera = MagicMock()
    camera.isOpened.return_value = True
    camera.get.return_value = 640
    camera.set.return_value = True
    return camera


@pytest.fixture(scope="function")
def mock_frame():
    """Create mock video frame."""
    import numpy as np
    return np.random.rand(480, 640, 3).astype(np.uint8)


@pytest.fixture(scope="function")
def mock_face_image():
    """Create mock face image."""
    import numpy as np
    return np.random.rand(112, 112, 3).astype(np.uint8)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_camera: mark test as requiring camera access"
    )
