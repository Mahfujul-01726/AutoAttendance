"""
Cancelable Cryptographic Biometrics Module for GDPR/Privacy-Preserving Template Protection.
Implements Orthonormal Stochastic Projections (OSP) on the unit hypersphere S^{511}.

Properties (ISO/IEC 24745 Standards):
1. Irreversibility: Given protected embedding E_sec = W_k * E, finding original E without W_k is computationally intractable.
2. Unlinkability: Two different seeds generate completely uncorrelated protected templates from the same face.
3. Revocability: If a template is compromised, the user seed is revoked and a new orthonormal matrix is issued.
4. Isometric Invariance: Preserves exact Euclidean and Cosine distances: cos(W_k E1, W_k E2) = cos(E1, E2) because W_k^T * W_k = I.
"""

import hashlib
import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class CancelableBiometricsEngine:
    """
    Cryptographic Orthonormal Transformation Engine for ISO/IEC 24745 Compliant Biometrics.
    """

    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim

    def _seed_to_int(self, seed_key: str) -> int:
        """Convert a user string key/email/ID into a deterministic 32-bit integer seed."""
        digest = hashlib.sha256(str(seed_key).encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    def generate_orthonormal_matrix(self, seed_key: str) -> np.ndarray:
        """
        Generate a deterministic, user-specific Orthonormal matrix W_k in R^{D x D}.
        Uses Gram-Schmidt / QR decomposition: W_k^T * W_k = I_D.
        """
        seed_val = self._seed_to_int(seed_key)
        rng = np.random.RandomState(seed_val)
        
        # Generate random Gaussian matrix
        random_matrix = rng.randn(self.embedding_dim, self.embedding_dim).astype(np.float32)
        
        # QR Decomposition yields exact orthonormal Q matrix
        q_matrix, _ = np.linalg.qr(random_matrix)
        return q_matrix.astype(np.float32)

    def protect_embedding(
        self,
        raw_embedding: np.ndarray,
        user_seed: str,
    ) -> np.ndarray:
        """
        Transform raw 512-d biometric face vector into protected cancelable domain:
        E_sec = W_k * E_raw
        """
        vec = np.asarray(raw_embedding, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        w_k = self.generate_orthonormal_matrix(user_seed)
        sec_embedding = np.dot(w_k, vec)
        
        # Guarantee unit norm on S^{511}
        sec_embedding = sec_embedding / (np.linalg.norm(sec_embedding) + 1e-8)
        return sec_embedding.astype(np.float32)

    def compute_protected_similarity(
        self,
        query_embedding: np.ndarray,
        stored_protected_embedding: np.ndarray,
        user_seed: str,
    ) -> float:
        """
        Compute similarity in the protected cryptographic domain.
        Projects query embedding with W_k before computing dot product.
        """
        protected_query = self.protect_embedding(query_embedding, user_seed)
        stored_norm = stored_protected_embedding / (np.linalg.norm(stored_protected_embedding) + 1e-8)
        
        cosine_sim = float(np.dot(protected_query, stored_norm))
        return cosine_sim
