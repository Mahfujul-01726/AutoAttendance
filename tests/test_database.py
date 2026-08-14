"""Unit tests for database module."""

import os
import tempfile
import unittest
import numpy as np
from pathlib import Path

from auto_attendance.database import AttendanceDatabase


class TestAttendanceDatabase(unittest.TestCase):
    """Test suite for AttendanceDatabase."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_attendance.sqlite3")
        self.db = AttendanceDatabase(self.db_path)

    def tearDown(self):
        del self.db
        import gc
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_database_initialization(self):
        """Test database initialization and schema creation."""
        self.assertTrue(os.path.exists(self.db_path))

    def test_upsert_student(self):
        """Test creating and updating a student."""
        student_id = self.db.upsert_student("Test Student", department="CSE", email="test@test.edu")
        self.assertIsInstance(student_id, int)
        self.assertGreater(student_id, 0)

        students = self.db.list_students()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["name"], "Test Student")

    def test_dual_memory_embeddings(self):
        """Test storing and loading dual-memory embeddings."""
        student_id = self.db.upsert_student("Mahfuj")
        dummy_vector = np.random.randn(512).astype(np.float32)
        dummy_vector = dummy_vector / np.linalg.norm(dummy_vector)

        self.db.add_embedding(student_id, dummy_vector, model_name="buffalo_l", quality_score=0.95)
        
        loaded = self.db.load_embeddings()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["student_name"], "Mahfuj")
        self.assertIn("ltm_anchor", loaded[0])
        self.assertIn("stm_prototype", loaded[0])

        # Test updating STM prototype
        new_vector = np.random.randn(512).astype(np.float32)
        self.db.update_stm_embedding(loaded[0]["id"], new_vector, drift_score=0.12)
        
        reloaded = self.db.load_embeddings()
        self.assertEqual(reloaded[0]["adaptation_count"], 1)
        self.assertEqual(reloaded[0]["last_drift"], 0.12)

    def test_adaptation_audit_logging(self):
        """Test logging and retrieving adaptation audit events."""
        student_id = self.db.upsert_student("Audit Tester")
        self.db.log_adaptation_event(
            student_id=student_id,
            student_name="Audit Tester",
            alpha=0.912,
            quality_score=0.88,
            liveness_score=0.95,
            drift_score=0.045,
            status="UPDATED"
        )

        logs = self.db.list_adaptation_logs(limit=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["student_name"], "Audit Tester")
        self.assertEqual(logs[0]["status"], "UPDATED")

    def test_attendance_marking(self):
        """Test recording attendance."""
        student_id = self.db.upsert_student("Attendance Tester")
        marked = self.db.mark_attendance(student_id, "Attendance Tester", confidence=0.15)
        self.assertTrue(marked)

        # Duplicate attendance on same date should be ignored
        duplicate = self.db.mark_attendance(student_id, "Attendance Tester", confidence=0.12)
        self.assertFalse(duplicate)

        records = self.db.list_attendance()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["student_name"], "Attendance Tester")


if __name__ == "__main__":
    unittest.main()
