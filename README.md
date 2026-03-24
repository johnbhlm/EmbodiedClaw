# EmbodiedClaw

EmbodiedClaw is an OpenClaw-powered assistant robot framework built on ROS 2.

It is designed for assistant robot demos that support:
- Feishu text/voice task interaction
- task orchestration with OpenClaw
- ROS 2 as the unified communication bus
- skill-based execution
- VLN as navigation skill provider
- VLA as manipulation skill provider
- robot-agnostic capability abstraction
- progressive iteration from wheel-based humanoid robots to humanoid platforms such as G1

## Design Principles

- Capability abstraction must not bind to a specific robot.
- VLN and VLA are treated as skill providers.
- OpenClaw handles task understanding, clarification, orchestration, and reporting.
- ROS 2 is the unified bus.
- Robot-specific logic must stay inside Robot Adapter.
- Execution must be observable, interruptible, recoverable, and replayable.

## Target Demo Scenarios

### 1. Tidy desk
A user sends a Feishu message such as:

> 收拾一下桌子

Expected system behavior:
- OpenClaw understands and structures the task
- Mission Orchestrator builds a task graph
- robot navigates to target desk
- perception scans desk
- VLA skill performs pick/place or tidy operations
- verification checks results
- progress and results are sent back to Feishu

### 2. Scheduled window inspection
A scheduled task runs every night at 21:00:

- navigate through predefined inspection points
- capture each window image
- check whether each window is closed
- send images and inspection summary back to Feishu

## Architecture

```text
Feishu text/voice
    ↓
Feishu Gateway
    ↓
OpenClaw Agent Layer
    ├─ intent understanding
    ├─ clarification
    ├─ task structuring
    └─ result summarization
    ↓
Mission Orchestrator
    ├─ task graph / state machine
    ├─ skill router
    ├─ recovery manager
    ├─ scheduler
    ├─ event bus
    └─ progress reporter
    ↓
ROS 2
    ├─ Navigation Skill Adapter -> VLN
    ├─ Manipulation Skill Adapter -> VLA
    ├─ Perception / Verification
    ├─ Robot Adapter
    ├─ Safety Supervisor
    └─ Data Logger
    ↓
Robot Runtime
    ├─ wheel-based humanoid platform
    └─ humanoid platform (e.g. G1)
Repository Layout
EmbodiedClaw/
├── AGENTS.md
├── README.md
├── apps/
│   └── bridge_api/
│       └── server.py
├── requirements-dev.txt
└── ros2_ws/
    └── src/
        ├── embodiedclaw_msgs/
        └── embodiedclaw_orchestrator/
Current Milestone: M1

M1 focuses on a minimal verifiable end-to-end pipeline:

OpenClaw / Feishu
→ HTTP Bridge
→ ROS 2 Orchestrator
→ fake task flow
→ task event feedback

This milestone does not yet connect real VLN, VLA, or robot hardware.

Included in M1
ROS 2 interface package: embodiedclaw_msgs
ROS 2 orchestrator package: embodiedclaw_orchestrator
HTTP bridge API with FastAPI
fake task execution flow for:
tidy_desk
inspect_windows
local end-to-end validation
M1 Local Test
1. Install Python dependencies
pip install -r requirements-dev.txt
2. Build ROS 2 workspace
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
3. Run orchestrator
cd ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run embodiedclaw_orchestrator orchestrator_node
4. Run FastAPI bridge
cd ..
source /opt/ros/humble/setup.bash
source ros2_ws/install/setup.bash
uvicorn apps.bridge_api.server:app --host 0.0.0.0 --port 8000
5. Health check
curl http://127.0.0.1:8000/health
6. Submit a tidy desk task
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "tidy_desk",
    "task_payload": {
      "area": "desk_01"
    }
  }'
7. Poll task status
curl http://127.0.0.1:8000/tasks/<task_id>
8. Watch ROS 2 task events
cd ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic echo /assistant/task_events
Roadmap
M0
architecture freeze
interface freeze
task protocol freeze
M1
fake end-to-end pipeline
ROS 2 task action server
progress event publishing
HTTP bridge
M2
navigation skill integration
fixed-point inspection demo
M3
manipulation skill integration
tidy desk demo
M4
scheduled tasks
recovery and escalation
M5
data loop
replay and evaluation
iterative optimization
Long-Term Goal

Build a reusable assistant robot framework where:

the upper layer is task- and skill-oriented
skill interfaces remain stable
the robot embodiment can be replaced
execution data can be used for continuous improvement
License

TBD
