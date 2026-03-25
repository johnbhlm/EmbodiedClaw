"""Tiny local usage example for the EmbodiedClaw HTTP client."""

from __future__ import annotations

import time

from apps.openclaw_tools.embodiedclaw_client import EmbodiedClawClient


if __name__ == "__main__":
    client = EmbodiedClawClient("http://127.0.0.1:8000")

    health_result = client.health()
    print("health:", health_result)

    chat_result = client.chat_command("往前走一米")
    print("chat_command:", chat_result)

    task_id = chat_result.get("task_id")
    if task_id:
        for _ in range(3):
            summary = client.get_task_summary(task_id)
            print("task_summary:", summary)
            if summary.get("final_status") in {"SUCCEEDED", "FAILED", "FAILED_TO_SUBMIT", "REJECTED"}:
                break
            time.sleep(1.0)
