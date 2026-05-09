import json
import os
import sqlite3
from datetime import datetime

import numpy as np

from config import DATABASE_PATH, MODELS_DIR


class AttendanceDatabase:
    """SQLite storage for students, face embeddings, attendance, and alerts."""

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or MODELS_DIR, exist_ok=True)
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

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
                    embedding_dim INTEGER NOT NULL,
                    image_path TEXT,
                    model_name TEXT NOT NULL,
                    quality_score REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
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
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO face_embeddings
                    (student_id, embedding, embedding_dim, image_path, model_name, quality_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    embedding_array.tobytes(),
                    int(embedding_array.shape[0]),
                    image_path,
                    model_name,
                    quality_score,
                    now,
                ),
            )

    def load_embeddings(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    face_embeddings.id,
                    face_embeddings.student_id,
                    face_embeddings.embedding,
                    face_embeddings.embedding_dim,
                    face_embeddings.image_path,
                    face_embeddings.model_name,
                    face_embeddings.quality_score,
                    students.name AS student_name
                FROM face_embeddings
                JOIN students ON students.id = face_embeddings.student_id
                WHERE students.status = 'active'
                """
            ).fetchall()

        embeddings = []
        for row in rows:
            vector = np.frombuffer(row["embedding"], dtype=np.float32, count=row["embedding_dim"])
            embeddings.append(
                {
                    "id": int(row["id"]),
                    "student_id": int(row["student_id"]),
                    "student_name": row["student_name"],
                    "embedding": vector,
                    "image_path": row["image_path"],
                    "model_name": row["model_name"],
                    "quality_score": row["quality_score"],
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
            },
            indent=2,
        )
