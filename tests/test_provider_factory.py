import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.fake_navigate_provider import FakeNavigateProvider
from providers.fake_observe_provider import FakeObserveProvider
from providers.provider_factory import get_navigate_provider, get_observe_provider


class ProviderFactoryTests(unittest.TestCase):
    def test_default_providers_are_fake(self) -> None:
        os.environ.pop('EMBODIEDCLAW_OBSERVE_PROVIDER', None)
        os.environ.pop('EMBODIEDCLAW_NAVIGATE_PROVIDER', None)

        self.assertIsInstance(get_observe_provider(), FakeObserveProvider)
        self.assertIsInstance(get_navigate_provider(), FakeNavigateProvider)


if __name__ == '__main__':
    unittest.main()
