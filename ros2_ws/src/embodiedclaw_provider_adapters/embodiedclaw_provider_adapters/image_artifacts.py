from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import cv2

ARTIFACT_DIR = Path.home() / 'code' / 'EmbodiedClaw' / 'runtime_artifacts' / 'observations'


def save_observation_frame(frame_bgr) -> str | None:
    """Persist observation frame and return file:// URI."""
    try:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')
        output_path = ARTIFACT_DIR / f'frame_{timestamp}.jpg'
        ok = cv2.imwrite(str(output_path), frame_bgr)
        if not ok:
            return None
        return output_path.resolve().as_uri()
    except Exception:
        return None
