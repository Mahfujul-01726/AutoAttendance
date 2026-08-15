"""
Interactive Visual Demo for All Research Novelties in AutoAttendance.
Fully Dynamic Real-Time Telemetry & Visual HUD:
1. Explainable AI (XAI Saliency Jet Heatmap)
2. Multi-Scale Retinex Photometric Illumination Normalization (Live Gain & Contrast)
3. Total Variation Adversarial Patch Defense Filtering (Live Energy Ratio)
4. rPPG Contactless Sub-Dermal Blood-Pulse Heart Rate & Spectral SNR
5. Planar Homography 3D Flow Disparity Guard (Live Frame-to-Frame Residue)
6. Multi-Cue DoG + FFT Anti-Spoofing Score
7. ISO/IEC 24745 Cancelable Biometrics & Riemannian (eps, delta)-Differential Privacy
8. Occlusion-Aware Dynamic Sub-Embedding Gating (Live Spatial Visibility)
9. UG-Adapt Bayesian vMF Dynamic Learning Rate alpha(t) & Drift Guard

Usage:
    python demo_all_novelties.py
"""

import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Add project root to sys.path
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from auto_attendance.face_recognition import FaceRecognitionModule
from auto_attendance.anti_spoofing import AntiSpoofing
from auto_attendance.explainable_ai import ExplainableSaliencyAttributor
from auto_attendance.photometric_harmonization import AdaptiveRetinexHarmonizer
from auto_attendance.adversarial_patch_filter import AdversarialPatchDefenseFilter
from auto_attendance.rppg_pulse_guard import RemotePulseLivenessGuard
from auto_attendance.homography_flow_guard import PlanarHomographyFlowGuard
from auto_attendance.cancelable_biometrics import CancelableBiometricsEngine
from auto_attendance.differential_privacy import HypersphericalDifferentialPrivacyEngine
from auto_attendance.occlusion_gating import OcclusionAwareSubEmbeddingGater
from auto_attendance.quality_gate import QualityGate
from auto_attendance.template_adapter import DualMemoryTemplateAdapter
from auto_attendance.config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT


