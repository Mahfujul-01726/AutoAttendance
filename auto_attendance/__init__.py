"""
AutoAttendance - Face Recognition Attendance System & UG-Adapt Framework
A professional real-time attendance tracking and continual biometrics research solution.
"""

__version__ = "2.5.0"
__author__ = "AutoAttendance Team"
__description__ = "Real-time face recognition attendance system with UG-Adapt continual learning, cancelable biometrics, rPPG, and demographic fairness"

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
    UG_ADAPT_ENABLED,
)
from .database import AttendanceDatabase
from .face_recognition import FaceRecognitionModule
from .attendance_manager import AttendanceManager
from .anti_spoofing import AntiSpoofing
from .quality_gate import QualityGate
from .template_adapter import DualMemoryTemplateAdapter
from .cancelable_biometrics import CancelableBiometricsEngine
from .photometric_harmonization import AdaptiveRetinexHarmonizer
from .occlusion_gating import OcclusionAwareSubEmbeddingGater
from .homography_flow_guard import PlanarHomographyFlowGuard
from .explainable_ai import ExplainableSaliencyAttributor
from .rppg_pulse_guard import RemotePulseLivenessGuard
from .differential_privacy import HypersphericalDifferentialPrivacyEngine
from .adversarial_patch_filter import AdversarialPatchDefenseFilter
from .optimal_transport_aligner import CrossCameraOptimalTransportAligner
from .fairness_calibrator import DemographicFairnessCalibrator

# Backward compatibility alias
AntiSpoofingModule = AntiSpoofing

__all__ = [
    "AttendanceDatabase",
    "AttendanceManager",
    "AntiSpoofing",
    "AntiSpoofingModule",
    "FaceRecognitionModule",
    "QualityGate",
    "DualMemoryTemplateAdapter",
    "CancelableBiometricsEngine",
    "AdaptiveRetinexHarmonizer",
    "OcclusionAwareSubEmbeddingGater",
    "PlanarHomographyFlowGuard",
    "ExplainableSaliencyAttributor",
    "RemotePulseLivenessGuard",
    "HypersphericalDifferentialPrivacyEngine",
    "AdversarialPatchDefenseFilter",
    "CrossCameraOptimalTransportAligner",
    "DemographicFairnessCalibrator",
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
    "UG_ADAPT_ENABLED",
]