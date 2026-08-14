"""
Cross-Camera Sliced-Wasserstein Optimal Transport Domain Alignment Module.
Aligns multi-camera embedding distributions (e.g., Gate camera vs. Overhead Classroom camera) on S^{511}.
Provides zero-retraining closed-form Riemannian domain transfer.
"""

from typing import Dict, Tuple
import numpy as np


class CrossCameraOptimalTransportAligner:
    """
    Closed-Form Sliced-Wasserstein Domain Alignment Engine on Riemannian Hyperspheres.
    """

    def __init__(self, embedding_dim: int = 512, num_projections: int = 50):
        self.embedding_dim = embedding_dim
        self.num_projections = num_projections
        # Domain shift adaptation parameters per camera ID
        self.camera_rotations: Dict[str, np.ndarray] = {}

    def compute_sliced_wasserstein_distance(
        self,
        source_embeddings: np.ndarray,
        target_embeddings: np.ndarray,
    ) -> float:
        """
        Compute Sliced-Wasserstein Distance (SWD) between two camera embedding distributions.
        """
        n_src, dim = source_embeddings.shape
        n_tgt = target_embeddings.shape[0]

        # Generate random 1D unit projection vectors on S^{D-1}
        projections = np.random.randn(self.num_projections, dim).astype(np.float32)
        projections = projections / np.linalg.norm(projections, axis=1, keepdims=True)

        swd_total = 0.0
        for theta in projections:
            # Project onto 1D line
            proj_src = np.dot(source_embeddings, theta)
            proj_tgt = np.dot(target_embeddings, theta)

            # Sort 1D projections
            sorted_src = np.sort(proj_src)
            sorted_tgt = np.sort(proj_tgt)

            # Resample to match length if different
            if n_src != n_tgt:
                indices = np.linspace(0, n_tgt - 1, n_src).astype(int)
                sorted_tgt = sorted_tgt[indices]

            # 1D Wasserstein-1 Distance is L1 norm of sorted vectors
            w1 = float(np.mean(np.abs(sorted_src - sorted_tgt)))
            swd_total += w1

        return float(swd_total / self.num_projections)

    def calibrate_camera_domain(
        self,
        camera_id: str,
        camera_samples: np.ndarray,
        reference_samples: np.ndarray,
    ) -> np.ndarray:
        """
        Estimate optimal Procrustes rotation matrix R in O(D) aligning camera_samples to reference:
        min_R ||reference - camera * R||_F subject to R^T * R = I
        """
        # Cross-covariance matrix
        h_cov = np.dot(camera_samples.T, reference_samples)
        # SVD decomposition
        u, _s, vt = np.linalg.svd(h_cov)
        r_opt = np.dot(u, vt).astype(np.float32)

        self.camera_rotations[camera_id] = r_opt
        return r_opt

    def align_query_to_reference(
        self,
        query_embedding: np.ndarray,
        camera_id: str,
    ) -> np.ndarray:
        """
        Transform a live embedding from camera_id into the canonical reference space.
        """
        vec = np.asarray(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        r_matrix = self.camera_rotations.get(camera_id)
        if r_matrix is not None:
            aligned = np.dot(vec, r_matrix)
            aligned = aligned / (np.linalg.norm(aligned) + 1e-8)
            return aligned.astype(np.float32)

        return vec
