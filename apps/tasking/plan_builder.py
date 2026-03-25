from __future__ import annotations

from typing import Any

from .skill_vocab import CanonicalSkill, TaskType
from .task_protocol import SkillStep, TaskSpec


class PlanBuilder:
    """Builds canonical-skill plans from a structured task spec."""

    def build(self, task: TaskSpec) -> list[SkillStep]:
        task_type = task.task_type
        payload = task.task_payload or {}

        if task_type == TaskType.MOVE_FORWARD:
            return [
                SkillStep(
                    skill_name=CanonicalSkill.MOVE_FORWARD,
                    params={'distance_m': float(payload.get('distance_m', 0.5))},
                    description='Move robot forward by requested distance',
                )
            ]

        if task_type == TaskType.ROTATE_RELATIVE:
            return [
                SkillStep(
                    skill_name=CanonicalSkill.NAVIGATE_TO,
                    params={'relative_pose': {'yaw_deg': float(payload.get('yaw_deg', 0.0))}},
                    description='Perform relative yaw change using navigation',
                    labels=['relative_navigation'],
                )
            ]

        if task_type == TaskType.NAVIGATE_TO:
            return [
                SkillStep(
                    skill_name=CanonicalSkill.NAVIGATE_TO,
                    params={'location_id': str(payload.get('location_id', ''))},
                    description='Navigate to requested location',
                )
            ]

        if task_type == TaskType.OBSERVE_SCENE:
            target = str(payload.get('area', payload.get('target', '')))
            return [
                SkillStep(
                    skill_name=CanonicalSkill.OBSERVE,
                    params={'target': target, 'mode': 'scene_summary'},
                    description='Observe scene and summarize',
                )
            ]

        if task_type == TaskType.LIST_OBJECTS_ON_SURFACE:
            target = str(payload.get('surface_id', payload.get('target', '')))
            return [
                SkillStep(
                    skill_name=CanonicalSkill.OBSERVE,
                    params={'target': target, 'mode': 'object_list'},
                    description='Observe objects on a surface',
                )
            ]

        if task_type == TaskType.BRING_OBJECT:
            object_name = str(payload.get('object_name', '')).strip()
            source = str(payload.get('source_location', '')).strip()
            recipient = str(payload.get('recipient_location', '')).strip()
            steps = [
                SkillStep(
                    skill_name=CanonicalSkill.NAVIGATE_TO,
                    params={'location_id': source},
                    description='Navigate to object source location',
                ),
                SkillStep(
                    skill_name=CanonicalSkill.OBSERVE,
                    params={
                        'mode': 'object_existence',
                        'target': source,
                        'object_name': object_name,
                    },
                    description='Check object existence at source',
                    labels=['object_existence_gate'],
                    branch={'on_missing': 'object_not_found'},
                ),
                SkillStep(
                    skill_name=CanonicalSkill.PICK,
                    params={'object_name': object_name},
                    description='Pick requested object',
                ),
            ]
            if recipient:
                steps.append(
                    SkillStep(
                        skill_name=CanonicalSkill.NAVIGATE_TO,
                        params={'location_id': recipient},
                        description='Navigate to recipient location',
                    )
                )
            steps.append(
                SkillStep(
                    skill_name=CanonicalSkill.PLACE_INTO,
                    params={'target': 'user_handover', 'recipient_location': recipient},
                    description='Place object for user handover',
                    labels=['recipient_location_gate'],
                    branch={'on_missing_recipient': 'recipient_location_required'},
                )
            )
            return steps

        if task_type == TaskType.TIDY_DESK:
            area = str(payload.get('area', 'desk_01'))
            return [
                SkillStep(
                    skill_name=CanonicalSkill.NAVIGATE_TO,
                    params={'location_id': area},
                    description='Navigate to desk area',
                ),
                SkillStep(
                    skill_name=CanonicalSkill.OBSERVE,
                    params={'target': area, 'mode': 'object_list'},
                    description='List objects currently on desk',
                ),
                SkillStep(
                    skill_name=CanonicalSkill.PICK,
                    params={'object_name': 'detected_target'},
                    description='Pick placeholder target object',
                ),
                SkillStep(
                    skill_name=CanonicalSkill.PLACE_INTO,
                    params={'target': 'default_container'},
                    description='Place object into default container',
                ),
                SkillStep(
                    skill_name=CanonicalSkill.OBSERVE,
                    params={'target': area, 'mode': 'verify_surface'},
                    description='Verify desk is tidy',
                    labels=['verification'],
                ),
            ]

        if task_type == TaskType.INSPECT_WINDOWS_AND_LIGHTS:
            window_targets = payload.get('window_targets') or []
            light_targets = payload.get('light_targets') or []
            steps: list[SkillStep] = []
            for target in window_targets:
                target_id = str(target)
                steps.extend(
                    [
                        SkillStep(
                            skill_name=CanonicalSkill.NAVIGATE_TO,
                            params={'location_id': target_id},
                            description=f'Navigate to window target {target_id}',
                        ),
                        SkillStep(
                            skill_name=CanonicalSkill.OBSERVE,
                            params={'target': target_id, 'mode': 'window_state'},
                            description=f'Inspect window state for {target_id}',
                        ),
                    ]
                )
            for target in light_targets:
                target_id = str(target)
                steps.extend(
                    [
                        SkillStep(
                            skill_name=CanonicalSkill.NAVIGATE_TO,
                            params={'location_id': target_id},
                            description=f'Navigate to light target {target_id}',
                        ),
                        SkillStep(
                            skill_name=CanonicalSkill.OBSERVE,
                            params={'target': target_id, 'mode': 'light_state'},
                            description=f'Inspect light state for {target_id}',
                        ),
                    ]
                )
            return steps

        if task_type == TaskType.STOP_TASK:
            return [
                SkillStep(
                    skill_name=CanonicalSkill.STOP,
                    params={},
                    description='Stop currently running task safely',
                )
            ]

        raise ValueError(f'Unsupported task type for planning: {task_type}')
