"""Unit tests for Frontier Novelties: rPPG Blood-Pulse Liveness and Hyperspherical Differential Privacy."""

import unittest
import numpy as np

from auto_attendance.rppg_pulse_guard import RemotePulseLivenessGuard
from auto_attendance.differential_privacy import HypersphericalDifferentialPrivacyEngine


class TestFrontierNovelties(unittest.TestCase):
    """Test suite for Frontier Research Engines."""

    def setUp(self):
        self.rppg = RemotePulseLivenessGuard(buffer_length=30, fps=30.0)
        self.dp = HypersphericalDifferentialPrivacyEngine(epsilon=1.5, delta=1e-5)

    def test_rppg_chrom_pulse_generation(self):
        """Test CHROM pulse extraction from synthetic temporal RGB series."""
        # Generate 30 frames of synthetic RGB signal with a 1.2 Hz pulse (72 BPM)
        t = np.linspace(0, 1.0, 30, dtype=np.float32)
        r = 150.0 + 2.0 * np.sin(2 * np.pi * 1.2 * t)
        g = 130.0 + 4.0 * np.sin(2 * np.pi * 1.2 * t)  # Stronger green absorption
        b = 110.0 + 1.0 * np.sin(2 * np.pi * 1.2 * t)
        rgb_series = np.column_stack([r, g, b])

        pulse = self.rppg.compute_chrom_pulse(rgb_series)
        self.assertEqual(len(pulse), 30)
        self.assertGreater(float(np.std(pulse)), 0.0)

    def test_rppg_cardiac_liveness_evaluation(self):
        """Test full rPPG cardiac liveness evaluation."""
        face = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        is_live, conf, metrics = self.rppg.evaluate_cardiac_liveness(face, subject_key="test_sub")

        self.assertIsInstance(is_live, bool)
        self.assertIsInstance(conf, float)
        self.assertIn("bpm", metrics)
        self.assertIn("cardiac_snr", metrics)

    def test_differential_privacy_properties(self):
        """Test (epsilon, delta)-DP perturbation on unit hypersphere."""
        dim = 512
        v = np.random.randn(dim).astype(np.float32)
        v = v / np.linalg.norm(v)

        privatized, dp_metrics = self.dp.privatize_embedding(v, seed=42)

        self.assertEqual(privatized.shape, (512,))
        # Must retain unit hypersphere norm
        self.assertAlmostEqual(float(np.linalg.norm(privatized)), 1.0, places=4)
        # Cosine fidelity should remain high (> 0.85) under epsilon=1.5
        self.assertGreater(dp_metrics["retention_fidelity"], 0.85)
        self.assertEqual(dp_metrics["epsilon"], 1.5)


if __name__ == "__main__":
    unittest.main()
