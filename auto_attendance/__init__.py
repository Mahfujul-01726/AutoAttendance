"""
AutoAttendance - Face Recognition Attendance System
A professional real-time attendance tracking solution.
"""

__version__ = "1.0.0"
__author__ = "AutoAttendance Team"
__description__ = "Real-time face recognition attendance system with anti-spoofing"

from .config import (
    CAMERA_ID,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    FPS,
    FRAME_PROCESS_INTERVAL,
    RECOGNITION_THRESHOLD,
    SPOOF_THRESHOLD,
    DATABASE_PATH,
    FACE_DATA_DIR,
    ATTENDANCE_DIR,
    MODELS_DIR,
)
from .database import AttendanceDatabase
from .face_recognition import FaceRecognitionModule
from .attendance_manager import AttendanceManager
from .anti_spoofing import AntiSpoofingModule

__all__ = [
    "AttendanceDatabase",
    "AttendanceManager",
    "AntiSpoofingModule",
    "FaceRecognitionModule",
    "CAMERA_ID",
    "FRAME_WIDTH",
    "FRAME_HEIGHT",
    "FPS",
    "FRAME_PROCESS_INTERVAL",
    "RECOGNITION_THRESHOLD",
    "SPOOF_THRESHOLD",
    "DATABASE_PATH",
    "FACE_DATA_DIR",
    "ATTENDANCE_DIR",
    "MODELS_DIR",
]