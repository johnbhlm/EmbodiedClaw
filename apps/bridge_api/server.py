import json
import threading
import uuid
from typing import Any, Dict

import rclpy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from apps.reasoning import CommandInterpreter
from apps.reasoning.dispatch_contract import build_dispatch_response
from embodiedclaw_msgs.action import ExecuteTask
from embodiedclaw_msgs.msg import TaskEvent

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


@app.post('/dispatch_command')
def dispatch_command(request: InterpretRequest) -> Dict[str, Any]:
    result = _interpreter.interpret(request.command, request.context)
    try:
        return build_dispatch_response(result, _create_task_internal)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
