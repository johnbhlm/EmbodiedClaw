AGENTS.md
Project overview

EmbodiedClaw is an assistant robot framework based on OpenClaw + ROS2.

Core principles:

capability abstraction must not bind to a specific robot
VLN and VLA are treated as skill providers
OpenClaw handles task understanding and orchestration, not low-level robot control
ROS2 is the unified bus
all robot-specific logic must stay inside Robot Adapter
Working rules
Prefer small, reviewable changes
Do not introduce unnecessary dependencies
Keep package names under embodiedclaw_*
Use Python for orchestration nodes
Keep ROS2 interfaces in a dedicated embodiedclaw_msgs package
Add or update README snippets when creating new packages
Run build/test commands after code changes
Build and test
ROS2 distro: Humble
Build:
cd ros2_ws && source /opt/ros/humble/setup.bash && colcon build --symlink-install
Run orchestrator:
source ros2_ws/install/setup.bash
ros2 run embodiedclaw_orchestrator orchestrator_node
First milestone

Implement M1 only:

embodiedclaw_msgs
embodiedclaw_orchestrator
HTTP bridge API
fake task execution for tidy_desk and inspect_windows
end-to-end local validation

Implementation requirements:

embodiedclaw_msgs
Create:
msg/TaskEvent.msg
action/ExecuteTask.action
valid package.xml
valid CMakeLists.txt

Use:
TaskEvent.msg

string task_id
string stage
string status
string message
string image_uri
builtin_interfaces/Time stamp

ExecuteTask.action
Goal:

string task_id
string task_type
string task_json
Result:
bool success
string summary
string[] artifact_uris
string error_code
Feedback:
string stage
float32 progress
string message
string image_uri
embodiedclaw_orchestrator
Create a Python ROS2 package with:
action server /assistant/execute_task
publisher /assistant/task_events

Implement fake execution plans for:

tidy_desk
inspect_windows

Expected behavior:

parse task_json
build a fake step plan
publish task events
publish action feedback
return final result

Suggested stages for tidy_desk:

RECEIVED
PLANNING
NAVIGATING
PERCEIVING
MANIPULATING
VERIFYING
REPORTING
COMPLETED

Suggested stages for inspect_windows:

RECEIVED
PLANNING
NAVIGATING
INSPECTING
REPORTING
COMPLETED
apps/bridge_api/server.py
Create a FastAPI app with:
GET /health
POST /tasks
GET /tasks/{task_id}

Requirements:

use ROS2 ActionClient to call /assistant/execute_task
subscribe to /assistant/task_events
keep in-memory task state
store:
latest stage
latest status
progress
events
feedback
final result
requirements-dev.txt
Include:
fastapi
uvicorn
pydantic

Validation requirements:

run colcon build --symlink-install
ensure the packages build cleanly
ensure the Python entry point is correct
ensure imports and package paths are correct

If local execution is not possible, still create the files correctly and explain what remains to validate manually.
