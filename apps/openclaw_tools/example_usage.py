"""Tiny local usage example for the EmbodiedClaw HTTP client."""

from __future__ import annotations

import time

from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient


if __name__ == "__main__":
    client = EmbodiedClawClient("http://127.0.0.1:8000")

    health_result = client.health()
    print("health:", health_result)

    handle_result = client.openclaw_handle_message("往前走一米")
    print("assistant:", handle_result.get("reply_text", ""))

    task_id = handle_result.get("task_id")
    if handle_result.get("needs_polling") and task_id:
        for _ in range(5):
            summary = client.openclaw_poll_task(task_id)
            print("assistant:", summary.get("reply_text", ""))
            if summary.get("terminal"):
                break
            time.sleep(1.0)