def draw_crisp_text(img, text, pos, color=(0, 255, 0), scale=0.48, thickness=1):
    """Draw single razor-sharp text with anti-aliasing (no shadow bleed)."""
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def run_live_novelty_demo():
    print("=" * 70)
    print("  AUTOATTENDANCE - FULLY DYNAMIC MULTI-NOVELTY TELEMETRY HUD")
    print("=" * 70)
    print("  Controls:")
    print("    'q' - Quit Demo")
    print("    's' - Save Current HUD Snapshot")
    print("=" * 70 + "\n")

    # Initialize all novelty engines
    recognizer = FaceRecognitionModule()
    recognizer.load_model()
    anti_spoof = AntiSpoofing()
    xai = ExplainableSaliencyAttributor()
    retinex = AdaptiveRetinexHarmonizer()
    patch_filter = AdversarialPatchDefenseFilter()
    rppg = RemotePulseLivenessGuard(buffer_length=45, fps=30.0)
    flow_guard = PlanarHomographyFlowGuard(history_len=10)
    cancelable = CancelableBiometricsEngine()
    dp_engine = HypersphericalDifferentialPrivacyEngine(epsilon=1.5)
    occlusion = OcclusionAwareSubEmbeddingGater()
    quality_gate = QualityGate()
    adapter = DualMemoryTemplateAdapter()

    cap = cv2.VideoCapture(CAMERA_ID)
    if not cap.isOpened():
        print(f"Error: Cannot access camera (ID: {CAMERA_ID})")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    fps_history = []
    t_prev = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read camera frame")
            break

        # Calculate dynamic FPS
        t_curr = time.time()
        fps = 1.0 / max(1e-4, (t_curr - t_prev))
        t_prev = t_curr
        fps_history.append(fps)
        if len(fps_history) > 15:
            fps_history.pop(0)
        avg_fps = float(np.mean(fps_history))

        frame = cv2.flip(frame, 1)
        h_main, w_main = frame.shape[:2]

        # Detect faces
        faces = recognizer.detect_faces(frame)

        # 3-panel visual HUD dimensions on the right
        panel_w, panel_h = 240, 180

        # Telemetry metrics dictionary
        telemetry = {}
        has_face = False
        is_masked = False

        if faces:
            primary_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            x1, y1, x2, y2 = recognizer._bbox_to_int(primary_face.bbox, frame.shape)
            face_crop = frame[y1:y2, x1:x2]
            landmarks = getattr(primary_face, "kps", None)
            det_score = float(getattr(primary_face, "det_score", 0.95))

            if face_crop.size > 0:
                has_face = True
                h_crop, w_crop = face_crop.shape[:2]

                # 1. Live Match against SQLite database
                emb = recognizer._normalized_embedding(primary_face)
                match = recognizer._match_embedding(emb)
                student_name = match["student_name"] if match else "Unknown / Guest"
                cos_dist = match["distance"] if match else 1.0

                # 2. Live Explainable AI Heatmap
                xai_crop, xai_metrics = xai.compute_saliency_heatmap(face_crop, confidence_score=det_score)
                xai_panel = cv2.resize(xai_crop, (panel_w, panel_h))

                # 3. Live Retinex Illumination Harmonization
                retinex_crop = retinex.harmonize(face_crop)
                retinex_panel = cv2.resize(retinex_crop, (panel_w, panel_h))
                
                std_raw = float(np.std(face_crop) + 1e-4)
                std_ret = float(np.std(retinex_crop) + 1e-4)
                contrast_gain = std_ret / std_raw
                mean_lum_raw = float(np.mean(cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)))
                mean_lum_ret = float(np.mean(cv2.cvtColor(retinex_crop, cv2.COLOR_BGR2GRAY)))

                # 4. Live Adversarial Patch Defense
                is_adv, adv_ratio, patch_metrics = patch_filter.detect_adversarial_gradients(face_crop)
                sanitized_crop = patch_filter.sanitize_adversarial_crop(face_crop)
                patch_panel = cv2.resize(sanitized_crop, (panel_w, panel_h))

                # 5. Live Occlusion Gating & Mask Detection
                weights, occ_metrics = occlusion.evaluate_spatial_visibility(face_crop, landmarks)
                is_masked = bool(occ_metrics.get("mask_detected", 0.0) == 1.0)
                upper_vis = occ_metrics.get("upper_visibility", 1.0)
                lower_vis = occ_metrics.get("lower_visibility", 1.0)

                # 6. Live rPPG Contactless Cardiovascular Pulse
                is_cardiac_live, rppg_conf, rppg_metrics = rppg.evaluate_cardiac_liveness(face_crop, subject_key="live_user")
                live_bpm = rppg_metrics.get("bpm", 72.0)
                live_snr = rppg_metrics.get("cardiac_snr", 2.5)

                # 7. Live Planar Homography 3D Flow Guard
                is_3d_real, homography_residue, homography_metrics = flow_guard.evaluate_depth_curvature(landmarks, subject_key="live_user")

                # 8. Live Anti-Spoofing DoG/FFT Spectral Score
                is_dog_real, dog_spoof_score = anti_spoof.analyze(face_crop)

                # 9. Live Quality Gate & Dynamic Bayesian alpha(t) rate
                sharpness = quality_gate.calculate_sharpness(face_crop)
                illumination = quality_gate.calculate_illumination(face_crop)
                pose_score, yaw, pitch = quality_gate.calculate_pose_score(landmarks)
                q_face = (0.40 * sharpness) + (0.30 * illumination) + (0.30 * pose_score)
                dynamic_alpha = adapter.compute_dynamic_alpha(quality_score=q_face, liveness_score=rppg_conf)

                # 10. Live Cancelable Biometrics & DP Perturbation
                transformed_emb = cancelable.protect_embedding(emb, user_seed="user_101")
                privatized_emb, dp_metrics = dp_engine.privatize_embedding(emb)
                dp_fidelity = dp_metrics.get("retention_fidelity", 0.985)

                # Draw bounding boxes on raw frame
                box_color = (0, 255, 255) if is_masked else (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                
                # Occlusion indicator boxes on the face
                if is_masked:
                    y_mask_top = y1 + int(h_crop * 0.55)
                    cv2.rectangle(frame, (x1, y_mask_top), (x2, y2), (0, 165, 255), 2)
                    y_eye_bottom = y1 + int(h_crop * 0.50)
                    cv2.rectangle(frame, (x1, y1), (x2, y_eye_bottom), (0, 255, 0), 1)

                telemetry = {
                    "student_name": student_name,
                    "cos_dist": cos_dist,
                    "live_bpm": live_bpm,
                    "live_snr": live_snr,
                    "is_cardiac_live": is_cardiac_live,
                    "rppg_conf": rppg_conf,
                    "is_3d_real": is_3d_real,
                    "homography_residue": homography_residue,
                    "is_dog_real": is_dog_real,
                    "dog_spoof_score": dog_spoof_score,
                    "is_masked": is_masked,
                    "upper_vis": upper_vis,
                    "lower_vis": lower_vis,
                    "contrast_gain": contrast_gain,
                    "mean_lum_raw": mean_lum_raw,
                    "mean_lum_ret": mean_lum_ret,
                    "is_adv": is_adv,
                    "adv_ratio": adv_ratio,
                    "dynamic_alpha": dynamic_alpha,
                    "q_face": q_face,
                    "hash_dim": len(transformed_emb),
                    "dp_fidelity": dp_fidelity,
                    "xai_upper": xai_metrics.get('upper_zone_pct', 0),
                    "xai_mid": xai_metrics.get('mid_zone_pct', 0),
                }

        if not has_face:
            xai_panel = np.zeros((panel_h, panel_w, 3), dtype=np.uint8)
            retinex_panel = np.zeros((panel_h, panel_w, 3), dtype=np.uint8)
            patch_panel = np.zeros((panel_h, panel_w, 3), dtype=np.uint8)
            draw_crisp_text(xai_panel, "No Face Detected", (30, 90), (0, 0, 255), 0.55)
            draw_crisp_text(retinex_panel, "No Face Detected", (30, 90), (0, 0, 255), 0.55)
            draw_crisp_text(patch_panel, "No Face Detected", (30, 90), (0, 0, 255), 0.55)

        # Label the 3 mini panels with solid banner
        for p, title in [(xai_panel, "[XAI Attention Heatmap]"), 
                         (retinex_panel, "[Retinex Enhanced View]"), 
                         (patch_panel, "[Adv-Patch Defense]")]:
            cv2.rectangle(p, (0, 0), (panel_w, 24), (20, 20, 20), -1)
            draw_crisp_text(p, title, (8, 16), (0, 255, 255), 0.45, 1)

        # Stack the 3 panels vertically on the right
        right_column = np.vstack([xai_panel, retinex_panel, patch_panel])
        
        # Resize main frame height to match right column height (540px)
        target_h = 540
        main_resized = cv2.resize(frame, (int(w_main * (target_h / h_main)), target_h))
        combined_dashboard = np.hstack([main_resized, right_column])

        # NOW draw the Telemetry HUD cleanly onto the combined canvas
        if has_face and telemetry:
            card_x1, card_y1, card_x2, card_y2 = 12, 12, 420, 290
            # Solid dark background card with crisp border
            cv2.rectangle(combined_dashboard, (card_x1, card_y1), (card_x2, card_y2), (16, 16, 16), -1)
            cv2.rectangle(combined_dashboard, (card_x1, card_y1), (card_x2, card_y2), (50, 50, 50), 1)

            # Header
            draw_crisp_text(combined_dashboard, f"--- LIVE TELEMETRY (FPS: {avg_fps:.1f}) ---", (card_x1 + 10, card_y1 + 22), (0, 255, 255), 0.48, 1)

            # Line 1: rPPG
            rppg_col = (0, 255, 0) if telemetry["is_cardiac_live"] else (0, 165, 255)
            draw_crisp_text(combined_dashboard, f"1. rPPG Pulse: {telemetry['live_bpm']:.1f} BPM (SNR: {telemetry['live_snr']:.2f}dB)", (card_x1 + 10, card_y1 + 46), rppg_col)

            # Line 2: 3D Homography Flow
            flow_col = (0, 255, 0) if telemetry["is_3d_real"] else (0, 0, 255)
            flow_txt = "3D Real Face" if telemetry["is_3d_real"] else "2D Planar Screen"
            draw_crisp_text(combined_dashboard, f"2. 3D Flow Guard: {flow_txt} (Residue={telemetry['homography_residue']:.2f})", (card_x1 + 10, card_y1 + 70), flow_col)

            # Line 3: Anti-Spoofing DoG/FFT
            dog_col = (0, 255, 0) if telemetry["is_dog_real"] else (0, 0, 255)
            draw_crisp_text(combined_dashboard, f"3. Spectral Anti-Spoof: {'Live Human' if telemetry['is_dog_real'] else 'Spoof'} (Score={telemetry['dog_spoof_score']:.3f})", (card_x1 + 10, card_y1 + 94), dog_col)

            # Line 4: Occlusion Gating
            if telemetry["is_masked"]:
                occ_txt = f"4. Occlusion: MASK DETECTED (Up={telemetry['upper_vis']:.2f}, Low={telemetry['lower_vis']:.2f})"
                occ_col = (0, 165, 255)
            else:
                occ_txt = f"4. Occlusion: Clean Face (Vis: Up={telemetry['upper_vis']:.2f}, Low={telemetry['lower_vis']:.2f})"
                occ_col = (255, 255, 255)
            draw_crisp_text(combined_dashboard, occ_txt, (card_x1 + 10, card_y1 + 118), occ_col)

            # Line 5: Retinex Illumination
            draw_crisp_text(combined_dashboard, f"5. Retinex Lighting: Gain={telemetry['contrast_gain']:.2f}x (Lum: {telemetry['mean_lum_raw']:.0f}->{telemetry['mean_lum_ret']:.0f})", (card_x1 + 10, card_y1 + 142), (255, 200, 100))

            # Line 6: Adversarial Patch Filter
            patch_col = (0, 0, 255) if telemetry["is_adv"] else (200, 255, 100)
            draw_crisp_text(combined_dashboard, f"6. Adv Patch Def: {'Detected' if telemetry['is_adv'] else 'Clean'} (Grad-Ratio={telemetry['adv_ratio']:.2f})", (card_x1 + 10, card_y1 + 166), patch_col)

            # Line 7: UG-Adapt Bayesian vMF Dynamic alpha(t)
            draw_crisp_text(combined_dashboard, f"7. UG-Adapt vMF: alpha(t)={telemetry['dynamic_alpha']:.4f} (Quality={telemetry['q_face']:.2f})", (card_x1 + 10, card_y1 + 190), (100, 255, 200))

            # Line 8: Cancelable Biometrics
            draw_crisp_text(combined_dashboard, f"8. Cancelable Bio: W_k Ortho-Hash Dim={telemetry['hash_dim']}", (card_x1 + 10, card_y1 + 214), (100, 255, 255))

            # Line 9: Differential Privacy
            draw_crisp_text(combined_dashboard, f"9. Diff Privacy: eps=1.5 (Fidelity={telemetry['dp_fidelity']:.4f})", (card_x1 + 10, card_y1 + 238), (255, 150, 255))

            # Line 10: XAI Attention Attribution
            draw_crisp_text(combined_dashboard, f"10. XAI Saliency: Upper={telemetry['xai_upper']}% Mid={telemetry['xai_mid']}%", (card_x1 + 10, card_y1 + 262), (255, 255, 150))

        # Status footer bar
        cv2.rectangle(combined_dashboard, (0, target_h - 26), (combined_dashboard.shape[1], target_h), (20, 20, 20), -1)
        draw_crisp_text(combined_dashboard, f"AutoAttendance Live HUD | Press 's' to Save Snapshot | 'q' to Quit", 
                        (15, target_h - 8), (200, 200, 200), 0.45, 1)

        cv2.imshow("AutoAttendance - Comprehensive Novelty Visualizer", combined_dashboard)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            snap_path = BASE_DIR / f"novelty_hud_snapshot_{int(time.time())}.jpg"
            cv2.imwrite(str(snap_path), combined_dashboard)
            print(f"✓ Snapshot saved: {snap_path}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_live_novelty_demo()
