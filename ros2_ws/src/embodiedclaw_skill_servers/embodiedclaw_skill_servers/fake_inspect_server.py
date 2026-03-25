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
            time.sleep(0.25)

        goal_handle.succeed()
        result = InspectSkill.Result()
        result.success = True
        result.finding = f'Inspection OK for {goal.target_id or "target"}'
        result.image_uris = [
            'mock://images/inspect_1.jpg',
            'mock://images/inspect_2.jpg',
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
