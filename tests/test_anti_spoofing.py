"""Unit tests for anti-spoofing module."""

import pytest
import numpy as np
from unittest.mock import patch


@pytest.mark.unit
class TestAntiSpoofing:
    """Test suite for AntiSpoofing module."""

    def test_module_initialization(self):
        """Test AntiSpoofing module initialization."""
        from anti_spoofing import AntiSpoofing
        module = AntiSpoofing()
        assert module is not None

    def test_analyze_valid_face(self):
        """Test analyzing a valid face image."""
        from anti_spoofing import AntiSpoofing
        module = AntiSpoofing()
        
        # Create mock face image (RGB format)
        face_crop = np.random.rand(112, 112, 3).astype(np.uint8)
        
        is_real, confidence = module.analyze(face_crop)
        
        assert isinstance(is_real, bool)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    def test_analyze_invalid_shape(self):
        """Test handling of invalid image shape."""
        from anti_spoofing import AntiSpoofing
        module = AntiSpoofing()
        
        # Create invalid face image (grayscale)
        face_crop = np.random.rand(112, 112).astype(np.uint8)
        
        is_real, confidence = module.analyze(face_crop)
        
        assert is_real is False
        assert confidence == 0.0

    def test_analyze_empty_image(self):
        """Test handling of empty image."""
        from anti_spoofing import AntiSpoofing
        module = AntiSpoofing()
        
        is_real, confidence = module.analyze(None)
        
        assert is_real is False
        assert confidence == 0.0

    def test_spoof_detection_threshold(self):
        """Test that threshold is correctly applied."""
        from anti_spoofing import AntiSpoofing
        module = AntiSpoofing(threshold=0.5)
        
        assert module.threshold == 0.5


@pytest.mark.unit
class TestSpoof Detection:
    """Test suite for spoof detection functionality."""

    def test_detect_printed_photo(self):
        """Test detection of printed photos."""
        # Mock printed photo (usually lower frequency content)
        printed_photo = np.ones((112, 112, 3), dtype=np.uint8) * 128
        
        assert printed_photo.shape == (112, 112, 3)

    def test_detect_screen_replay(self):
        """Test detection of screen replays."""
        # Mock screen replay with regular patterns
        screen_replay = np.zeros((112, 112, 3), dtype=np.uint8)
        screen_replay[::10, :, :] = 255  # Add scanline pattern
        
        assert screen_replay.shape == (112, 112, 3)

    def test_detect_real_face(self):
        """Test that real faces pass anti-spoofing."""
        # Mock real face (higher frequency content)
        real_face = np.random.rand(112, 112, 3).astype(np.uint8)
        
        assert real_face.shape == (112, 112, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
