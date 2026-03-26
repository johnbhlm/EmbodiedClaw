import json
import threading
import uuid
from pathlib import Path
from dataclasses import asdict
from typing import Any, Dict

import rclpy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from apps.openclaw_bridge.openclaw_formatter import build_message_response, build_poll_response
from apps.reasoning import CommandInterpreter
from apps.reasoning.dispatch_contract import build_dispatch_response
from apps.providers.provider_config import get_camera_topic, get_observe_backend_name, get_observe_provider_name
from embodiedclaw_msgs.action import ExecuteTask
from embodiedclaw_msgs.msg import TaskEvent


CAMERA_STATUS_FILE = Path(__file__).resolve().parents[2] / 'runtime_artifacts' / 'observe_camera_status.json'

SUPPORTED_TASK_TYPES = {
    'move_forward',
    'rotate_relative',
    'navigate_to',
    'observe_scene',
    'list_objects_on_surface',
    'bring_object',
    'tidy_desk',
    'inspect_windows_and_lights',
    'inspect_windows',
    'stop_task',
}


class TaskCreateRequest(BaseModel):
    task_type: str = Field(..., description='Task type such as tidy_desk, bring_object, or inspect_windows_and_lights')
    task_payload: Dict[str, Any] = Field(default_factory=dict)


class InterpretRequest(BaseModel):
    command: str
    context: Dict[str, Any] = Field(default_factory=dict)


class OpenClawHandleMessageRequest(BaseModel):
    command: str
    context: Dict[str, Any] = Field(default_factory=dict)


class BridgeNode(Node):
    def __init__(self, state: Dict[str, Dict[str, Any]], lock: threading.Lock):
        super().__init__('embodiedclaw_bridge_api')
        self._state = state
        self._lock = lock
        self._goal_to_task: Dict[str, str] = {}
        self._action_client = ActionClient(self, ExecuteTask, '/assistant/execute_task')
        self._event_sub = self.create_subscription(TaskEvent, '/assistant/task_events', self._on_task_event, 50)

    def _on_task_event(self, msg: TaskEvent) -> None:
        with self._lock:
            task = self._state.setdefault(msg.task_id, _default_task_state(msg.task_id, 'unknown', {}))
            event = {
                'stage': msg.stage,
                'status': msg.status,
                'message': msg.message,
                'image_uri': msg.image_uri,
                'stamp': {'sec': msg.stamp.sec, 'nanosec': msg.stamp.nanosec},
            }
            task['latest_stage'] = msg.stage
            task['latest_status'] = msg.status
            task['events'].append(event)

    def submit_task(self, task_id: str, task_type: str, task_payload: Dict[str, Any]) -> None:
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            raise RuntimeError('Action server /assistant/execute_task is unavailable')

        goal = ExecuteTask.Goal()
        goal.task_id = task_id
        goal.task_type = task_type
        goal.task_json = json.dumps(task_payload)

        send_future = self._action_client.send_goal_async(goal, feedback_callback=self._feedback_callback)
        send_future.add_done_callback(lambda fut: self._goal_response_callback(task_id, fut))

    def _goal_response_callback(self, task_id: str, future) -> None:
        goal_handle = future.result()

        with self._lock:
            task = self._state.get(task_id)
            if task is None:
                return
            if not goal_handle.accepted:
                task['latest_status'] = 'REJECTED'
                task['final_result'] = {
                    'success': False,
                    'summary': 'Goal rejected by orchestrator',
                    'artifact_uris': [],
                    'error_code': 'REJECTED',
                }
                return

            self._goal_to_task[_goal_uuid_to_key(goal_handle.goal_id.uuid)] = task_id
            task['latest_status'] = 'ACCEPTED'

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda fut: self._result_callback(task_id, fut))

    def _feedback_callback(self, feedback_msg) -> None:
        fb = feedback_msg.feedback
        goal_key = _goal_uuid_to_key(feedback_msg.goal_id.uuid)

        with self._lock:
            task_id = self._goal_to_task.get(goal_key)
            if task_id is None:
                return
            task = self._state.get(task_id)
            if task is None:
                return

            task['latest_stage'] = fb.stage
            task['progress'] = fb.progress
            task['feedback'].append(
                {
                    'stage': fb.stage,
                    'progress': fb.progress,
                    'message': fb.message,
                    'image_uri': fb.image_uri,
                }
            )

    def _result_callback(self, task_id: str, future) -> None:
        result = future.result().result
        with self._lock:
            task = self._state.get(task_id)
            if task is None:
                return

            task['latest_status'] = 'SUCCEEDED' if result.success else 'FAILED'
            task['progress'] = 1.0
            task['final_result'] = {
                'success': result.success,
                'summary': result.summary,
                'artifact_uris': list(result.artifact_uris),
                'error_code': result.error_code,
            }


