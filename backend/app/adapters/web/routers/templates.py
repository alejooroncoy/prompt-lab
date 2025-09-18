"""
Templates Router.
Handles prompt template API endpoints.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.entities.prompt_template import TemplateCategory
from app.config.dependencies import get_prompt_template_repository

logger = logging.getLogger(__name__)

router = APIRouter()


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    name: str
    description: str
    category: str
    complexity: str
    template: str
    variables: dict
    metadata: dict
    created_at: str


class TemplateListResponse(BaseModel):
    """Template list response model."""
    templates: List[TemplateResponse]
    total: int
    category: Optional[str] = None


class TemplateValidationRequest(BaseModel):
    """Template validation request model."""
    template_id: Optional[str] = None
    template_content: Optional[str] = None
    variables: Optional[dict] = None
    category: Optional[str] = None


class TemplateValidationResponse(BaseModel):
    """Template validation response model."""
    is_valid: bool
    rendered_prompt: Optional[str] = None
    required_variables: Optional[List[str]] = None
    missing_variables: Optional[List[str]] = None
    estimated_tokens: int = 0
    validation_errors: Optional[List[str]] = None
    template_info: Optional[dict] = None


class TemplateRenderResponse(BaseModel):
    """Template render response model."""
    template_id: str
    template_name: str
    variables_used: dict
    rendered_prompt: str
    estimated_tokens: int


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by template category"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of templates to return"),
    template_repo = Depends(get_prompt_template_repository)
):
    """
    Get available prompt templates.
    """
    try:
        if category:
            # Get templates by category
            templates = await template_repo.get_templates_by_category(category, limit)
        else:
            # Get all templates
            templates = await template_repo.get_all_templates(limit)
        
        # Convert to response format
        template_data = []
        for template in templates:
            template_data.append(TemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                category=template.category.value,
                complexity=template.complexity.value,
                template=template.template,
                variables=template.variables,
                metadata=template.metadata,
                created_at=template.created_at.isoformat()
            ))
        
        return TemplateListResponse(
            templates=template_data,
            total=len(template_data),
            category=category
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    template_repo = Depends(get_prompt_template_repository)
):
    """
    Get specific template by ID.
    """
    try:
        template = await template_repo.get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return TemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category.value,
            complexity=template.complexity.value,
            template=template.template,
            variables=template.variables,
            metadata=template.metadata,
            created_at=template.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")


@router.get("/templates/search")
async def search_templates(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    template_repo = Depends(get_prompt_template_repository)
):
    """
    Search templates by name, description, or content.
    """
    try:
        templates = await template_repo.search_templates(query, limit)
        
        # Convert to response format
        template_data = []
        for template in templates:
            template_data.append(TemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                category=template.category.value,
                complexity=template.complexity.value,
                template=template.template,
                variables=template.variables,
                metadata=template.metadata,
                created_at=template.created_at.isoformat()
            ))
        
        return {
            "query": query,
            "templates": template_data,
            "total": len(template_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to search templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to search templates")


@router.get("/templates/categories")
async def get_template_categories():
    """
    Get available template categories.
    """
    try:
        categories = [
            {
                "value": category.value,
                "name": category.value.title(),
                "description": f"Templates for {category.value} use cases"
            }
            for category in TemplateCategory
        ]
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Failed to get template categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template categories")


@router.post("/templates/validate", response_model=TemplateValidationResponse)
async def validate_template(
    request: TemplateValidationRequest,
    template_repo = Depends(get_prompt_template_repository)
):
    """
    Validate a template and render it with variables.
    """
    try:
        from app.core.use_cases.chat.validate_prompt import PromptValidationUseCase
        
        # Create validation use case
        validation_use_case = PromptValidationUseCase(template_repo)
        
        # Create validation request
        validation_request = TemplateValidationRequest(
            template_id=request.template_id,
            template_content=request.template_content,
            variables=request.variables,
            category=request.category
        )
        
        # Execute validation
        response = await validation_use_case.execute(validation_request)
        
        return TemplateValidationResponse(
            is_valid=response.is_valid,
            rendered_prompt=response.rendered_prompt,
            required_variables=response.required_variables,
            missing_variables=response.missing_variables,
            estimated_tokens=response.estimated_tokens,
            validation_errors=response.validation_errors,
            template_info=response.template_info
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate template: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate template")


@router.post("/templates/{template_id}/render", response_model=TemplateRenderResponse)
async def render_template(
    template_id: str,
    variables: dict,
    template_repo = Depends(get_prompt_template_repository)
):
    """
    Render a template with provided variables.
    """
    try:
        template = await template_repo.get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Render template
        rendered_prompt = template.render(**variables)
        
        return TemplateRenderResponse(
            template_id=template_id,
            template_name=template.name,
            variables_used=variables,
            rendered_prompt=rendered_prompt,
            estimated_tokens=len(rendered_prompt) // 4  # Rough estimation
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to render template")
