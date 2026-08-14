"""
AutoAttendance Configuration
Centralized settings for the face recognition attendance system and UG-Adapt framework.
Supports environment variable overrides via .env file.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Set timezone globally for Hugging Face Spaces (which default to UTC)
TIMEZONE = os.getenv("TIMEZONE", "Asia/Dhaka")
os.environ['TZ'] = TIMEZONE
if hasattr(time, 'tzset'):
    time.tzset()

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable with fallback."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Get float from environment variable with fallback."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


# =============================================================================
# PROJECT PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
FACE_DATA_DIR = DATA_DIR / "faces"
TRAINING_DATA_DIR = DATA_DIR / "training"
ATTENDANCE_DIR = DATA_DIR / "attendance"
MODELS_DIR = BASE_DIR / "models"
UNKNOWN_FACES_DIR = DATA_DIR / "unknown_faces"
LOGS_DIR = BASE_DIR / "logs"

# Create required directories
for directory in [DATA_DIR, FACE_DATA_DIR, TRAINING_DATA_DIR, ATTENDANCE_DIR, MODELS_DIR, UNKNOWN_FACES_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CAMERA SETTINGS
# =============================================================================
CAMERA_ID = get_env_int("CAMERA_ID", 0)
FRAME_WIDTH = get_env_int("FRAME_WIDTH", 640)
FRAME_HEIGHT = get_env_int("FRAME_HEIGHT", 480)
FPS = get_env_int("FPS", 30)

# Frame processing interval - process every N frames for performance
FRAME_PROCESS_INTERVAL = get_env_int("FRAME_PROCESS_INTERVAL", 5)

# =============================================================================
# INSIGHTFACE SETTINGS
# =============================================================================
# Face detection and recognition model
INSIGHTFACE_MODEL_NAME = os.getenv("INSIGHTFACE_MODEL_NAME", "buffalo_l")
INSIGHTFACE_DET_SIZE = (320, 320)
INSIGHTFACE_PROVIDERS = ["CPUExecutionProvider"]  # CPU for compatibility
INSIGHTFACE_MAX_FACES = get_env_int("INSIGHTFACE_MAX_FACES", 1)

# =============================================================================
# RECOGNITION SETTINGS (Cosine Distance)
# =============================================================================
RECOGNITION_THRESHOLD = get_env_float("RECOGNITION_THRESHOLD", 0.45)
CONFIDENCE_THRESHOLD = RECOGNITION_THRESHOLD

# =============================================================================
# ANTI-SPOOFING SETTINGS
# =============================================================================
# Difference of Gaussians parameters
DOG_SIGMA1 = get_env_float("DOG_SIGMA1", 0.5)
DOG_SIGMA2 = get_env_float("DOG_SIGMA2", 1.0)

# Spoof threshold - higher = more lenient, lower = stricter
SPOOF_THRESHOLD = get_env_float("SPOOF_THRESHOLD", 0.35)

# =============================================================================
# UG-ADAPT RESEARCH SETTINGS (Continual Learning & Dual-Memory)
# =============================================================================
UG_ADAPT_ENABLED = get_env_bool("UG_ADAPT_ENABLED", True)
UG_ALPHA_BASE = get_env_float("UG_ALPHA_BASE", 0.90)
UG_DRIFT_THRESHOLD = get_env_float("UG_DRIFT_THRESHOLD", 0.35)
UG_QUALITY_THRESHOLD = get_env_float("UG_QUALITY_THRESHOLD", 0.65)
UG_LIVENESS_THRESHOLD = get_env_float("UG_LIVENESS_THRESHOLD", 0.70)
UG_TEMPORAL_WINDOW = get_env_int("UG_TEMPORAL_WINDOW", 5)
UG_DUAL_MEMORY_LAMBDA = get_env_float("UG_DUAL_MEMORY_LAMBDA", 0.60)

# =============================================================================
# DATABASE SETTINGS
# =============================================================================
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(MODELS_DIR / "attendance.sqlite3")))
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# =============================================================================
# EMAIL SETTINGS (Gmail with App Password)
# =============================================================================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = get_env_int("SMTP_PORT", 587)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", EMAIL_ADDRESS)

# =============================================================================
# LOGGING & OUTPUT SETTINGS
# =============================================================================
LOG_FILE = ATTENDANCE_DIR / "attendance.log"
EXCEL_FILE = ATTENDANCE_DIR / "attendance.xlsx"
ALERT_SOUND = BASE_DIR / "alert.wav"

# =============================================================================
# APPLICATION METADATA
# =============================================================================
APP_NAME = "AutoAttendance"
APP_VERSION = "2.0.0"
DEBUG = get_env_bool("DEBUG", False)

# =============================================================================
# EXPORT SETTINGS
# =============================================================================
EXPORT_CSV = True
EXPORT_EXCEL = True
EXPORT_INCLUDE_TIMESTAMP = True

# =============================================================================
# LEGACY SETTINGS (Maintained for backward compatibility)
# =============================================================================
RECOGNITION_MODEL_PATH = MODELS_DIR / "face_recognizer.yml"
TRAINING_DATA_PATH = TRAINING_DATA_DIR


def validate_config() -> list:
    """Validate configuration and return list of warnings."""
    issues = []
    
    if not EMAIL_ADDRESS:
        issues.append("EMAIL_ADDRESS not configured (email notifications disabled)")
    
    if not EMAIL_PASSWORD and EMAIL_ADDRESS:
        issues.append("EMAIL_PASSWORD not configured (email notifications disabled)")
    
    if not DATABASE_PATH.parent.exists():
        issues.append(f"Database directory does not exist: {DATABASE_PATH.parent}")
    
    if CAMERA_ID < 0:
        issues.append(f"Invalid CAMERA_ID: {CAMERA_ID}")
    
    if FRAME_WIDTH < 100 or FRAME_HEIGHT < 100:
        issues.append(f"Invalid frame size: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    
    return issues
