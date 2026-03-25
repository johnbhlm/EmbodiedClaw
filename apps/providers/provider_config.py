from __future__ import annotations

import os

OBSERVE_PROVIDER_ENV = 'EMBODIEDCLAW_OBSERVE_PROVIDER'
NAVIGATE_PROVIDER_ENV = 'EMBODIEDCLAW_NAVIGATE_PROVIDER'
DEFAULT_PROVIDER = 'fake'


def _normalize(value: str | None, default: str = DEFAULT_PROVIDER) -> str:
    return (value or default).strip().lower() or default


def get_observe_provider_name() -> str:
    return _normalize(os.getenv(OBSERVE_PROVIDER_ENV), DEFAULT_PROVIDER)


def get_navigate_provider_name() -> str:
    return _normalize(os.getenv(NAVIGATE_PROVIDER_ENV), DEFAULT_PROVIDER)
