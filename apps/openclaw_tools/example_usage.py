"""Tiny local usage example for the EmbodiedClaw HTTP client."""

from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient


if __name__ == "__main__":
    client = EmbodiedClawClient("http://127.0.0.1:8000")

    print(client.health())

    task = client.submit_robot_task("tidy_desk", {"area": "desk_01"})
    print(task)

    status = client.get_robot_task_status(task["task_id"])
    print(status)
