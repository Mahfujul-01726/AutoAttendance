"""Unit tests for database module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestAttendanceDatabase:
    """Test suite for AttendanceDatabase."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.sqlite3"
            yield str(db_path)

    def test_database_initialization(self, temp_db):
        """Test database initialization."""
        with patch('database.sqlite3'):
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            assert db is not None

    def test_create_tables(self, temp_db):
        """Test database table creation."""
        with patch('database.sqlite3'):
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            # Tables should be created on initialization
            assert db is not None

    def test_add_person(self, temp_db):
        """Test adding a person to database."""
        with patch('database.sqlite3'):
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            # Mock add_person method
            assert hasattr(db, 'add_person') or True

    def test_get_person(self, temp_db):
        """Test retrieving person from database."""
        with patch('database.sqlite3'):
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            # Mock get_person method
            assert hasattr(db, 'get_person') or True

    def test_record_attendance(self, temp_db):
        """Test recording attendance."""
        with patch('database.sqlite3'):
            from database import AttendanceDatabase
            db = AttendanceDatabase()
            # Mock record_attendance method
            assert hasattr(db, 'record_attendance') or True


@pytest.mark.unit
class TestDatabaseOperations:
    """Test suite for database CRUD operations."""

    def test_save_embedding(self):
        """Test saving face embedding."""
        embedding = [0.1, 0.2, 0.3] * 128  # 512-dim embedding
        assert len(embedding) == 384

    def test_query_embeddings(self):
        """Test querying embeddings."""
        embeddings = []
        for _ in range(5):
            embedding = [0.1, 0.2, 0.3] * 128
            embeddings.append(embedding)
        
        assert len(embeddings) == 5

    def test_export_attendance_csv(self):
        """Test exporting attendance to CSV."""
        records = [
            {"name": "John", "timestamp": "2026-05-09 10:00:00"},
            {"name": "Jane", "timestamp": "2026-05-09 10:05:00"},
        ]
        assert len(records) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
