import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.fake_navigate_provider import FakeNavigateProvider


class FakeNavigateProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = FakeNavigateProvider()

    def test_move_forward_success(self) -> None:
        result = self.provider.move_forward(1.0)
        self.assertTrue(result['success'])

    def test_relative_navigation_success(self) -> None:
        result = self.provider.navigate_to(pose_json='{"yaw_deg": 45}')
        self.assertTrue(result['success'])


if __name__ == '__main__':
    unittest.main()
