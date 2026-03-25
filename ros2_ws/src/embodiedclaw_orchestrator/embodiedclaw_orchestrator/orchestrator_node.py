import json
import threading
from dataclasses import dataclass
from typing import Any, Dict, List

import rclpy
from rclpy.action import ActionClient, ActionServer
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from embodiedclaw_msgs.action import ExecuteTask, InspectSkill, ManipulateSkill, NavigateSkill
from embodiedclaw_msgs.msg import TaskEvent


@dataclass
class SkillCallResult:
    success: bool
    detail: str
    artifact_uris: List[str]
    image_uris: List[str]


class OrchestratorNode(Node):
    def __init__(self) -> None:
        super().__init__('embodiedclaw_orchestrator')
        self.event_publisher = self.create_publisher(TaskEvent, '/assistant/task_events', 10)
        self.action_server = ActionServer(
            self,
            ExecuteTask,
            '/assistant/execute_task',
            execute_callback=self.execute_callback,
        )
        self._navigate_client = ActionClient(self, NavigateSkill, '/assistant/navigate_skill')
        self._manipulate_client = ActionClient(self, ManipulateSkill, '/assistant/manipulate_skill')
        self._inspect_client = ActionClient(self, InspectSkill, '/assistant/inspect_skill')
        self.get_logger().info('EmbodiedClaw orchestrator started (skill-oriented).')

    def _publish_event(self, task_id: str, stage: str, status: str, message: str, image_uri: str = '') -> None:
        event = TaskEvent()
        event.task_id = task_id
        event.stage = stage
        event.status = status
        event.message = message
        event.image_uri = image_uri
        event.stamp = self.get_clock().now().to_msg()
        self.event_publisher.publish(event)

    def _publish_feedback(self, goal_handle, stage: str, progress: float, message: str, image_uri: str = '') -> None:
        feedback = ExecuteTask.Feedback()
        feedback.stage = stage
        feedback.progress = progress
        feedback.message = message
        feedback.image_uri = image_uri
        goal_handle.publish_feedback(feedback)

    def _forward_skill_feedback(self, goal_handle, stage: str, feedback, progress_base: float, progress_span: float) -> None:
        progress = min(0.99, progress_base + (feedback.progress * progress_span))
        message = f'[{feedback.phase}] {feedback.message}'
        image_uri = getattr(feedback, 'image_uri', '')
        self._publish_feedback(goal_handle, stage, progress, message, image_uri)

    def _call_skill(self, client: ActionClient, goal_msg: Any, goal_handle, stage: str, progress_base: float, progress_span: float) -> SkillCallResult:
        if not client.wait_for_server(timeout_sec=2.0):
            return SkillCallResult(False, f'Skill action unavailable for stage {stage}', [], [])

        done_event = threading.Event()
        state: Dict[str, Any] = {}

        def _feedback_cb(feedback_msg):
            self._forward_skill_feedback(goal_handle, stage, feedback_msg.feedback, progress_base, progress_span)

        def _goal_response_cb(future):
            accepted_handle = future.result()
            if accepted_handle is None or not accepted_handle.accepted:
                state['result'] = SkillCallResult(False, f'Skill goal rejected for stage {stage}', [], [])
                done_event.set()
                return

            result_future = accepted_handle.get_result_async()

            def _result_cb(result_future_inner):
                wrapped_result = result_future_inner.result().result
                if hasattr(wrapped_result, 'detail'):
                    detail = wrapped_result.detail
                elif hasattr(wrapped_result, 'finding'):
                    detail = wrapped_result.finding
                else:
                    detail = ''

                artifact_uris = list(getattr(wrapped_result, 'artifact_uris', []))
                image_uris = list(getattr(wrapped_result, 'image_uris', []))
                state['result'] = SkillCallResult(bool(wrapped_result.success), detail, artifact_uris, image_uris)
                done_event.set()

            result_future.add_done_callback(_result_cb)

        send_future = client.send_goal_async(goal_msg, feedback_callback=_feedback_cb)
        send_future.add_done_callback(_goal_response_cb)

        done_event.wait(timeout=30.0)
        if not done_event.is_set():
            return SkillCallResult(False, f'Skill action timed out for stage {stage}', [], [])

        return state['result']

    def _fail_task(self, goal_handle, task_id: str, stage: str, message: str, error_code: str, artifact_uris: List[str] | None = None):
        artifacts = artifact_uris or []
        self._publish_event(task_id, stage, 'FAILED', message)
        self._publish_feedback(goal_handle, stage, 1.0, message)
        goal_handle.abort()

        result = ExecuteTask.Result()
        result.success = False
        result.summary = message
        result.artifact_uris = artifacts
        result.error_code = error_code
        return result

    def _run_tidy_desk(self, goal_handle, task_id: str, task_payload: Dict[str, Any]) -> ExecuteTask.Result:
        self._publish_event(task_id, 'PLANNING', 'RUNNING', 'Building tidy desk skill plan')
        self._publish_feedback(goal_handle, 'PLANNING', 0.1, 'Building tidy desk skill plan')

        nav_goal = NavigateSkill.Goal()
        nav_goal.request_id = f'{task_id}-navigate'
        nav_goal.target_type = 'area'
        nav_goal.location_id = str(task_payload.get('area', 'desk_zone'))
        nav_goal.pose_json = json.dumps(task_payload.get('target_pose', {}))

        nav_result = self._call_skill(self._navigate_client, nav_goal, goal_handle, 'NAVIGATING', 0.15, 0.2)
        if not nav_result.success:
            return self._fail_task(goal_handle, task_id, 'NAVIGATING', nav_result.detail or 'Navigate skill failed', 'NAVIGATE_FAILED')

        self._publish_event(task_id, 'PERCEIVING', 'RUNNING', 'Preparing manipulation request')
        self._publish_feedback(goal_handle, 'PERCEIVING', 0.42, 'Preparing manipulation request')

        manipulate_goal = ManipulateSkill.Goal()
        manipulate_goal.request_id = f'{task_id}-manipulate'
        manipulate_goal.skill_name = 'tidy_surface'
        manipulate_goal.target_object = str(task_payload.get('target_object', 'desk_items'))
        manipulate_goal.target_place = str(task_payload.get('target_place', 'desk_surface'))
        manipulate_goal.params_json = json.dumps(task_payload)

        manipulate_result = self._call_skill(self._manipulate_client, manipulate_goal, goal_handle, 'MANIPULATING', 0.45, 0.3)
        if not manipulate_result.success:
            return self._fail_task(
                goal_handle,
                task_id,
                'MANIPULATING',
                manipulate_result.detail or 'Manipulate skill failed',
                'MANIPULATE_FAILED',
            )

        inspect_goal = InspectSkill.Goal()
        inspect_goal.request_id = f'{task_id}-inspect'
        inspect_goal.inspect_type = 'verify_surface'
        inspect_goal.target_id = str(task_payload.get('area', 'desk_zone'))
        inspect_goal.params_json = json.dumps({'source': 'tidy_desk'})

        inspect_result = self._call_skill(self._inspect_client, inspect_goal, goal_handle, 'VERIFYING', 0.78, 0.15)
        if not inspect_result.success:
            return self._fail_task(goal_handle, task_id, 'VERIFYING', inspect_result.detail or 'Inspect skill failed', 'INSPECT_FAILED')

        self._publish_event(task_id, 'REPORTING', 'RUNNING', 'Aggregating tidy desk result')
        self._publish_feedback(goal_handle, 'REPORTING', 0.95, 'Aggregating tidy desk result')

        goal_handle.succeed()
        result = ExecuteTask.Result()
        result.success = True
        result.summary = 'Skill-oriented execution finished for tidy_desk'
        result.artifact_uris = manipulate_result.artifact_uris + inspect_result.image_uris
        result.error_code = ''

        self._publish_event(task_id, 'COMPLETED', 'DONE', 'Task completed successfully')
        self._publish_feedback(goal_handle, 'COMPLETED', 1.0, 'Task completed successfully')
        return result

    def _run_inspect_windows(self, goal_handle, task_id: str, task_payload: Dict[str, Any]) -> ExecuteTask.Result:
        self._publish_event(task_id, 'PLANNING', 'RUNNING', 'Building window inspection skill plan')
        self._publish_feedback(goal_handle, 'PLANNING', 0.1, 'Building window inspection skill plan')

        windows = task_payload.get('windows')
        if not isinstance(windows, list) or not windows:
            windows = ['window_1', 'window_2']

        collected_images: List[str] = []
        count = float(len(windows))

        for idx, window_id in enumerate(windows, start=1):
            progress_base = 0.12 + ((idx - 1) / count) * 0.72
            self._publish_event(task_id, 'NAVIGATING', 'RUNNING', f'Navigating to {window_id}')

            nav_goal = NavigateSkill.Goal()
            nav_goal.request_id = f'{task_id}-navigate-{idx}'
            nav_goal.target_type = 'window'
            nav_goal.location_id = str(window_id)
            nav_goal.pose_json = '{}'

            nav_result = self._call_skill(self._navigate_client, nav_goal, goal_handle, 'NAVIGATING', progress_base, 0.12 / count)
            if not nav_result.success:
                return self._fail_task(
                    goal_handle,
                    task_id,
                    'NAVIGATING',
                    nav_result.detail or f'Navigate skill failed at {window_id}',
                    'NAVIGATE_FAILED',
                )

            self._publish_event(task_id, 'INSPECTING', 'RUNNING', f'Inspecting {window_id}')
            inspect_goal = InspectSkill.Goal()
            inspect_goal.request_id = f'{task_id}-inspect-{idx}'
            inspect_goal.inspect_type = 'window_state_check'
            inspect_goal.target_id = str(window_id)
            inspect_goal.params_json = json.dumps(task_payload.get('inspect_params', {}))

            inspect_result = self._call_skill(self._inspect_client, inspect_goal, goal_handle, 'INSPECTING', progress_base + 0.12 / count, 0.12 / count)
            if not inspect_result.success:
                return self._fail_task(
                    goal_handle,
                    task_id,
                    'INSPECTING',
                    inspect_result.detail or f'Inspect skill failed at {window_id}',
                    'INSPECT_FAILED',
                )
            collected_images.extend(inspect_result.image_uris)

        self._publish_event(task_id, 'REPORTING', 'RUNNING', 'Aggregating window inspection report')
        self._publish_feedback(goal_handle, 'REPORTING', 0.95, 'Aggregating window inspection report')

        goal_handle.succeed()
        result = ExecuteTask.Result()
        result.success = True
        result.summary = f'Skill-oriented execution finished for inspect_windows ({len(windows)} windows)'
        result.artifact_uris = collected_images
        result.error_code = ''

        self._publish_event(task_id, 'COMPLETED', 'DONE', 'Task completed successfully')
        self._publish_feedback(goal_handle, 'COMPLETED', 1.0, 'Task completed successfully')
        return result

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        task_id = goal.task_id
        task_type = goal.task_type

        try:
            task_payload = json.loads(goal.task_json) if goal.task_json else {}
        except json.JSONDecodeError:
            task_payload = {}

        self.get_logger().info(f'Received task_id={task_id} task_type={task_type} payload={task_payload}')
        self._publish_event(task_id, 'RECEIVED', 'RUNNING', 'Task accepted by orchestrator')
        self._publish_feedback(goal_handle, 'RECEIVED', 0.02, 'Task accepted by orchestrator')

        if task_type == 'tidy_desk':
            return self._run_tidy_desk(goal_handle, task_id, task_payload)

        if task_type == 'inspect_windows':
            return self._run_inspect_windows(goal_handle, task_id, task_payload)

        return self._fail_task(
            goal_handle,
            task_id,
            'REJECTED',
            f'Unsupported task type: {task_type}',
            'UNSUPPORTED_TASK_TYPE',
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = OrchestratorNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.remove_node(node)
        node.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