def _default_task_state(task_id: str, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'task_id': task_id,
        'task_type': task_type,
        'task_payload': payload,
        'latest_stage': 'CREATED',
        'latest_status': 'CREATED',
        'progress': 0.0,
        'events': [],
        'feedback': [],
        'final_result': None,
    }


def _goal_uuid_to_key(goal_uuid: Any) -> str:
    if isinstance(goal_uuid, bytes):
        return goal_uuid.hex()
    if isinstance(goal_uuid, (list, tuple)):
        return bytes(goal_uuid).hex()
    return str(goal_uuid)


def _normalize_image_uris(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _derive_task_images(task: Dict[str, Any], latest_feedback: Dict[str, Any], latest_event: Dict[str, Any]) -> tuple[list[str], str | None]:
    result = task.get('final_result')
    if isinstance(result, dict):
        artifact_uris = _normalize_image_uris(result.get('artifact_uris'))
        if artifact_uris:
            return artifact_uris, artifact_uris[0]

        image_uris = _normalize_image_uris(result.get('image_uris'))
        if image_uris:
            return image_uris, image_uris[0]

        primary = result.get('primary_image_uri')
        if isinstance(primary, str) and primary.strip():
            return [primary], primary

    latest_image_uri = latest_feedback.get('image_uri') or latest_event.get('image_uri') or ''
    if isinstance(latest_image_uri, str) and latest_image_uri.strip():
        return [latest_image_uri], latest_image_uri

    return [], None


app = FastAPI(title='EmbodiedClaw Bridge API', version='0.0.1')
_task_state: Dict[str, Dict[str, Any]] = {}
_task_state_lock = threading.Lock()
_bridge_node: BridgeNode | None = None
_executor: MultiThreadedExecutor | None = None
_spin_thread: threading.Thread | None = None
_interpreter = CommandInterpreter()


@app.on_event('startup')
def startup_event() -> None:
    global _bridge_node, _executor, _spin_thread
    if not rclpy.ok():
        rclpy.init(args=None)

    _bridge_node = BridgeNode(_task_state, _task_state_lock)
    _executor = MultiThreadedExecutor()
    _executor.add_node(_bridge_node)

    _spin_thread = threading.Thread(target=_executor.spin, daemon=True)
    _spin_thread.start()


@app.on_event('shutdown')
def shutdown_event() -> None:
    global _bridge_node, _executor, _spin_thread
    if _executor is not None and _bridge_node is not None:
        _executor.remove_node(_bridge_node)
        _bridge_node.destroy_node()
    if _executor is not None:
        _executor.shutdown()
    if _spin_thread is not None:
        _spin_thread.join(timeout=2.0)

    _bridge_node = None
    _executor = None
    _spin_thread = None

    if rclpy.ok():
        rclpy.shutdown()


@app.get('/health')
def health() -> Dict[str, str]:
    return {'status': 'ok'}




@app.get('/camera_status')
def camera_status() -> Dict[str, Any]:
    status = {
        'observe_provider': get_observe_provider_name(),
        'camera_topic': get_camera_topic(),
        'observe_backend': get_observe_backend_name(),
        'has_recent_frame': False,
        'latest_frame_age_sec': None,
    }

    if CAMERA_STATUS_FILE.exists():
        try:
            persisted = json.loads(CAMERA_STATUS_FILE.read_text(encoding='utf-8'))
            if isinstance(persisted, dict):
                status.update(persisted)
        except (OSError, json.JSONDecodeError):
            pass
    return status

@app.post('/tasks')
def create_task(request: TaskCreateRequest) -> Dict[str, Any]:
    return _create_task_internal(request.task_type, request.task_payload)


def _create_task_internal(task_type: str, task_payload: Dict[str, Any]) -> Dict[str, Any]:
    if _bridge_node is None:
        raise HTTPException(status_code=500, detail='Bridge node is not initialized')

    if task_type not in SUPPORTED_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f'Unsupported task_type: {task_type}')

    task_id = str(uuid.uuid4())
    with _task_state_lock:
        _task_state[task_id] = _default_task_state(task_id, task_type, task_payload)

    try:
        _bridge_node.submit_task(task_id, task_type, task_payload)
    except RuntimeError as exc:
        with _task_state_lock:
            _task_state[task_id]['latest_status'] = 'FAILED_TO_SUBMIT'
            _task_state[task_id]['final_result'] = {
                'success': False,
                'summary': str(exc),
                'artifact_uris': [],
                'error_code': 'ACTION_SERVER_UNAVAILABLE',
            }

    return {'task_id': task_id}


