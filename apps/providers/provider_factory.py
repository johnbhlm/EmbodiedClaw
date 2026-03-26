from __future__ import annotations

from .base import NavigateProvider, ObserveProvider
from .basic_observe_backend import BasicObserveBackend
from .fake_navigate_provider import FakeNavigateProvider
from .fake_observe_provider import FakeObserveProvider
from .provider_config import (
    get_navigate_provider_name,
    get_observe_backend_name,
    get_observe_provider_name,
    get_observe_require_fresh_frame_sec,
)
from .ros_camera_observe_provider import RosCameraObserveProvider


def _build_observe_backend(name: str):
    if name == 'basic':
        return BasicObserveBackend()
    raise ValueError(f'Unsupported observe backend: {name}')


def get_observe_provider(latest_image_buffer=None) -> ObserveProvider:
    provider_name = get_observe_provider_name()
    if provider_name == 'fake':
        return FakeObserveProvider()
    if provider_name == 'ros_camera':
        if latest_image_buffer is None:
            raise ValueError(
                'EMBODIEDCLAW_OBSERVE_PROVIDER=ros_camera requires a LatestImageBuffer from adapter runtime.'
            )
        backend = _build_observe_backend(get_observe_backend_name())
        return RosCameraObserveProvider(
            latest_image_buffer=latest_image_buffer,
            backend=backend,
            require_fresh_frame_sec=get_observe_require_fresh_frame_sec(),
        )
    raise ValueError(f'Unsupported observe provider: {provider_name}')


def get_navigate_provider() -> NavigateProvider:
    provider_name = get_navigate_provider_name()
    if provider_name == 'fake':
        return FakeNavigateProvider()
    raise ValueError(f'Unsupported navigate provider: {provider_name}')
