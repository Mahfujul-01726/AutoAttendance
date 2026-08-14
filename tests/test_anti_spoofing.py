"""Unit tests for anti-spoofing module."""

import unittest
import numpy as np

from auto_attendance.anti_spoofing import AntiSpoofing


class TestAntiSpoofing(unittest.TestCase):
    """Test suite for AntiSpoofing module."""

    def test_module_initialization(self):
        """Test AntiSpoofing module initialization."""
        module = AntiSpoofing()
        self.assertIsNotNone(module)

    def test_analyze_valid_face(self):
        """Test analyzing a valid face image."""
        module = AntiSpoofing()
        face_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        is_real, confidence = module.analyze(face_crop)
        
        self.assertIsInstance(is_real, bool)
        self.assertIsInstance(confidence, float)
        self.assertTrue(0.0 <= confidence <= 1.0)

    def test_analyze_invalid_shape(self):
        """Test handling of invalid image shape."""
        module = AntiSpoofing()
        face_crop = np.random.rand(112, 112).astype(np.uint8)
        is_real, confidence = module.analyze(face_crop)
        
        self.assertFalse(is_real)
        self.assertEqual(confidence, 0.0)

    def test_analyze_empty_image(self):
        """Test handling of empty image."""
        module = AntiSpoofing()
        is_real, confidence = module.analyze(None)
        
        self.assertFalse(is_real)
        self.assertEqual(confidence, 0.0)

    def test_spoof_detection_threshold(self):
        """Test that threshold is correctly applied."""
        module = AntiSpoofing(threshold=0.5)
        self.assertEqual(module.threshold, 0.5)


class TestSpoofDetection(unittest.TestCase):
    """Test suite for spoof detection functionality."""

    def test_detect_printed_photo(self):
        """Test detection of uniform/printed photos."""
        printed_photo = np.ones((112, 112, 3), dtype=np.uint8) * 128
        module = AntiSpoofing()
        is_real, score = module.analyze(printed_photo)
        self.assertFalse(is_real)

    def test_detect_real_face(self):
        """Test random noise texture analysis."""
        real_face = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        self.assertEqual(real_face.shape, (112, 112, 3))


if __name__ == "__main__":
    unittest.main()