@app.get('/tasks/{task_id}')
def get_task(task_id: str) -> Dict[str, Any]:
    with _task_state_lock:
        task = _task_state.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail='Task not found')
        return task


@app.post('/interpret')
def interpret_command(request: InterpretRequest) -> Dict[str, Any]:
    result = _interpreter.interpret(request.command, request.context)
    return result.to_dict()


def _build_dispatch_for_command(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    interpretation = _interpreter.interpret(command, context)
    return build_dispatch_response(interpretation, _create_task_internal)


@app.post('/dispatch_command')
def dispatch_command(request: InterpretRequest) -> Dict[str, Any]:
    try:
        return _build_dispatch_for_command(request.command, request.context)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post('/chat_command')
def chat_command(request: InterpretRequest) -> Dict[str, Any]:
    try:
        dispatch_result = _build_dispatch_for_command(request.command, request.context)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    interpretation = dispatch_result.get('interpretation', {})
    status = interpretation.get('status')
    if status in {'clarification_needed', 'scheduled_task', 'unsupported'}:
        return {'interpretation': interpretation, 'dispatch': None, 'task_id': None}

    task_submission = dispatch_result.get('task_submission') or {}
    return {
        'interpretation': interpretation,
        'dispatch': task_submission,
        'task_id': task_submission.get('task_id'),
    }


@app.get('/task_summary/{task_id}')
def get_task_summary(task_id: str) -> Dict[str, Any]:
    with _task_state_lock:
        task = _task_state.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail='Task not found')

        events = task.get('events', [])
        feedback = task.get('feedback', [])
        latest_event = events[-1] if events else {}
        latest_feedback = feedback[-1] if feedback else {}
        image_uris, primary_image_uri = _derive_task_images(task, latest_feedback, latest_event)

        result = task.get('final_result')
        final_status = task.get('latest_status')
        return {
            'task_id': task_id,
            'task_type': task.get('task_type'),
            'final_status': final_status,
            'progress': task.get('progress', 0.0),
            'latest_stage': task.get('latest_stage'),
            'latest_status': task.get('latest_status'),
            'latest_message': latest_feedback.get('message') or latest_event.get('message') or '',
            'latest_image_uri': latest_feedback.get('image_uri') or latest_event.get('image_uri') or '',
            'image_uris': image_uris,
            'primary_image_uri': primary_image_uri,
            'result': result,
        }


@app.post('/openclaw/handle_message')
def openclaw_handle_message(request: OpenClawHandleMessageRequest) -> Dict[str, Any]:
    chat_result = chat_command(InterpretRequest(command=request.command, context=request.context))
    return asdict(build_message_response(chat_result))


@app.get('/openclaw/poll_task/{task_id}')
def openclaw_poll_task(task_id: str) -> Dict[str, Any]:
    summary = get_task_summary(task_id)
    return asdict(build_poll_response(summary))
