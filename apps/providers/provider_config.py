from __future__ import annotations

import os

OBSERVE_PROVIDER_ENV = 'EMBODIEDCLAW_OBSERVE_PROVIDER'
NAVIGATE_PROVIDER_ENV = 'EMBODIEDCLAW_NAVIGATE_PROVIDER'
CAMERA_TOPIC_ENV = 'EMBODIEDCLAW_CAMERA_TOPIC'
OBSERVE_BACKEND_ENV = 'EMBODIEDCLAW_OBSERVE_BACKEND'
OBSERVE_REQUIRE_FRESH_FRAME_SEC_ENV = 'EMBODIEDCLAW_OBSERVE_REQUIRE_FRESH_FRAME_SEC'
SAVE_OBSERVE_IMAGES_ENV = 'EMBODIEDCLAW_SAVE_OBSERVE_IMAGES'

DEFAULT_PROVIDER = 'fake'
DEFAULT_CAMERA_TOPIC = '/camera/camera/color/image_raw'
DEFAULT_OBSERVE_BACKEND = 'basic'
DEFAULT_OBSERVE_REQUIRE_FRESH_FRAME_SEC = 2.0
DEFAULT_SAVE_OBSERVE_IMAGES = True


def _normalize(value: str | None, default: str = DEFAULT_PROVIDER) -> str:
    return (value or default).strip().lower() or default


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    return default


def get_observe_provider_name() -> str:
    return _normalize(os.getenv(OBSERVE_PROVIDER_ENV), DEFAULT_PROVIDER)


def get_navigate_provider_name() -> str:
    return _normalize(os.getenv(NAVIGATE_PROVIDER_ENV), DEFAULT_PROVIDER)


def get_camera_topic() -> str:
    return (os.getenv(CAMERA_TOPIC_ENV) or DEFAULT_CAMERA_TOPIC).strip() or DEFAULT_CAMERA_TOPIC


def get_observe_backend_name() -> str:
    return _normalize(os.getenv(OBSERVE_BACKEND_ENV), DEFAULT_OBSERVE_BACKEND)


def get_observe_require_fresh_frame_sec() -> float:
    return _parse_float(os.getenv(OBSERVE_REQUIRE_FRESH_FRAME_SEC_ENV), DEFAULT_OBSERVE_REQUIRE_FRESH_FRAME_SEC)


def get_save_observe_images() -> bool:
    return _parse_bool(os.getenv(SAVE_OBSERVE_IMAGES_ENV), DEFAULT_SAVE_OBSERVE_IMAGES)
