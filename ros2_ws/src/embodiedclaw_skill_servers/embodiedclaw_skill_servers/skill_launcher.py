import rclpy
from rclpy.executors import MultiThreadedExecutor

from embodiedclaw_skill_servers.fake_inspect_server import FakeInspectSkillServer
from embodiedclaw_skill_servers.fake_manipulate_server import FakeManipulateSkillServer
from embodiedclaw_skill_servers.fake_navigate_server import FakeNavigateSkillServer


def main(args=None) -> None:
    rclpy.init(args=args)

    navigate_server = FakeNavigateSkillServer()
    manipulate_server = FakeManipulateSkillServer()
    inspect_server = FakeInspectSkillServer()

    executor = MultiThreadedExecutor()
    executor.add_node(navigate_server)
    executor.add_node(manipulate_server)
    executor.add_node(inspect_server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.remove_node(navigate_server)
        executor.remove_node(manipulate_server)
        executor.remove_node(inspect_server)
        navigate_server.destroy_node()
        manipulate_server.destroy_node()
        inspect_server.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
