from __future__ import annotations

from typing import Any


def _normalize_image_uris(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def extract_sendable_media(response: dict) -> dict:
    """Extract image send hints from OpenClaw polling/message response payloads."""
    image_uris = _normalize_image_uris(response.get('image_uris'))
    primary_image_uri = response.get('primary_image_uri')

    if not image_uris and isinstance(primary_image_uri, str) and primary_image_uri.strip():
        image_uris = [primary_image_uri]
    elif image_uris and not isinstance(primary_image_uri, str):
        primary_image_uri = image_uris[0]

    if not isinstance(primary_image_uri, str) or not primary_image_uri.strip():
        primary_image_uri = image_uris[0] if image_uris else None

    return {
        'has_image': bool(image_uris),
        'primary_image_uri': primary_image_uri,
        'image_uris': image_uris,
    }
