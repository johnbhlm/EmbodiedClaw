# EmbodiedClaw

EmbodiedClaw is an OpenClaw-powered assistant robot framework built on ROS 2.

It keeps high-level task understanding in OpenClaw, keeps execution on ROS 2, and keeps robot-specific logic inside robot adapters.

## Design Principles

- Capability abstraction must not bind to a specific robot.
- OpenClaw handles high-level understanding, clarification, orchestration, and reporting.
- ROS 2 is the unified bus.
- VLN and VLA are skill providers, not the planner.
- Robot-specific logic stays inside Robot Adapter.

## Canonical High-Level Skills

M2-beta freezes the agent-facing canonical v1 skill vocabulary:

- `observe`: scene/objects/state inspection.
- `move_forward`: short forward motion primitive.
- `navigate_to`: absolute or relative navigation target.
- `place_into`: put an item into target place/container/handover point.
- `pick`: pick an item.
- `toggle`: toggle a binary actuator/device state.
- `close`: close an object/device.
- `open`: open an object/device.
- `stop`: safe stop/cancel semantic.

> Left/right turn commands are represented as structured relative navigation tasks (`rotate_relative` -> `navigate_to(relative_pose=...)`), **not** as a separate canonical skill.

## OpenClaw Task Protocol

OpenClaw should emit structured tasks rather than low-level motion command strings.

### Example: `move_forward`

```json
{
  "task_id": "t1",
  "task_type": "move_forward",
  "task_payload": {"distance_m": 1.0}
}
```

### Example: `rotate_relative`

```json
{
  "task_id": "t2",
  "task_type": "rotate_relative",
  "task_payload": {"yaw_deg": 45}
}
```

### Example: `observe_scene`

```json
{
  "task_id": "t3",
  "task_type": "observe_scene",
  "task_payload": {"area": "desk_01"}
}
```

### Example: `bring_object`

```json
{
  "task_id": "t4",
  "task_type": "bring_object",
  "task_payload": {
    "object_name": "apple",
    "source_location": "dining_table",
    "recipient_location": "user_location"
  }
}
```

### Example: `tidy_desk`

```json
{
  "task_id": "t5",
  "task_type": "tidy_desk",
  "task_payload": {"area": "desk_01"}
}
```

### Example: `inspect_windows_and_lights`

```json
{
  "task_id": "t6",
  "task_type": "inspect_windows_and_lights",
  "task_payload": {
    "window_targets": ["window_01", "window_02"],
    "light_targets": ["light_01", "light_02"]
  }
}
```

## M2-beta Reasoning and Skill Routing

M2-beta introduces a lightweight structured tasking layer under `apps/tasking/`:

- `task_protocol.py` defines dataclass task/step schemas.
- `skill_vocab.py` freezes canonical skills and supported task types.
- `plan_builder.py` centralizes rule-based task decomposition.

The orchestrator is now **plan-driven**:

1. Parse incoming task goal into `TaskSpec`.
2. Build canonical skill plan through `PlanBuilder`.
3. Execute each `SkillStep` through a canonical skill router.

Skill routing:

- `observe` -> `/assistant/inspect_skill`
- `move_forward`, `navigate_to` -> `/assistant/navigate_skill`
- `pick`, `place_into`, `open`, `close`, `toggle` -> `/assistant/manipulate_skill`
- `stop` -> internal safe cancellation handling

Fake skill servers remain temporary providers for local testing.
Real VLN/VLA/SDK-backed adapters can later replace these servers without changing upper task interfaces (`POST /tasks`, `ExecuteTask`, canonical plans).

## Repository Layout

```text
EmbodiedClaw/
├── apps/
│   ├── bridge_api/
│   ├── openclaw_tools/
│   └── tasking/
├── ros2_ws/
│   └── src/
│       ├── embodiedclaw_msgs/
│       ├── embodiedclaw_orchestrator/
│       └── embodiedclaw_skill_servers/
├── tests/
└── README.md
```

## M2-beta Local Test

1. Install Python dependencies
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Build workspace
   ```bash
   cd ros2_ws
   source /opt/ros/humble/setup.bash
   colcon build --symlink-install
   source install/setup.bash
   ```
3. Run fake skill servers
   ```bash
   ros2 run embodiedclaw_skill_servers skill_launcher
   ```
4. Run orchestrator
   ```bash
   ros2 run embodiedclaw_orchestrator orchestrator_node
   ```
5. Run bridge API (new terminal)
   ```bash
   cd ..
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   uvicorn apps.bridge_api.server:app --host 0.0.0.0 --port 8000
   ```
6. Submit tasks
   ```bash
   # move_forward
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"move_forward","task_payload":{"distance_m":1.0}}'

   # observe_scene
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"observe_scene","task_payload":{"area":"desk_01"}}'

   # bring_object
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"bring_object","task_payload":{"object_name":"apple","source_location":"dining_table","recipient_location":"user_location"}}'

   # tidy_desk
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"tidy_desk","task_payload":{"area":"desk_01"}}'

   # inspect_windows_and_lights
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"inspect_windows_and_lights","task_payload":{"window_targets":["window_01"],"light_targets":["light_01"]}}'
   ```
7. Poll task status
   ```bash
   curl http://127.0.0.1:8000/tasks/<task_id>
   ```
8. Inspect ROS 2 actions
   ```bash
   cd ros2_ws
   source /opt/ros/humble/setup.bash
   source install/setup.bash
   ros2 action list
   ```
