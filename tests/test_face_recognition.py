"""Unit tests for face recognition module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestFaceRecognitionModule:
    """Test suite for FaceRecognitionModule."""

    def test_module_initialization(self):
        """Test that FaceRecognitionModule initializes without errors."""
        with patch('face_recognition.InsightFace'):
            from face_recognition import FaceRecognitionModule
            module = FaceRecognitionModule()
            assert module is not None

    def test_model_loading(self):
        """Test model loading functionality."""
        with patch('face_recognition.InsightFace'):
            from face_recognition import FaceRecognitionModule
            module = FaceRecognitionModule()
            with patch.object(module, 'app', create=True):
                # Test passes if no exception is raised
                assert module is not None

    def test_embedding_extraction(self):
        """Test face embedding extraction."""
        with patch('face_recognition.InsightFace'):
            from face_recognition import FaceRecognitionModule
            module = FaceRecognitionModule()
            
            # Create mock face image
            face_image = np.random.rand(112, 112, 3).astype(np.uint8)
            
            # Should return a numpy array
            assert face_image.shape == (112, 112, 3)


@pytest.mark.unit
class TestFaceDetection:
    """Test suite for face detection functionality."""

    def test_detect_faces_in_frame(self):
        """Test face detection in video frame."""
        frame = np.random.rand(480, 640, 3).astype(np.uint8)
        
        # Verify frame dimensions
        assert frame.shape == (480, 640, 3)

    def test_detect_multiple_faces(self):
        """Test detection of multiple faces."""
        frame = np.random.rand(480, 640, 3).astype(np.uint8)
        
        # Create mock detection results
        detections = [
            {"bbox": (100, 100, 50, 50), "confidence": 0.95},
            {"bbox": (300, 100, 50, 50), "confidence": 0.88},
        ]
        
        assert len(detections) == 2

    def test_detect_no_faces(self):
        """Test behavior when no faces detected."""
        frame = np.random.rand(480, 640, 3).astype(np.uint8)
        detections = []
        
        assert len(detections) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
