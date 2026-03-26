import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from providers.basic_observe_backend import BasicObserveBackend


class BasicObserveBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = BasicObserveBackend()
        class DummyFrame:
            shape = (10, 20, 3)

        self.frame = DummyFrame()

    def test_scene_summary_mode(self) -> None:
        result = self.backend.infer(self.frame, mode='scene_summary', target='desk')
        self.assertTrue(result['ok'])
        self.assertEqual(result['mode'], 'scene_summary')
        self.assertEqual(result['image_size'], {'width': 20, 'height': 10})

    def test_object_list_mode(self) -> None:
        result = self.backend.infer(self.frame, mode='object_list', target='desk')
        self.assertEqual(result['objects'], ['unknown_object'])
        self.assertIn('not connected yet', result['note'])

    def test_object_existence_mode(self) -> None:
        result = self.backend.infer(
            self.frame,
            mode='object_existence',
            target='desk',
            extra={'object_name': 'cup'},
        )
        self.assertEqual(result['object_name'], 'cup')
        self.assertFalse(result['exists'])

    def test_verify_surface_mode(self) -> None:
        result = self.backend.infer(self.frame, mode='verify_surface', target='desk')
        self.assertFalse(result['tidy'])

    def test_window_state_mode(self) -> None:
        result = self.backend.infer(self.frame, mode='window_state', target='window_01')
        self.assertEqual(result['target_id'], 'window_01')
        self.assertIsNone(result['closed'])

    def test_light_state_mode(self) -> None:
        result = self.backend.infer(self.frame, mode='light_state', target='light_01')
        self.assertEqual(result['target_id'], 'light_01')
        self.assertIsNone(result['off'])


if __name__ == '__main__':
    unittest.main()
