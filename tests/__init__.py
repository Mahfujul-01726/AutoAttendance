"""Test suite for AutoAttendance.

This package contains unit tests, integration tests, and fixtures for the
AutoAttendance face recognition attendance system.
"""

import pytest
from pathlib import Path

# Add parent directory to path for imports
TEST_DIR = Path(__file__).parent.absolute()
PROJECT_DIR = TEST_DIR.parent
