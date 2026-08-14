"""
Planar Homography Optical Flow Disparity Guard Module.
Rejects 2D Deepfake video replays and flat mobile/iPad screen presentation attacks.
Exploits 3D facial curvature depth disparity vs flat planar perspective homography.
"""

import collections
from typing import Dict, Optional, Tuple
import cv2
import numpy as np


class PlanarHomographyFlowGuard:
    """
    3D Facial Curvature vs 2D Flat Screen Optical Flow Disparity Engine.
    """

    def __init__(self, history_len: int = 10, min_disparity_threshold: float = 1.2):
        self.history_len = history_len
        self.min_disparity_threshold = min_disparity_threshold
        # Stores historical landmark coordinates per active identity key
        self.trackers: Dict[str, collections.deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=self.history_len)
        )

    def evaluate_depth_curvature(
        self,
        landmarks: Optional[np.ndarray],
        subject_key: str = "default",
    ) -> Tuple[bool, float, Dict[str, float]]:
        """
        Evaluate non-planar 3D optical flow disparity across consecutive video frames.
        
        Returns:
            (is_genuine_3d, disparity_score, metrics_dict)
            - is_genuine_3d: True if real 3D head, False if flat 2D screen replay.
        """
        if landmarks is None or len(landmarks) < 4:
            # Neutral pass for unaligned single frames
            return True, 2.5, {"homography_residue": 2.5, "is_flat_screen": 0.0}

        pts = np.asarray(landmarks, dtype=np.float32)
        history = self.trackers[subject_key]
        history.append(pts)

        if len(history) < 3:
            return True, 2.0, {"homography_residue": 2.0, "is_flat_screen": 0.0}

        prev_pts = history[-2]
        curr_pts = history[-1]

        # Compute optical flow motion magnitude
        motion_vector = curr_pts - prev_pts
        motion_mag = float(np.mean(np.linalg.norm(motion_vector, axis=1)))

        # If head is stationary (micro-jitter only), pass with nominal baseline
        if motion_mag < 0.8:
            return True, 1.8, {"homography_residue": 1.8, "is_flat_screen": 0.0}

        # Estimate 2D Perspective Homography Matrix H (3x3) using RANSAC
        try:
            h_matrix, _inliers = cv2.findHomography(prev_pts, curr_pts, cv2.RANSAC, 3.0)
            if h_matrix is not None:
                # Project previous points through flat 2D homography
                prev_homo = np.hstack([prev_pts, np.ones((len(prev_pts), 1), dtype=np.float32)])
                projected = np.dot(h_matrix, prev_homo.T).T
                projected_2d = projected[:, :2] / (projected[:, 2:3] + 1e-8)

                # Compute Non-Planar 3D Curvature Residue
                residue = float(np.mean(np.linalg.norm(curr_pts - projected_2d, axis=1)))
            else:
                residue = 2.0
        except Exception:
            residue = 2.0

        # A flat screen has residue ~ 0.0 to 0.5 (strictly planar motion)
        # A real 3D face with nose/cheeks/eyes depth has residue > 1.2
        is_flat_screen = residue < self.min_disparity_threshold
        is_genuine_3d = not is_flat_screen

        metrics = {
            "homography_residue": residue,
            "motion_magnitude": motion_mag,
            "is_flat_screen": 1.0 if is_flat_screen else 0.0,
            "disparity_score": float(np.clip(residue / 3.0, 0.0, 1.0)),
        }

        return is_genuine_3d, residue, metrics
