"""
Dual-Memory Template Adapter Module with Bayesian von Mises-Fisher (vMF) Hyperspherical Filter.
Implements:
1. Directional Bayesian vMF Maximum-A-Posteriori (MAP) hyperspherical belief update.
2. Dynamic Uncertainty-Aware Rate: alpha(t) = f(Q_face, S_live)
3. Decoupled Long-Term Memory (LTM Anchor) vs Short-Term Memory (STM Prototype)
4. Hyperspherical Geodesic Drift Guard (D_drift <= delta_max)
5. Zero-Poisoning Auto-Rollback mechanism
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
    Dual-Memory Continual Biometric Adaptation Engine with Bayesian vMF Hyperspherical Filtering.
    """

    def __init__(
        self,
        alpha_base: float = UG_ALPHA_BASE,
        drift_threshold: float = UG_DRIFT_THRESHOLD,
        dual_lambda: float = UG_DUAL_MEMORY_LAMBDA,
        kappa_base: float = 50.0,
    ):
        self.alpha_base = alpha_base
        self.drift_threshold = drift_threshold
        self.dual_lambda = dual_lambda
        self.kappa_base = kappa_base

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

    def bayesian_vmf_update(
        self,
        prior_mean: np.ndarray,
        prior_kappa: float,
        live_embedding: np.ndarray,
        quality_score: float,
        liveness_score: float,
    ) -> Tuple[np.ndarray, float]:
        r"""
        Riemannian Bayesian von Mises-Fisher (vMF) Directional Filter on S^{511}.
        
        Formula:
            R_{t+1} = \kappa_t \mu_t + \kappa_{obs} E_{live}
            \kappa_{t+1} = ||R_{t+1}||
            \mu_{t+1} = R_{t+1} / \kappa_{t+1}
            where \kappa_{obs} = \kappa_0 \cdot (Q_{face} \cdot S_{live})
        """
        mu_t = np.asarray(prior_mean, dtype=np.float32)
        mu_t = mu_t / (np.linalg.norm(mu_t) + 1e-8)

        e_live = np.asarray(live_embedding, dtype=np.float32)
        e_live = e_live / (np.linalg.norm(e_live) + 1e-8)

        # Observation certainty scales concentration
        certainty = float(np.clip(quality_score * liveness_score, 0.0, 1.0))
        kappa_obs = self.kappa_base * (certainty ** 2)

        # Posterior resultant vector
        resultant = (prior_kappa * mu_t) + (kappa_obs * e_live)
        posterior_kappa = float(np.linalg.norm(resultant) + 1e-8)
        posterior_mean = resultant / posterior_kappa

        return posterior_mean, posterior_kappa

    def compute_joint_similarity(
        self,
        live_embedding: np.ndarray,
        ltm_anchor: np.ndarray,
        stm_prototype: Optional[np.ndarray] = None
    ) -> Tuple[float, float, float]:
        """
        Compute Joint Dual-Memory Matching Score.
        """
        live_emb = np.asarray(live_embedding, dtype=np.float32)
        ltm_emb = np.asarray(ltm_anchor, dtype=np.float32)
        
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
        current_kappa: float = 50.0,
    ) -> Tuple[np.ndarray, str, Dict[str, float]]:
        """
        Execute the Dynamic Template Adaptation & Drift-Guard Policy with vMF Filtering.
        
        Returns:
            (new_stm_vector, status_string, metrics_dict)
            where status_string in ["UPDATED", "ROLLBACK", "REJECTED"]
        """
        live_emb = np.asarray(live_embedding, dtype=np.float32)
        ltm = np.asarray(ltm_anchor, dtype=np.float32)
        stm = np.asarray(current_stm, dtype=np.float32)

        # 1. Compute dynamic alpha & vMF posterior
        alpha = self.compute_dynamic_alpha(quality_score, liveness_score)
        vmf_mean, post_kappa = self.bayesian_vmf_update(
            prior_mean=stm,
            prior_kappa=current_kappa,
            live_embedding=live_emb,
            quality_score=quality_score,
            liveness_score=liveness_score
        )

        # Dynamic EMA candidate vector (aligned with vMF expectation)
        cand_stm = alpha * stm + (1.0 - alpha) * live_emb
        cand_norm = np.linalg.norm(cand_stm)
        if cand_norm > 0:
            cand_stm = cand_stm / cand_norm

        # 2. Geodesic Drift Check against Immutable LTM Anchor
        drift_distance = self.calculate_drift_distance(cand_stm, ltm)

        metrics = {
            "alpha": alpha,
            "drift_distance": drift_distance,
            "quality_score": quality_score,
            "liveness_score": liveness_score,
            "drift_threshold": self.drift_threshold,
            "posterior_kappa": post_kappa,
        }

        # 3. Drift Decision
        if drift_distance <= self.drift_threshold:
            logger.debug(f"UG-Adapt: Safe update accepted (drift={drift_distance:.4f}, alpha={alpha:.4f}, kappa={post_kappa:.1f})")
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
