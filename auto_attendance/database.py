import contextlib
import json
import os
import sqlite3
from datetime import datetime

import numpy as np

from .config import DATABASE_PATH, MODELS_DIR


class AttendanceDatabase:
    """SQLite storage for students, dual-memory face embeddings, attendance, and adaptation audit logs."""

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or MODELS_DIR, exist_ok=True)
        self._init_schema()

    @contextlib.contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    external_id TEXT,
                    department TEXT,
                    email TEXT,
                    phone TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    anchor_embedding BLOB,
                    active_embedding BLOB,
                    embedding_dim INTEGER NOT NULL,
                    image_path TEXT,
                    model_name TEXT NOT NULL,
                    quality_score REAL,
                    adaptation_count INTEGER DEFAULT 0,
                    last_drift REAL DEFAULT 0.0,
                    rollback_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS adaptation_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    student_name TEXT NOT NULL,
                    alpha REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    liveness_score REAL NOT NULL,
                    drift_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    student_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    camera_id TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(student_name, date),
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    image_path TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            # Automatic schema migration for existing databases
            self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        """Safely add missing columns to face_embeddings if database was created with old schema."""
        cursor = conn.execute("PRAGMA table_info(face_embeddings)")
        columns = [row["name"] for row in cursor.fetchall()]
        
        migrations = [
            ("anchor_embedding", "BLOB"),
            ("active_embedding", "BLOB"),
            ("adaptation_count", "INTEGER DEFAULT 0"),
            ("last_drift", "REAL DEFAULT 0.0"),
            ("rollback_count", "INTEGER DEFAULT 0"),
            ("updated_at", "TEXT"),
        ]
        
        for col_name, col_type in migrations:
            if col_name not in columns:
                try:
                    conn.execute(f"ALTER TABLE face_embeddings ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass

    def upsert_student(self, name, **fields):
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO students (name, external_id, department, email, phone, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    external_id = COALESCE(excluded.external_id, students.external_id),
                    department = COALESCE(excluded.department, students.department),
                    email = COALESCE(excluded.email, students.email),
                    phone = COALESCE(excluded.phone, students.phone),
                    status = excluded.status
                """,
                (
                    name,
                    fields.get("external_id"),
                    fields.get("department"),
                    fields.get("email"),
                    fields.get("phone"),
                    fields.get("status", "active"),
                    now,
                ),
            )
            row = conn.execute("SELECT id FROM students WHERE name = ?", (name,)).fetchone()
            return int(row["id"])

    def clear_embeddings(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM face_embeddings")

    def add_embedding(self, student_id, embedding, image_path=None, model_name="unknown", quality_score=None):
        embedding_array = np.asarray(embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
            
        raw_bytes = embedding_array.tobytes()
        now = datetime.now().isoformat(timespec="seconds")
        
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO face_embeddings
                    (student_id, embedding, anchor_embedding, active_embedding, embedding_dim, image_path, model_name, quality_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    raw_bytes,
                    raw_bytes,  # LTM Anchor
                    raw_bytes,  # STM Active prototype
                    int(embedding_array.shape[0]),
                    image_path,
                    model_name,
                    quality_score,
                    now,
                    now,
                ),
            )

    def update_stm_embedding(self, embedding_id: int, new_stm_vector: np.ndarray, drift_score: float, is_rollback: bool = False):
        """Update the active STM prototype in the database after a safe adaptation or rollback."""
        stm_array = np.asarray(new_stm_vector, dtype=np.float32)
        norm = np.linalg.norm(stm_array)
        if norm > 0:
            stm_array = stm_array / norm
            
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            if is_rollback:
                conn.execute(
                    """
                    UPDATE face_embeddings
                    SET active_embedding = ?,
                        last_drift = ?,
                        rollback_count = rollback_count + 1,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (stm_array.tobytes(), float(drift_score), now, embedding_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE face_embeddings
                    SET active_embedding = ?,
                        last_drift = ?,
                        adaptation_count = adaptation_count + 1,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (stm_array.tobytes(), float(drift_score), now, embedding_id),
                )

    def log_adaptation_event(
        self,
        student_id: int,
        student_name: str,
        alpha: float,
        quality_score: float,
        liveness_score: float,
        drift_score: float,
        status: str
    ):
        """Log an adaptation, rollback, or bypass event into adaptation_audit_logs."""
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO adaptation_audit_logs
                    (student_id, student_name, alpha, quality_score, liveness_score, drift_score, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (student_id, student_name, float(alpha), float(quality_score), float(liveness_score), float(drift_score), status, now),
            )

    def list_adaptation_logs(self, limit: int = 100):
        """Fetch recent adaptation audit log records."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, student_id, student_name, alpha, quality_score, liveness_score, drift_score, status, created_at
                FROM adaptation_audit_logs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def load_embeddings(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    face_embeddings.id,
                    face_embeddings.student_id,
                    face_embeddings.embedding,
                    face_embeddings.anchor_embedding,
                    face_embeddings.active_embedding,
                    face_embeddings.embedding_dim,
                    face_embeddings.image_path,
                    face_embeddings.model_name,
                    face_embeddings.quality_score,
                    face_embeddings.adaptation_count,
                    face_embeddings.last_drift,
                    face_embeddings.rollback_count,
                    students.name AS student_name
                FROM face_embeddings
                JOIN students ON students.id = face_embeddings.student_id
                WHERE students.status = 'active'
                """
            ).fetchall()

        embeddings = []
        for row in rows:
            dim = int(row["embedding_dim"])
            # Fallbacks for raw / anchor / active
            raw_vec = np.frombuffer(row["embedding"], dtype=np.float32, count=dim)
            
            if row["anchor_embedding"] is not None:
                anchor_vec = np.frombuffer(row["anchor_embedding"], dtype=np.float32, count=dim)
            else:
                anchor_vec = raw_vec.copy()
                
            if row["active_embedding"] is not None:
                active_vec = np.frombuffer(row["active_embedding"], dtype=np.float32, count=dim)
            else:
                active_vec = raw_vec.copy()

            embeddings.append(
                {
                    "id": int(row["id"]),
                    "student_id": int(row["student_id"]),
                    "student_name": row["student_name"],
                    "embedding": active_vec,              # Backward compatibility
                    "ltm_anchor": anchor_vec,             # LTM
                    "stm_prototype": active_vec,          # STM
                    "image_path": row["image_path"],
                    "model_name": row["model_name"],
                    "quality_score": row["quality_score"],
                    "adaptation_count": int(row["adaptation_count"] or 0),
                    "last_drift": float(row["last_drift"] or 0.0),
                    "rollback_count": int(row["rollback_count"] or 0),
                }
            )
        return embeddings

    def list_students(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT students.*, COUNT(face_embeddings.id) AS embedding_count
                FROM students
                LEFT JOIN face_embeddings ON face_embeddings.student_id = students.id
                GROUP BY students.id
                ORDER BY students.name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_attendance(self, student_id, student_name, confidence, camera_id=None, status="Present"):
        timestamp = datetime.now()
        date_text = timestamp.strftime("%Y-%m-%d")
        time_text = timestamp.strftime("%H:%M:%S")
        created_at = timestamp.isoformat(timespec="seconds")

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO attendance
                    (student_id, student_name, date, time, status, confidence, camera_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (student_id, student_name, date_text, time_text, status, confidence, camera_id, created_at),
            )
            return cursor.rowcount == 1

    def list_attendance(self, date=None, limit=200):
        params = []
        where_clause = ""
        if date:
            where_clause = "WHERE date = ?"
            params.append(date)

        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, student_id, student_name, date, time, status, confidence, camera_id, created_at
                FROM attendance
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def add_alert(self, alert_type, message, image_path=None):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alerts (alert_type, message, image_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (alert_type, message, image_path, datetime.now().isoformat(timespec="seconds")),
            )

    def list_alerts(self, limit=100):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, alert_type, message, image_path, created_at
                FROM alerts
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_total_embeddings(self):
        """Get total count of face embeddings."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM face_embeddings").fetchone()
            return int(row["count"]) if row else 0

    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT student_name, time, confidence FROM attendance 
                   WHERE date = ? ORDER BY time DESC""",
                (date,)
            ).fetchall()
        return [tuple(row) for row in rows]

    def export_snapshot(self):
        return json.dumps(
            {
                "students": self.list_students(),
                "attendance": self.list_attendance(limit=500),
                "alerts": self.list_alerts(limit=100),
                "adaptation_audit": self.list_adaptation_logs(limit=100),
            },
            indent=2,
        )
