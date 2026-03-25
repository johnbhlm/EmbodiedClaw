# EmbodiedClaw

EmbodiedClaw is an **OpenClaw-powered, ROS2-based, skill-oriented embodied assistant framework**.

It keeps high-level task understanding in OpenClaw, executes through ROS2, and isolates robot-specific logic in adapters/providers.

## Design Principles

- Capability abstraction must not bind to a specific robot.
- OpenClaw handles high-level understanding, clarification, orchestration, and reporting.
- ROS2 is the unified bus.
- VLN and VLA are skill providers, not the planner.
- Robot-specific logic stays inside Robot Adapter or provider implementations.

## Canonical High-Level Skills

Canonical v1 skill vocabulary:

- `observe`: scene/objects/state inspection.
- `move_forward`: short forward motion primitive.
- `navigate_to`: absolute or relative navigation target.
- `place_into`: put an item into target place/container/handover point.
- `pick`: pick an item.
- `toggle`: toggle a binary actuator/device state.
- `close`: close an object/device.
- `open`: open an object/device.
- `stop`: safe stop/cancel semantic.

> Rotation commands are represented as structured relative navigation tasks (`rotate_relative` -> `navigate_to(relative_pose=...)`), not as a separate canonical skill.

## Provider-Oriented Execution

M3-alpha introduces a provider-oriented execution layer for **observe** and **navigate**:

- Canonical skills remain stable at the orchestrator/task interface.
- `observe` and `move_forward` / `navigate_to` are delegated through ROS2 provider adapters.
- Fake providers are still the default so local E2E flows continue working without camera/VLN/runtime dependencies.
- Future camera/VLN/SDK-backed providers can be plugged in behind the same adapters without changing upper task interfaces (`POST /tasks`, `ExecuteTask`, canonical plans).

Current routing:

- `observe` -> `/assistant/inspect_skill` (served by `embodiedclaw_provider_adapters`)
- `move_forward`, `navigate_to` -> `/assistant/navigate_skill` (served by `embodiedclaw_provider_adapters`)
- `pick`, `place_into`, `open`, `close`, `toggle` -> `/assistant/manipulate_skill` (served by `embodiedclaw_skill_servers` fake manipulate server)
- `stop` -> internal orchestrator handling

## Provider Layer

`apps/providers/` defines provider interfaces + implementations:

- `ObserveProvider` and `NavigateProvider` interfaces
- deterministic fake defaults (`FakeObserveProvider`, `FakeNavigateProvider`)
- factory-based selection through environment variables:
  - `EMBODIEDCLAW_OBSERVE_PROVIDER`
  - `EMBODIEDCLAW_NAVIGATE_PROVIDER`

Both variables default to `fake`.

M3-alpha also includes explicit placeholder skeletons for upcoming providers:

- `CameraObserveProvider` (future real camera/VLA integration)
- `UnitreeSDKNavigateProvider` (future VLN/SDK adapter-backed motion)

## Repository Layout

```text
EmbodiedClaw/
├── apps/
│   ├── bridge_api/
│   ├── openclaw_tools/
│   ├── providers/
│   └── tasking/
├── ros2_ws/
│   └── src/
│       ├── embodiedclaw_msgs/
│       ├── embodiedclaw_orchestrator/
│       ├── embodiedclaw_provider_adapters/
│       └── embodiedclaw_skill_servers/
├── tests/
└── README.md
```

## M3-alpha Local Test

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
3. Run provider adapter launcher (observe + navigate)
   ```bash
   ros2 run embodiedclaw_provider_adapters adapter_launcher
   ```
4. Run fake manipulate server (new terminal)
   ```bash
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   ros2 run embodiedclaw_skill_servers fake_manipulate_server
   ```
5. Run orchestrator (new terminal)
   ```bash
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   ros2 run embodiedclaw_orchestrator orchestrator_node
   ```
6. Run bridge API (new terminal)
   ```bash
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   uvicorn apps.bridge_api.server:app --host 0.0.0.0 --port 8000
   ```
7. Submit tasks
   ```bash
   # observe_scene
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"observe_scene","task_payload":{"area":"desk_01"}}'

   # list_objects_on_surface
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"list_objects_on_surface","task_payload":{"surface":"desk_01"}}'

   # move_forward
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"move_forward","task_payload":{"distance_m":1.0}}'

   # rotate_relative
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"rotate_relative","task_payload":{"yaw_deg":45}}'

   # bring_object
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"bring_object","task_payload":{"object_name":"apple","source_location":"dining_table","recipient_location":"user_location"}}'

   # inspect_windows_and_lights
   curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"task_type":"inspect_windows_and_lights","task_payload":{"window_targets":["window_01"],"light_targets":["light_01"]}}'
   ```
8. Poll task status
   ```bash
   curl http://127.0.0.1:8000/tasks/<task_id>
   ```
9. Inspect ROS2 action list
   ```bash
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   ros2 action list
   ```

## Roadmap

- **M3-alpha**: provider abstraction and provider-backed adapter execution for observe/navigate.
- **Next milestone**: replace fake providers with real camera/VLN/SDK-backed providers while preserving canonical skill + task interfaces.
