from enum import Enum


class CanonicalSkill(str, Enum):
    OBSERVE = 'observe'
    MOVE_FORWARD = 'move_forward'
    NAVIGATE_TO = 'navigate_to'
    PLACE_INTO = 'place_into'
    PICK = 'pick'
    TOGGLE = 'toggle'
    CLOSE = 'close'
    OPEN = 'open'
    STOP = 'stop'


class TaskType(str, Enum):
    MOVE_FORWARD = 'move_forward'
    ROTATE_RELATIVE = 'rotate_relative'
    NAVIGATE_TO = 'navigate_to'
    OBSERVE_SCENE = 'observe_scene'
    LIST_OBJECTS_ON_SURFACE = 'list_objects_on_surface'
    BRING_OBJECT = 'bring_object'
    TIDY_DESK = 'tidy_desk'
    INSPECT_WINDOWS_AND_LIGHTS = 'inspect_windows_and_lights'
    STOP_TASK = 'stop_task'


CANONICAL_SKILLS_V1 = tuple(skill.value for skill in CanonicalSkill)
TASK_TYPES_V1 = tuple(task_type.value for task_type in TaskType)
