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

## OpenClaw Command Contract

M3-beta adds a deterministic command interpretation contract for demo natural-language commands:

- OpenClaw should still emit structured tasks whenever possible.
- EmbodiedClaw now provides an explicit command interpretation + clarification layer for integration stability.
- This layer is intentionally minimal and rule-based for demos/testing; it is **not** a replacement for full OpenClaw reasoning/planning.

The interpretation layer returns `InterpretationResult` with statuses:

- `executable`
- `clarification_needed`
- `unsupported`
- `scheduled_task`

## Supported Demo Commands

- `往前走一米` -> `move_forward`
- `左转45度` / `右转45度` -> `rotate_relative`
- `你看到了什么` -> `observe_scene`
- `桌子上都有什么` -> `list_objects_on_surface` (needs `surface_id` context)
- `收拾一下桌子` -> `tidy_desk` (needs `area`/`surface_id` context)
- `将餐桌上苹果给我` -> `bring_object` (needs `recipient_location` context)
- `每天晚上九点巡检窗户和灯是否关闭` -> `inspect_windows_and_lights` with daily `21:00` schedule metadata
- `停止` -> `stop_task`

## M3-beta Interpretation and Dispatch

Bridge API now includes:

- `POST /interpret`: converts `command` + optional `context` to `InterpretationResult`.
- `POST /dispatch_command`: interprets first, then:
  - auto-submits only when status is `executable`;
  - returns interpretation only for `clarification_needed`, `scheduled_task`, `unsupported`.

`/tasks` and `/tasks/{task_id}` behavior is unchanged.

## M2-beta Reasoning and Skill Routing

- `CameraObserveProvider` (future real camera/VLA integration)
- `UnitreeSDKNavigateProvider` (future VLN/SDK adapter-backed motion)

## Repository Layout

```text
EmbodiedClaw/
├── apps/
│   ├── bridge_api/
│   ├── openclaw_tools/
│   ├── reasoning/
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

## M3-beta Local Test

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
3. Run provider adapter launcher (skill servers for M3-alpha/M3-beta local fake providers)
   ```bash
   ros2 run embodiedclaw_provider_adapters adapter_launcher
   ```
4. (Optional if separate in your setup) run fake manipulate server
   ```bash
   ros2 run embodiedclaw_skill_servers fake_manipulate_server
   ```
5. Run orchestrator
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
7. Test command interpretation endpoints
   ```bash
   # interpret move_forward
   curl -X POST http://127.0.0.1:8000/interpret -H "Content-Type: application/json" -d '{"command":"往前走一米","context":{}}'

   # interpret bring_object (clarification expected if recipient_location missing)
   curl -X POST http://127.0.0.1:8000/interpret -H "Content-Type: application/json" -d '{"command":"将餐桌上苹果给我","context":{}}'

   # dispatch observe_scene
   curl -X POST http://127.0.0.1:8000/dispatch_command -H "Content-Type: application/json" -d '{"command":"你看到了什么","context":{}}'

   # dispatch move_forward
   curl -X POST http://127.0.0.1:8000/dispatch_command -H "Content-Type: application/json" -d '{"command":"往前走一米","context":{}}'

   # interpret scheduled inspection
   curl -X POST http://127.0.0.1:8000/interpret -H "Content-Type: application/json" -d '{"command":"每天晚上九点巡检窗户和灯是否关闭","context":{}}'
   ```
8. Poll task status
   ```bash
   curl http://127.0.0.1:8000/tasks/<task_id>
   ```
9. Inspect ROS 2 actions
   ```bash
   source /opt/ros/humble/setup.bash
   source ros2_ws/install/setup.bash
   ros2 action list
   ```

## Roadmap

- **M3-alpha**: provider abstraction and provider-backed adapter execution for observe/navigate.
- **Next milestone**: replace fake providers with real camera/VLN/SDK-backed providers while preserving canonical skill + task interfaces.
