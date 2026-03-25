"""Tiny local usage example for the EmbodiedClaw HTTP client."""

from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient


if __name__ == "__main__":
    client = EmbodiedClawClient("http://127.0.0.1:8000")

    health_result = client.health()
    print("health:", health_result)

    interpret_result = client.interpret_command("往前走一米")
    print("interpret_command:", interpret_result)

    dispatch_result = client.dispatch_command("你看到了什么")
    print("dispatch_command:", dispatch_result)
