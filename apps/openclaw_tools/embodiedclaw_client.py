"""Minimal HTTP client for calling EmbodiedClaw bridge APIs."""

from __future__ import annotations

from typing import Any

import requests


class EmbodiedClawClient:
    """Lightweight client for EmbodiedClaw HTTP bridge endpoints."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        """GET /health."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def submit_robot_task(self, task_type: str, task_payload: dict[str, Any]) -> dict[str, Any]:
        """POST /tasks with task_type and task_payload."""
        payload = {
            "task_type": task_type,
            "task_payload": task_payload,
        }
        response = requests.post(f"{self.base_url}/tasks", json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def get_robot_task_status(self, task_id: str) -> dict[str, Any]:
        """GET /tasks/{task_id}."""
        response = requests.get(f"{self.base_url}/tasks/{task_id}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def interpret_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST /interpret for deterministic command-to-task interpretation."""
        payload = {'command': command, 'context': context or {}}
        response = requests.post(f"{self.base_url}/interpret", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def dispatch_command(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST /dispatch_command to interpret command then submit executable task."""
        payload = {'command': command, 'context': context or {}}
        response = requests.post(f"{self.base_url}/dispatch_command", json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
