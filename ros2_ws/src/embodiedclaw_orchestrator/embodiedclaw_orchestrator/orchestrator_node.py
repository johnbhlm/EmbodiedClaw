import json
import time
from typing import Dict, List, Tuple

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import ExecuteTask
from embodiedclaw_msgs.msg import TaskEvent


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
        self.get_logger().info('EmbodiedClaw orchestrator started.')

    def _plan_for_task(self, task_type: str) -> List[Tuple[str, str]]:
        plans: Dict[str, List[Tuple[str, str]]] = {
            'tidy_desk': [
                ('RECEIVED', 'Task accepted by orchestrator'),
                ('PLANNING', 'Building tidy desk execution plan'),
                ('NAVIGATING', 'Navigating to target area'),
                ('PERCEIVING', 'Scanning desk for objects'),
                ('MANIPULATING', 'Performing tidy operation'),
                ('VERIFYING', 'Verifying desk condition'),
                ('REPORTING', 'Preparing task summary'),
                ('COMPLETED', 'Task completed successfully'),
            ],
            'inspect_windows': [
                ('RECEIVED', 'Task accepted by orchestrator'),
                ('PLANNING', 'Building window inspection plan'),
                ('NAVIGATING', 'Navigating inspection points'),
                ('INSPECTING', 'Inspecting windows and recording status'),
                ('REPORTING', 'Preparing inspection report'),
                ('COMPLETED', 'Task completed successfully'),
            ],
        }
        return plans.get(task_type, [
            ('RECEIVED', 'Task accepted by orchestrator'),
            ('PLANNING', 'Building generic execution plan'),
            ('REPORTING', 'Preparing fallback summary'),
            ('COMPLETED', 'Task completed successfully'),
        ])

    def _publish_event(self, task_id: str, stage: str, status: str, message: str, image_uri: str = '') -> None:
        event = TaskEvent()
        event.task_id = task_id
        event.stage = stage
        event.status = status
        event.message = message
        event.image_uri = image_uri
        event.stamp = self.get_clock().now().to_msg()
        self.event_publisher.publish(event)

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        task_id = goal.task_id
        task_type = goal.task_type

        try:
            task_payload = json.loads(goal.task_json) if goal.task_json else {}
        except json.JSONDecodeError:
            task_payload = {}

        self.get_logger().info(f'Received task_id={task_id} task_type={task_type} payload={task_payload}')

        steps = self._plan_for_task(task_type)
        total = len(steps)

        for index, (stage, message) in enumerate(steps, start=1):
            progress = float(index) / float(total)
            status = 'DONE' if stage == 'COMPLETED' else 'RUNNING'

            self._publish_event(task_id, stage, status, message)

            feedback = ExecuteTask.Feedback()
            feedback.stage = stage
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = ''
            goal_handle.publish_feedback(feedback)

            time.sleep(0.4)

        goal_handle.succeed()

        result = ExecuteTask.Result()
        result.success = True
        result.summary = f'Fake execution finished for task_type={task_type}'
        result.artifact_uris = []
        result.error_code = ''

        self.get_logger().info(f'Finished task_id={task_id} task_type={task_type}')
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = OrchestratorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
