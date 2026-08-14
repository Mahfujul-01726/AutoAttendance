"""Unit tests for Next-Gen Novelties: Occlusion Gating, Homography Flow Guard, and Explainable AI."""

import unittest
import numpy as np

from auto_attendance.occlusion_gating import OcclusionAwareSubEmbeddingGater
from auto_attendance.homography_flow_guard import PlanarHomographyFlowGuard
from auto_attendance.explainable_ai import ExplainableSaliencyAttributor


class TestNextGenNovelties(unittest.TestCase):
    """Test suite for Next-Gen Research Engines."""

    def setUp(self):
        self.occlusion_gater = OcclusionAwareSubEmbeddingGater()
        self.flow_guard = PlanarHomographyFlowGuard()
        self.xai = ExplainableSaliencyAttributor()

    def test_occlusion_visibility_unmasked(self):
        """Test spatial visibility evaluation on an unmasked face."""
        # Random normal face texture
        clean_face = (np.random.rand(120, 120, 3) * 255).astype(np.uint8)
        weights, metrics = self.occlusion_gater.evaluate_spatial_visibility(clean_face)

        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(float(np.sum(weights)), 1.0, places=4)
        self.assertIn("upper_visibility", metrics)
        self.assertIn("lower_visibility", metrics)

    def test_occlusion_visibility_masked(self):
        """Test detection of surgical mask (solid uniform lower zone)."""
        masked_face = (np.random.rand(120, 120, 3) * 255).astype(np.uint8)
        # Paint lower 35% with uniform blue surgical mask color
        masked_face[80:, :, :] = [210, 150, 50]  # BGR uniform blue

        weights, metrics = self.occlusion_gater.evaluate_spatial_visibility(masked_face)
        self.assertEqual(metrics["mask_detected"], 1.0)
        self.assertLess(metrics["lower_visibility"], metrics["upper_visibility"])

    def test_homography_flow_guard_planar_screen(self):
        """Test detection of 2D flat screen movement (near zero homography residue)."""
        # Generate 5 landmark points
        pts1 = np.array([[30, 40], [70, 40], [50, 60], [35, 80], [65, 80]], dtype=np.float32)
        # Apply exact 2D affine shift (flat screen panning)
        shift = np.array([2.0, 1.5], dtype=np.float32)
        pts2 = pts1 + shift
        pts3 = pts2 + shift

        self.flow_guard.evaluate_depth_curvature(pts1, subject_key="screen_attack")
        self.flow_guard.evaluate_depth_curvature(pts2, subject_key="screen_attack")
        is_3d, residue, metrics = self.flow_guard.evaluate_depth_curvature(pts3, subject_key="screen_attack")

        # Flat screen transformation has near-zero homography residue
        self.assertLess(residue, 1.2)
        self.assertEqual(metrics["is_flat_screen"], 1.0)

    def test_explainable_ai_saliency_heatmap(self):
        """Test computation of Jet attention heatmap and attribution metrics."""
        face = (np.random.rand(112, 112, 3) * 255).astype(np.uint8)
        blended, att_metrics = self.xai.compute_saliency_heatmap(face, confidence_score=0.92)

        self.assertEqual(blended.shape, face.shape)
        self.assertEqual(blended.dtype, np.uint8)
        self.assertIn("upper_zone_pct", att_metrics)
        self.assertIn("mid_zone_pct", att_metrics)
        self.assertIn("lower_zone_pct", att_metrics)
        # Percentages should sum to ~100%
        total_pct = att_metrics["upper_zone_pct"] + att_metrics["mid_zone_pct"] + att_metrics["lower_zone_pct"]
        self.assertTrue(98.0 <= total_pct <= 102.0)


if __name__ == "__main__":
    unittest.main()
