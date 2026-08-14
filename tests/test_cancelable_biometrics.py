"""Unit tests for Cancelable Biometrics and Photometric Harmonization modules."""

import unittest
import numpy as np

from auto_attendance.cancelable_biometrics import CancelableBiometricsEngine
from auto_attendance.photometric_harmonization import AdaptiveRetinexHarmonizer


class TestCancelableBiometrics(unittest.TestCase):
    """Test suite for Cryptographic Cancelable Biometrics (ISO/IEC 24745)."""

    def setUp(self):
        self.engine = CancelableBiometricsEngine(embedding_dim=512)

    def test_orthonormal_matrix_properties(self):
        """Test that generated matrix is strictly orthonormal (W^T * W = I)."""
        w = self.engine.generate_orthonormal_matrix("student_123")
        self.assertEqual(w.shape, (512, 512))

        # W^T * W should equal Identity matrix
        identity_approx = np.dot(w.T, w)
        identity_expected = np.eye(512, dtype=np.float32)
        np.testing.assert_allclose(identity_approx, identity_expected, atol=1e-5)

    def test_isometric_invariance(self):
        """Test that cosine similarity between two faces is identical in protected domain."""
        v1 = np.random.randn(512).astype(np.float32)
        v1 = v1 / np.linalg.norm(v1)

        v2 = np.random.randn(512).astype(np.float32)
        v2 = v2 / np.linalg.norm(v2)

        original_sim = float(np.dot(v1, v2))

        seed = "secure_user_key_42"
        p1 = self.engine.protect_embedding(v1, seed)
        p2 = self.engine.protect_embedding(v2, seed)

        protected_sim = float(np.dot(p1, p2))
        self.assertAlmostEqual(original_sim, protected_sim, places=4)

    def test_unlinkability(self):
        """Test that two different seeds produce uncorrelated protected templates from the same face."""
        v = np.random.randn(512).astype(np.float32)
        v = v / np.linalg.norm(v)

        p_seed_a = self.engine.protect_embedding(v, "key_classroom_A")
        p_seed_b = self.engine.protect_embedding(v, "key_classroom_B")

        # Cross-correlation between different domain keys should be near zero (orthogonal)
        cross_sim = float(np.dot(p_seed_a, p_seed_b))
        self.assertLess(abs(cross_sim), 0.15)


class TestPhotometricHarmonization(unittest.TestCase):
    """Test suite for Adaptive Retinex Photometric Harmonization."""

    def setUp(self):
        self.harmonizer = AdaptiveRetinexHarmonizer()

    def test_harmonize_dimensions_and_validity(self):
        """Test that harmonized image retains original shape and valid uint8 range."""
        test_crop = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        enhanced = self.harmonizer.harmonize(test_crop)

        self.assertEqual(enhanced.shape, test_crop.shape)
        self.assertEqual(enhanced.dtype, np.uint8)
        self.assertTrue(np.all(enhanced >= 0) and np.all(enhanced <= 255))

    def test_harmonize_shadowed_face(self):
        """Test dynamic range enhancement on shadowed/under-exposed face image."""
        # Create half-dark, half-bright image
        shadow_crop = np.zeros((100, 100, 3), dtype=np.uint8)
        shadow_crop[:, :50, :] = 30   # Dark shadow
        shadow_crop[:, 50:, :] = 220  # Bright sun

        enhanced = self.harmonizer.harmonize(shadow_crop)
        # Shadow region should have boosted mean luminance
        dark_region_mean = np.mean(enhanced[:, :50, :])
        self.assertGreater(dark_region_mean, 30.0)


if __name__ == "__main__":
    unittest.main()
