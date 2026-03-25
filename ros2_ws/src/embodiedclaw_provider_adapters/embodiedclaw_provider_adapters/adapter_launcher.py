import rclpy
from rclpy.executors import MultiThreadedExecutor

from embodiedclaw_provider_adapters.navigate_adapter_server import NavigateAdapterServer
from embodiedclaw_provider_adapters.observe_adapter_server import ObserveAdapterServer


def main(args=None) -> None:
    rclpy.init(args=args)

    observe_server = ObserveAdapterServer()
    navigate_server = NavigateAdapterServer()

    executor = MultiThreadedExecutor()
    executor.add_node(observe_server)
    executor.add_node(navigate_server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.remove_node(observe_server)
        executor.remove_node(navigate_server)
        observe_server.destroy_node()
        navigate_server.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
