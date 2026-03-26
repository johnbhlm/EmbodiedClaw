import unittest

from apps.openclaw_bridge.openclaw_formatter import build_poll_response


class OpenClawImagePollingTests(unittest.TestCase):
    def test_completed_with_artifacts_exposes_images(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-1',
                'final_status': 'SUCCEEDED',
                'task_type': 'observe_scene',
                'result': {
                    'summary': '观测完成',
                    'artifact_uris': ['file:///tmp/obs_1.jpg', 'file:///tmp/obs_2.jpg'],
                },
                'progress': 1.0,
            }
        )
        self.assertEqual('completed', response.mode)
        self.assertEqual(['file:///tmp/obs_1.jpg', 'file:///tmp/obs_2.jpg'], response.image_uris)
        self.assertEqual('file:///tmp/obs_1.jpg', response.primary_image_uri)
        self.assertIn('已获取当前画面', response.reply_text)

    def test_completed_without_artifacts_has_empty_images(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-2',
                'final_status': 'SUCCEEDED',
                'result': {'summary': '执行完成'},
            }
        )
        self.assertEqual([], response.image_uris)
        self.assertIsNone(response.primary_image_uri)

    def test_running_has_empty_images(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-3',
                'final_status': 'RUNNING',
                'latest_stage': 'PERCEIVING',
                'latest_message': '处理中',
                'result': {'artifact_uris': ['file:///tmp/running.jpg']},
            }
        )
        self.assertEqual('running', response.mode)
        self.assertEqual([], response.image_uris)
        self.assertIsNone(response.primary_image_uri)

    def test_failed_without_artifacts_has_empty_images(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-4',
                'final_status': 'FAILED',
                'result': {'summary': '识别失败'},
            }
        )
        self.assertEqual('failed', response.mode)
        self.assertEqual([], response.image_uris)
        self.assertIsNone(response.primary_image_uri)

    def test_failed_with_artifacts_keeps_images(self) -> None:
        response = build_poll_response(
            {
                'task_id': 'task-5',
                'final_status': 'FAILED',
                'result': {
                    'summary': '部分失败',
                    'artifact_uris': ['file:///tmp/failure_snapshot.jpg'],
                },
            }
        )
        self.assertEqual('failed', response.mode)
        self.assertEqual(['file:///tmp/failure_snapshot.jpg'], response.image_uris)
        self.assertEqual('file:///tmp/failure_snapshot.jpg', response.primary_image_uri)


if __name__ == '__main__':
    unittest.main()
