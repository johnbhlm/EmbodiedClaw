import json
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from embodiedclaw_msgs.action import InspectSkill


class FakeInspectSkillServer(Node):
    def __init__(self) -> None:
        super().__init__('fake_inspect_skill_server')
        self._action_server = ActionServer(
            self,
            InspectSkill,
            '/assistant/inspect_skill',
            execute_callback=self.execute_callback,
        )
        self.get_logger().info('Fake inspect skill server ready.')

    def execute_callback(self, goal_handle):
        goal = goal_handle.request
        self.get_logger().info(
            f'Inspect request_id={goal.request_id} inspect_type={goal.inspect_type} '
            f'target_id={goal.target_id}'
        )

        for phase, progress, message, image_uri in [
            ('STARTED', 0.2, 'Inspection request accepted', ''),
            ('SCANNING', 0.55, 'Capturing visual evidence', 'mock://images/inspect_scan.jpg'),
            ('ANALYZING', 0.9, 'Analyzing inspection result', 'mock://images/inspect_analysis.jpg'),
        ]:
            feedback = InspectSkill.Feedback()
            feedback.phase = phase
            feedback.progress = progress
            feedback.message = message
            feedback.image_uri = image_uri
            goal_handle.publish_feedback(feedback)
            time.sleep(0.2)

        params = {}
        if goal.params_json:
            try:
                params = json.loads(goal.params_json)
            except json.JSONDecodeError:
                params = {}

        inspect_type = goal.inspect_type or 'scene_summary'
        target_id = goal.target_id or params.get('target', 'target')

        if inspect_type == 'scene_summary':
            finding = {'summary': 'table and chair visible'}
        elif inspect_type == 'object_list':
            finding = {'objects': ['apple', 'cup', 'book']}
        elif inspect_type == 'object_existence':
            object_name = str(params.get('object_name', 'apple'))
            finding = {'object_name': object_name, 'exists': object_name.lower() != 'missing_object'}
        elif inspect_type == 'verify_surface':
            finding = {'tidy': True}
        elif inspect_type == 'window_state':
            finding = {'target_id': target_id, 'closed': True}
        elif inspect_type == 'light_state':
            finding = {'target_id': target_id, 'off': True}
        else:
            finding = {'summary': f'unsupported inspect_type={inspect_type}, fallback success'}

        goal_handle.succeed()
        result = InspectSkill.Result()
        result.success = True
        result.finding = json.dumps(finding)
        result.image_uris = [
            f'mock://images/{inspect_type}_{target_id}_1.jpg',
            f'mock://images/{inspect_type}_{target_id}_2.jpg',
        ]
        return result


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FakeInspectSkillServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
