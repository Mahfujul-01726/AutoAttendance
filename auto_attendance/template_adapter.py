"""
Dual-Memory Template Adapter Module for UG-Adapt
Implements Uncertainty-Gated Dynamic EMA, Geodesic Drift Guard, and Auto-Rollback.
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np

from .config import (
    UG_ALPHA_BASE,
    UG_DRIFT_THRESHOLD,
    UG_DUAL_MEMORY_LAMBDA,
)

logger = logging.getLogger(__name__)


class DualMemoryTemplateAdapter:
    """
    Dual-Memory Continual Biometric Adaptation Engine.
    
    Features:
    - Dynamic Uncertainty-Aware Rate: alpha(t) = f(Q_face, S_live)
    - Decoupled Long-Term Memory (LTM Anchor) vs Short-Term Memory (STM Prototype)
    - Hyperspherical Geodesic Drift Guard (D_drift <= delta_max)
    - Zero-Poisoning Auto-Rollback mechanism
    """

    def __init__(
        self,
        alpha_base: float = UG_ALPHA_BASE,
        drift_threshold: float = UG_DRIFT_THRESHOLD,
        dual_lambda: float = UG_DUAL_MEMORY_LAMBDA,
    ):
        self.alpha_base = alpha_base
        self.drift_threshold = drift_threshold
        self.dual_lambda = dual_lambda

    def compute_dynamic_alpha(
        self,
        quality_score: float,
        liveness_score: float,
        gamma: float = 1.0
    ) -> float:
        """
        Compute dynamic learning weight alpha(t) in [alpha_base, 1.0].
        
        High certainty -> alpha -> alpha_base (~0.90) -> higher adaptation.
        Low certainty  -> alpha -> 1.00 -> zero/negligible adaptation.
        """
        certainty = max(0.0, min(1.0, float(quality_score * liveness_score)))
        alpha = self.alpha_base + (1.0 - self.alpha_base) * (1.0 - (certainty ** gamma))
        return float(max(self.alpha_base, min(1.0, alpha)))

    def compute_joint_similarity(
        self,
        live_embedding: np.ndarray,
        ltm_anchor: np.ndarray,
        stm_prototype: Optional[np.ndarray] = None
    ) -> Tuple[float, float, float]:
        """
        Compute Joint Dual-Memory Matching Score.
        
        Returns:
            (joint_similarity, ltm_similarity, stm_similarity)
        """
        live_emb = np.asarray(live_embedding, dtype=np.float32)
        ltm_emb = np.asarray(ltm_anchor, dtype=np.float32)
        
        # Ensure L2 normalization
        norm_live = np.linalg.norm(live_emb)
        norm_ltm = np.linalg.norm(ltm_emb)
        if norm_live > 0:
            live_emb = live_emb / norm_live
        if norm_ltm > 0:
            ltm_emb = ltm_emb / norm_ltm
            
        sim_ltm = float(np.dot(live_emb, ltm_emb))
        
        if stm_prototype is not None:
            stm_emb = np.asarray(stm_prototype, dtype=np.float32)
            norm_stm = np.linalg.norm(stm_emb)
            if norm_stm > 0:
                stm_emb = stm_emb / norm_stm
            sim_stm = float(np.dot(live_emb, stm_emb))
        else:
            sim_stm = sim_ltm

        joint_score = self.dual_lambda * sim_ltm + (1.0 - self.dual_lambda) * sim_stm
        return float(joint_score), float(sim_ltm), float(sim_stm)

    def calculate_drift_distance(
        self,
        candidate_stm: np.ndarray,
        ltm_anchor: np.ndarray
    ) -> float:
        """
        Compute Geodesic/Cosine Drift Distance on the unit hypersphere:
        D_drift = 1.0 - cos(E_cand, E_LTM)
        """
        cand = np.asarray(candidate_stm, dtype=np.float32)
        ltm = np.asarray(ltm_anchor, dtype=np.float32)
        
        cand = cand / (np.linalg.norm(cand) + 1e-8)
        ltm = ltm / (np.linalg.norm(ltm) + 1e-8)
        
        cosine_sim = float(np.dot(cand, ltm))
        drift_distance = max(0.0, 1.0 - cosine_sim)
        return float(drift_distance)

    def adapt(
        self,
        live_embedding: np.ndarray,
        ltm_anchor: np.ndarray,
        current_stm: np.ndarray,
        quality_score: float,
        liveness_score: float = 1.0,
    ) -> Tuple[np.ndarray, str, Dict[str, float]]:
        """
        Execute the Dynamic Template Adaptation & Drift-Guard Policy.
        
        Returns:
            (new_stm_vector, status_string, metrics_dict)
            where status_string in ["UPDATED", "ROLLBACK", "REJECTED"]
        """
        live_emb = np.asarray(live_embedding, dtype=np.float32)
        ltm = np.asarray(ltm_anchor, dtype=np.float32)
        stm = np.asarray(current_stm, dtype=np.float32)

        # 1. Compute dynamic alpha
        alpha = self.compute_dynamic_alpha(quality_score, liveness_score)

        # 2. Dynamic EMA computation
        cand_stm = alpha * stm + (1.0 - alpha) * live_emb
        cand_norm = np.linalg.norm(cand_stm)
        if cand_norm > 0:
            cand_stm = cand_stm / cand_norm

        # 3. Geodesic Drift Check against Immutable LTM Anchor
        drift_distance = self.calculate_drift_distance(cand_stm, ltm)

        metrics = {
            "alpha": alpha,
            "drift_distance": drift_distance,
            "quality_score": quality_score,
            "liveness_score": liveness_score,
            "drift_threshold": self.drift_threshold,
        }

        # 4. Drift Decision
        if drift_distance <= self.drift_threshold:
            logger.debug(f"UG-Adapt: Safe update accepted (drift={drift_distance:.4f}, alpha={alpha:.4f})")
            return cand_stm, "UPDATED", metrics
        else:
            logger.warning(
                f"[ALERT] UG-Adapt: Drift Breach Detected! (drift={drift_distance:.4f} > {self.drift_threshold:.4f}). "
                f"Triggering Auto-Rollback to LTM anchor."
            )
            # Rollback to pristine LTM anchor
            rollback_vector = ltm / (np.linalg.norm(ltm) + 1e-8)
            metrics["rollback_triggered"] = 1.0
            return rollback_vector, "ROLLBACK", metrics
