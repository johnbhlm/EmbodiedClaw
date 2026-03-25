from __future__ import annotations

from providers.base import NavigateProvider, ObserveProvider
from providers.fake_navigate_provider import FakeNavigateProvider
from providers.fake_observe_provider import FakeObserveProvider
from providers.provider_config import get_navigate_provider_name, get_observe_provider_name


def get_observe_provider() -> ObserveProvider:
    provider_name = get_observe_provider_name()
    if provider_name == 'fake':
        return FakeObserveProvider()
    raise ValueError(f'Unsupported observe provider: {provider_name}')


def get_navigate_provider() -> NavigateProvider:
    provider_name = get_navigate_provider_name()
    if provider_name == 'fake':
        return FakeNavigateProvider()
    raise ValueError(f'Unsupported navigate provider: {provider_name}')
