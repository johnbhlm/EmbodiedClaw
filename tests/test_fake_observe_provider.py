import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.fake_observe_provider import FakeObserveProvider


class FakeObserveProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = FakeObserveProvider()

    def test_object_existence(self) -> None:
        apple = self.provider.observe_scene(target='desk_01', mode='object_existence', extra={'object_name': 'apple'})
        banana = self.provider.observe_scene(target='desk_01', mode='object_existence', extra={'object_name': 'banana'})
        self.assertTrue(apple['exists'])
        self.assertFalse(banana['exists'])

    def test_object_list_contains_apple(self) -> None:
        finding = self.provider.observe_scene(target='desk_01', mode='object_list')
        self.assertIn('apple', finding['objects'])


if __name__ == '__main__':
    unittest.main()
