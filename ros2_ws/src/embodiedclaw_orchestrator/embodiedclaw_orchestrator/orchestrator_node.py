import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sys

import rclpy
from rclpy.action import ActionClient, ActionServer
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from embodiedclaw_msgs.action import ExecuteTask, InspectSkill, ManipulateSkill, NavigateSkill
from embodiedclaw_msgs.msg import TaskEvent

REPO_ROOT = Path(__file__).resolve().parents[4]
APPS_DIR = REPO_ROOT / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))

from tasking import PlanBuilder, SkillStep, TaskSpec
from tasking.skill_vocab import CanonicalSkill, TaskType


@dataclass
class SkillCallResult:
    success: bool
    detail: str
    artifact_uris: list[str]
    image_uris: list[str]


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
        self._plan_builder = PlanBuilder()
        self.get_logger().info('EmbodiedClaw orchestrator started (M2-beta plan-driven).')

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

    def _call_skill(
        self,
        client: ActionClient,
        goal_msg: Any,
        goal_handle,
        stage: str,
        progress_base: float,
        progress_span: float,
    ) -> SkillCallResult:
        if not client.wait_for_server(timeout_sec=2.0):
            return SkillCallResult(False, f'Skill action unavailable for stage {stage}', [], [])

        done_event = threading.Event()
        state: dict[str, Any] = {}

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

    def _fail_task(
        self,
        goal_handle,
        task_id: str,
        stage: str,
        message: str,
        error_code: str,
        artifact_uris: list[str] | None = None,
    ):
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

    def _parse_task_spec(self, goal) -> TaskSpec:
        try:
            payload = json.loads(goal.task_json) if goal.task_json else {}
        except json.JSONDecodeError:
            payload = {}

        task_type = goal.task_type
        if task_type == 'inspect_windows':
            task_type = TaskType.INSPECT_WINDOWS_AND_LIGHTS
            payload = {
                'window_targets': payload.get('windows', []),
                'light_targets': payload.get('light_targets', []),
            }

        metadata = {'source': 'execute_task_action'}
        return TaskSpec(
            task_id=goal.task_id,
            task_type=task_type,
            task_payload=payload,
            metadata=metadata,
        )

    def _stage_for_step(self, step: SkillStep) -> str:
        if step.skill_name == CanonicalSkill.OBSERVE and step.params.get('mode') == 'verify_surface':
            return 'VERIFYING'
        if step.skill_name == CanonicalSkill.OBSERVE:
            return 'EXECUTING'
        if step.skill_name == CanonicalSkill.STOP:
            return 'CANCELLED'
        return 'EXECUTING'

    def execute_canonical_skill(
        self,
        task_id: str,
        goal_handle,
        step: SkillStep,
        progress_base: float,
        progress_span: float,
    ) -> SkillCallResult:
        skill_name = step.skill_name
        params = step.params
        stage = self._stage_for_step(step)

        if skill_name == CanonicalSkill.OBSERVE:
            endpoint = '/assistant/inspect_skill'
            self.get_logger().info(f'Canonical skill={skill_name} routed to {endpoint} (provider adapter).')
            goal_msg = InspectSkill.Goal()
            goal_msg.request_id = f'{task_id}-observe'
            goal_msg.inspect_type = str(params.get('mode', 'scene_summary'))
            goal_msg.target_id = str(params.get('target', ''))
            goal_msg.params_json = json.dumps(params)
            return self._call_skill(self._inspect_client, goal_msg, goal_handle, stage, progress_base, progress_span)

        if skill_name in {CanonicalSkill.MOVE_FORWARD, CanonicalSkill.NAVIGATE_TO}:
            endpoint = '/assistant/navigate_skill'
            self.get_logger().info(f'Canonical skill={skill_name} routed to {endpoint} (provider adapter).')
            goal_msg = NavigateSkill.Goal()
            goal_msg.request_id = f'{task_id}-{skill_name}'
            goal_msg.target_type = 'relative' if 'relative_pose' in params else 'location'
            goal_msg.location_id = str(params.get('location_id', ''))
            if skill_name == CanonicalSkill.MOVE_FORWARD:
                goal_msg.pose_json = json.dumps({'move_forward': {'distance_m': float(params.get('distance_m', 0.5))}})
            else:
                goal_msg.pose_json = json.dumps(params.get('relative_pose', params.get('pose', {})))
            return self._call_skill(self._navigate_client, goal_msg, goal_handle, stage, progress_base, progress_span)

        if skill_name in {
            CanonicalSkill.PICK,
            CanonicalSkill.PLACE_INTO,
            CanonicalSkill.OPEN,
            CanonicalSkill.CLOSE,
            CanonicalSkill.TOGGLE,
        }:
            endpoint = '/assistant/manipulate_skill'
            self.get_logger().info(f'Canonical skill={skill_name} routed to {endpoint} (fake manipulate server).')
            goal_msg = ManipulateSkill.Goal()
            goal_msg.request_id = f'{task_id}-{skill_name}'
            goal_msg.skill_name = skill_name
            goal_msg.target_object = str(params.get('object_name', params.get('target', '')))
            goal_msg.target_place = str(params.get('target', params.get('location_id', '')))
            goal_msg.params_json = json.dumps(params)
            return self._call_skill(self._manipulate_client, goal_msg, goal_handle, stage, progress_base, progress_span)

        if skill_name == CanonicalSkill.STOP:
            self.get_logger().info('Canonical skill=stop handled internally by orchestrator.')
            return SkillCallResult(True, 'stop_requested', [], [])

        return SkillCallResult(False, f'Unsupported canonical skill: {skill_name}', [], [])

    def execute_callback(self, goal_handle):
        task_spec = self._parse_task_spec(goal_handle.request)
        task_id = task_spec.task_id
        task_type = task_spec.task_type

        self.get_logger().info(
            f'Received task_id={task_id} task_type={task_type} payload={task_spec.task_payload}'
        )
        self._publish_event(task_id, 'RECEIVED', 'RUNNING', 'Task accepted by orchestrator')
        self._publish_feedback(goal_handle, 'RECEIVED', 0.02, 'Task accepted by orchestrator')

        self._publish_event(task_id, 'PLANNING', 'RUNNING', 'Building canonical skill plan')
        self._publish_feedback(goal_handle, 'PLANNING', 0.08, 'Building canonical skill plan')

        try:
            plan = self._plan_builder.build(task_spec)
        except ValueError as exc:
            return self._fail_task(goal_handle, task_id, 'PLANNING', str(exc), 'UNSUPPORTED_TASK_TYPE')

        if not plan:
            return self._fail_task(goal_handle, task_id, 'PLANNING', 'Planner produced an empty plan', 'EMPTY_PLAN')

        artifact_uris: list[str] = []
        result_summary = f'Plan executed for {task_type}'
        total_steps = len(plan)

        for idx, step in enumerate(plan, start=1):
            progress_base = 0.1 + ((idx - 1) / total_steps) * 0.8
            progress_span = 0.8 / total_steps
            stage = self._stage_for_step(step)
            self._publish_event(task_id, stage, 'RUNNING', f'Executing {step.skill_name}: {step.description}')

            if task_type == TaskType.BRING_OBJECT and 'recipient_location_gate' in step.labels:
                recipient = str(task_spec.task_payload.get('recipient_location', '')).strip()
                if not recipient:
                    return self._fail_task(
                        goal_handle,
                        task_id,
                        'EXECUTING',
                        'recipient_location_required',
                        'RECIPIENT_LOCATION_REQUIRED',
                        artifact_uris=artifact_uris,
                    )

            call_result = self.execute_canonical_skill(task_id, goal_handle, step, progress_base, progress_span)
            artifact_uris.extend(call_result.artifact_uris)
            artifact_uris.extend(call_result.image_uris)
            if not call_result.success:
                return self._fail_task(
                    goal_handle,
                    task_id,
                    stage,
                    call_result.detail or f'Canonical skill failed: {step.skill_name}',
                    'SKILL_EXECUTION_FAILED',
                    artifact_uris=artifact_uris,
                )

            if task_type == TaskType.BRING_OBJECT and 'object_existence_gate' in step.labels:
                finding_data: dict[str, Any]
                try:
                    finding_data = json.loads(call_result.detail) if call_result.detail else {}
                except json.JSONDecodeError:
                    finding_data = {}
                if finding_data.get('exists') is False:
                    return self._fail_task(
                        goal_handle,
                        task_id,
                        'EXECUTING',
                        'object_not_found',
                        'OBJECT_NOT_FOUND',
                        artifact_uris=artifact_uris,
                    )

            if step.skill_name == CanonicalSkill.STOP:
                self._publish_event(task_id, 'CANCELLED', 'CANCELLED', 'Task stopped by stop_task plan step')
                self._publish_feedback(goal_handle, 'CANCELLED', 1.0, 'Task cancelled safely')
                goal_handle.canceled()
                result = ExecuteTask.Result()
                result.success = False
                result.summary = 'Task cancelled via stop_task'
                result.artifact_uris = artifact_uris
                result.error_code = 'TASK_CANCELLED'
                return result

        self._publish_event(task_id, 'REPORTING', 'RUNNING', 'Aggregating execution report')
        self._publish_feedback(goal_handle, 'REPORTING', 0.95, 'Aggregating execution report')

        goal_handle.succeed()
        result = ExecuteTask.Result()
        result.success = True
        result.summary = result_summary
        result.artifact_uris = artifact_uris
        result.error_code = ''

        self._publish_event(task_id, 'COMPLETED', 'DONE', 'Task completed successfully')
        self._publish_feedback(goal_handle, 'COMPLETED', 1.0, 'Task completed successfully')
        return result


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
