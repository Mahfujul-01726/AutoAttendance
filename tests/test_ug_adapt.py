"""Unit tests for UG-Adapt QualityGate and DualMemoryTemplateAdapter modules."""

import unittest
import numpy as np

from auto_attendance.quality_gate import QualityGate
from auto_attendance.template_adapter import DualMemoryTemplateAdapter


class TestUGAdaptModules(unittest.TestCase):
    """Test suite for UG-Adapt Research Components."""

    def setUp(self):
        self.gate = QualityGate(quality_threshold=0.65, liveness_threshold=0.70, temporal_window=3)
        self.adapter = DualMemoryTemplateAdapter(alpha_base=0.90, drift_threshold=0.35, dual_lambda=0.60)

    def test_sharpness_calculation(self):
        """Test Laplacian sharpness score computation."""
        sharp_img = np.zeros((100, 100, 3), dtype=np.uint8)
        sharp_img[::2, ::2] = 255
        score_sharp = self.gate.calculate_sharpness(sharp_img)
        self.assertGreater(score_sharp, 0.5)

        solid_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        score_solid = self.gate.calculate_sharpness(solid_img)
        self.assertEqual(score_solid, 0.0)

    def test_illumination_calculation(self):
        """Test illumination score computation."""
        mid_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        score_mid = self.gate.calculate_illumination(mid_img)
        self.assertEqual(score_mid, 1.0)

        dark_img = np.zeros((100, 100, 3), dtype=np.uint8)
        score_dark = self.gate.calculate_illumination(dark_img)
        self.assertEqual(score_dark, 0.0)

    def test_dynamic_alpha(self):
        """Test dynamic learning rate scaling with uncertainty."""
        alpha_high = self.adapter.compute_dynamic_alpha(quality_score=1.0, liveness_score=1.0)
        self.assertAlmostEqual(alpha_high, 0.90, places=3)

        alpha_low = self.adapter.compute_dynamic_alpha(quality_score=0.0, liveness_score=1.0)
        self.assertAlmostEqual(alpha_low, 1.00, places=3)

    def test_bayesian_vmf_update(self):
        """Test Riemannian Bayesian von Mises-Fisher directional update."""
        dim = 512
        prior_mean = np.random.randn(dim).astype(np.float32)
        prior_mean = prior_mean / np.linalg.norm(prior_mean)
        
        live_emb = np.random.randn(dim).astype(np.float32)
        live_emb = live_emb / np.linalg.norm(live_emb)

        post_mean, post_kappa = self.adapter.bayesian_vmf_update(
            prior_mean=prior_mean,
            prior_kappa=50.0,
            live_embedding=live_emb,
            quality_score=0.90,
            liveness_score=0.95
        )
        self.assertAlmostEqual(float(np.linalg.norm(post_mean)), 1.0, places=4)
        self.assertGreater(post_kappa, 0.0)

    def test_dual_memory_joint_scoring(self):
        """Test joint matching score calculation."""
        dim = 512
        vec1 = np.random.randn(dim).astype(np.float32)
        vec1 = vec1 / np.linalg.norm(vec1)

        score, ltm_s, stm_s = self.adapter.compute_joint_similarity(vec1, vec1, vec1)
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_drift_distance_calculation(self):
        """Test cosine/geodesic drift distance."""
        dim = 512
        ltm = np.random.randn(dim).astype(np.float32)
        ltm = ltm / np.linalg.norm(ltm)

        # Distance to self must be 0
        d_self = self.adapter.calculate_drift_distance(ltm, ltm)
        self.assertAlmostEqual(d_self, 0.0, places=5)

        # Orthogonal vector distance must be 1.0
        orth = np.random.randn(dim).astype(np.float32)
        orth = orth - np.dot(orth, ltm) * ltm
        orth = orth / np.linalg.norm(orth)
        d_orth = self.adapter.calculate_drift_distance(orth, ltm)
        self.assertAlmostEqual(d_orth, 1.0, places=4)

    def test_drift_guard_and_safe_adaptation(self):
        """Test safe adaptation within drift threshold."""
        dim = 512
        ltm = np.random.randn(dim).astype(np.float32)
        ltm = ltm / np.linalg.norm(ltm)

        small_noise = np.random.randn(dim).astype(np.float32) * 0.05
        live = ltm + small_noise
        live = live / np.linalg.norm(live)

        new_stm, status, metrics = self.adapter.adapt(
            live_embedding=live,
            ltm_anchor=ltm,
            current_stm=ltm,
            quality_score=0.90,
            liveness_score=0.95
        )

        self.assertEqual(status, "UPDATED")
        self.assertLessEqual(metrics["drift_distance"], 0.35)

    def test_drift_guard_and_auto_rollback(self):
        """Test Auto-Rollback trigger when drift threshold is breached."""
        dim = 512
        ltm = np.random.randn(dim).astype(np.float32)
        ltm = ltm / np.linalg.norm(ltm)

        # Set up a severely drifted current STM (orthogonal to LTM anchor)
        orth = np.random.randn(dim).astype(np.float32)
        orth = orth - np.dot(orth, ltm) * ltm
        orth = orth / np.linalg.norm(orth)

        # Candidate generated from already drifted STM and orthogonal live frame
        new_stm, status, metrics = self.adapter.adapt(
            live_embedding=orth,
            ltm_anchor=ltm,
            current_stm=orth,
            quality_score=0.95,
            liveness_score=0.95
        )

        self.assertEqual(status, "ROLLBACK")
        self.assertEqual(metrics.get("rollback_triggered"), 1.0)
        # Verify rollback reverted to pristine anchor
        cosine_to_ltm = float(np.dot(new_stm, ltm))
        self.assertAlmostEqual(cosine_to_ltm, 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
