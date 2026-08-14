"""Unit tests for Ultimate Frontiers: Adversarial Patch Defense and Sliced-Wasserstein Domain Alignment."""

import unittest
import numpy as np

from auto_attendance.adversarial_patch_filter import AdversarialPatchDefenseFilter
from auto_attendance.optimal_transport_aligner import CrossCameraOptimalTransportAligner


class TestUltimateFrontiers(unittest.TestCase):
    """Test suite for Adversarial Patch Defense and Optimal Transport Domain Alignment."""

    def setUp(self):
        self.patch_defense = AdversarialPatchDefenseFilter()
        self.ot_aligner = CrossCameraOptimalTransportAligner(embedding_dim=512, num_projections=30)

    def test_adversarial_patch_detection_clean_image(self):
        """Test that natural clean face image does not trigger false positive adversarial alarm."""
        clean_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        is_adv, ratio, metrics = self.patch_defense.detect_adversarial_gradients(clean_crop)

        self.assertFalse(is_adv)
        self.assertIn("energy_ratio", metrics)

    def test_adversarial_patch_sanitization(self):
        """Test Total Variation sanitization filter retains valid shape and uint8 range."""
        test_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        sanitized = self.patch_defense.sanitize_adversarial_crop(test_crop)

        self.assertEqual(sanitized.shape, test_crop.shape)
        self.assertEqual(sanitized.dtype, np.uint8)

    def test_sliced_wasserstein_distance(self):
        """Test Sliced-Wasserstein distance computation between two distributions."""
        dim = 512
        src = np.random.randn(20, dim).astype(np.float32)
        src = src / np.linalg.norm(src, axis=1, keepdims=True)

        tgt = np.random.randn(20, dim).astype(np.float32)
        tgt = tgt / np.linalg.norm(tgt, axis=1, keepdims=True)

        swd = self.ot_aligner.compute_sliced_wasserstein_distance(src, tgt)
        self.assertIsInstance(swd, float)
        self.assertGreater(swd, 0.0)

    def test_cross_camera_calibration_and_alignment(self):
        """Test Procrustes domain rotation calibration and query alignment."""
        dim = 512
        ref = np.random.randn(20, dim).astype(np.float32)
        ref = ref / np.linalg.norm(ref, axis=1, keepdims=True)

        # Generate camera domain with known slight rotation
        cam = ref + np.random.randn(20, dim).astype(np.float32) * 0.05
        cam = cam / np.linalg.norm(cam, axis=1, keepdims=True)

        r_matrix = self.ot_aligner.calibrate_camera_domain("gate_cam_1", cam, ref)
        self.assertEqual(r_matrix.shape, (512, 512))

        # Test query alignment
        query = cam[0]
        aligned_query = self.ot_aligner.align_query_to_reference(query, "gate_cam_1")
        self.assertEqual(aligned_query.shape, (512,))
        self.assertAlmostEqual(float(np.linalg.norm(aligned_query)), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
