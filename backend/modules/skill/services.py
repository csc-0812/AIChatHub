"""
技能管理模块 - 服务层
"""
import os
from typing import List, Optional
from fastapi import HTTPException

from skills import (
    load_skills_from_directory, get_skill, get_all_skills,
    create_skill, update_skill, delete_skill, toggle_skill,
    create_skill_template, execute_skill
)
from .models import (
    SkillInfo, SkillParameter, CreateSkillRequest, 
    UpdateSkillRequest, SkillExecuteResponse, SkillListResponse
)


class SkillService:
    def __init__(self):
        self.skills_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "skills", "skills_dir"
        )
        self.skills_dir = os.path.abspath(self.skills_dir)
    
    def _convert_to_skill_info(self, skill) -> SkillInfo:
        parameters = []
        for param in getattr(skill, 'parameters', []):
            parameters.append(SkillParameter(
                name=param.get('name', ''),
                type=param.get('type', 'string'),
                description=param.get('description', ''),
                required=param.get('required', True),
                default=param.get('default')
            ))
        
        return SkillInfo(
            name=skill.name,
            description=skill.description,
            version=getattr(skill, 'version', '1.0.0'),
            category=getattr(skill, 'category', 'general'),
            enabled=getattr(skill, 'enabled', True),
            parameters=parameters,
            system_prompt=getattr(skill, 'system_prompt', ''),
            user_prompt=getattr(skill, 'user_prompt', '')
        )
    
    def load_skills(self) -> SkillListResponse:
        skills = load_skills_from_directory(self.skills_dir)
        skill_infos = [self._convert_to_skill_info(s) for s in skills]
        return SkillListResponse(
            skills=skill_infos,
            total=len(skill_infos)
        )
    
    def get_skill_info(self, name: str) -> Optional[SkillInfo]:
        skill = get_skill(name)
        if not skill:
            return None
        return self._convert_to_skill_info(skill)
    
    def create_skill(self, request: CreateSkillRequest) -> SkillInfo:
        try:
            skill = create_skill(
                name=request.name,
                description=request.description,
                category=request.category,
                parameters=[p.dict() for p in request.parameters],
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                script=request.script
            )
            return self._convert_to_skill_info(skill)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def update_skill(self, name: str, request: UpdateSkillRequest) -> Optional[SkillInfo]:
        params = {}
        if request.name is not None:
            params['new_name'] = request.name
        if request.description is not None:
            params['description'] = request.description
        if request.category is not None:
            params['category'] = request.category
        if request.parameters is not None:
            params['parameters'] = [p.dict() for p in request.parameters]
        if request.system_prompt is not None:
            params['system_prompt'] = request.system_prompt
        if request.user_prompt is not None:
            params['user_prompt'] = request.user_prompt
        if request.script is not None:
            params['script'] = request.script
        
        try:
            skill = update_skill(name, **params)
            if not skill:
                return None
            return self._convert_to_skill_info(skill)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def delete_skill(self, name: str) -> bool:
        return delete_skill(name)
    
    def toggle_skill(self, name: str) -> bool:
        return toggle_skill(name)
    
    def create_skill_template(self, name: str) -> bool:
        return create_skill_template(self.skills_dir, name)
    
    async def execute_skill(self, skill_name: str, parameters: dict) -> SkillExecuteResponse:
        result = await execute_skill(skill_name, parameters)
        return SkillExecuteResponse(
            success=result.get('success', False),
            output=result.get('output'),
            error=result.get('error')
        )


skill_service = SkillService()