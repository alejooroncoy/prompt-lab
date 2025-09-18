"""
Prompt Validation Use Case.
Validates and processes prompt templates.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ...entities.prompt_template import PromptTemplate, TemplateCategory
from ...ports.repository_port import PromptTemplateRepositoryPort

logger = logging.getLogger(__name__)


@dataclass
class PromptValidationRequest:
    """Request structure for prompt validation."""
    template_id: Optional[str] = None
    template_content: Optional[str] = None
    variables: Dict[str, Any] = None
    category: Optional[TemplateCategory] = None
    
    def __post_init__(self) -> None:
        """Validate request invariants."""
        if not self.template_id and not self.template_content:
            raise ValueError("Either template_id or template_content must be provided")


@dataclass
class PromptValidationResponse:
    """Response structure for prompt validation."""
    is_valid: bool
    rendered_prompt: Optional[str] = None
    required_variables: List[str] = None
    missing_variables: List[str] = None
    estimated_tokens: int = 0
    validation_errors: List[str] = None
    template_info: Optional[Dict[str, Any]] = None


class PromptValidationUseCase:
    """
    Prompt validation use case.
    Validates prompt templates and renders them with variables.
    """
    
    def __init__(self, template_repo: PromptTemplateRepositoryPort):
        """
        Initialize prompt validation use case.
        
        Args:
            template_repo: Prompt template repository
        """
        self._template_repo = template_repo
    
    async def execute(self, request: PromptValidationRequest) -> PromptValidationResponse:
        """
        Execute prompt validation workflow.
        
        Args:
            request: Prompt validation request
            
        Returns:
            Prompt validation response with results
            
        Raises:
            ValueError: For invalid request data
            Exception: For processing errors
        """
        try:
            # Step 1: Load template
            template = await self._load_template(request)
            
            # Step 2: Validate template
            validation_errors = self._validate_template(template)
            
            # Step 3: Check required variables
            required_variables = template.get_required_variables()
            missing_variables = self._check_missing_variables(
                required_variables, 
                request.variables or {}
            )
            
            # Step 4: Render prompt if variables are complete
            rendered_prompt = None
            if not missing_variables and request.variables:
                try:
                    rendered_prompt = template.render(**request.variables)
                except Exception as e:
                    validation_errors.append(f"Template rendering failed: {e}")
            
            # Step 5: Calculate estimated tokens
            estimated_tokens = template.estimated_tokens
            if rendered_prompt:
                estimated_tokens = len(rendered_prompt) // 4  # Rough estimation
            
            # Step 6: Create response
            is_valid = len(validation_errors) == 0 and len(missing_variables) == 0
            
            return PromptValidationResponse(
                is_valid=is_valid,
                rendered_prompt=rendered_prompt,
                required_variables=required_variables,
                missing_variables=missing_variables,
                estimated_tokens=estimated_tokens,
                validation_errors=validation_errors,
                template_info={
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category.value,
                    "complexity": template.complexity.value,
                    "is_complex": template.is_complex
                }
            )
            
        except Exception as e:
            logger.error(f"Prompt validation failed: {e}")
            return PromptValidationResponse(
                is_valid=False,
                validation_errors=[f"Validation failed: {e}"]
            )
    
    async def _load_template(self, request: PromptValidationRequest) -> PromptTemplate:
        """Load template from repository or create from content."""
        if request.template_id:
            template = await self._template_repo.get_template_by_id(request.template_id)
            if not template:
                raise ValueError(f"Template {request.template_id} not found")
            return template
        else:
            # Create template from content
            if not request.template_content:
                raise ValueError("Template content is required when template_id is not provided")
            
            return PromptTemplate.create(
                name="Custom Template",
                description="User-provided template",
                category=request.category or TemplateCategory.GENERAL,
                template=request.template_content
            )
    
    def _validate_template(self, template: PromptTemplate) -> List[str]:
        """Validate template structure and content."""
        errors = []
        
        # Check template length
        if len(template.template) > 50000:
            errors.append("Template is too long (max 50000 characters)")
        
        # Check for basic structure
        if not template.template.strip():
            errors.append("Template content cannot be empty")
        
        # Check for balanced braces
        if not self._check_balanced_braces(template.template):
            errors.append("Template has unbalanced braces")
        
        # Check for reasonable variable names
        import re
        variable_pattern = r'\{\{?(\w+)\}?\}'
        variables = re.findall(variable_pattern, template.template)
        
        for var in variables:
            if not var.replace('_', '').isalnum():
                errors.append(f"Invalid variable name: {var}")
        
        return errors
    
    def _check_missing_variables(
        self, 
        required_variables: List[str], 
        provided_variables: Dict[str, Any]
    ) -> List[str]:
        """Check for missing required variables."""
        missing = []
        provided_keys = set(provided_variables.keys())
        
        for var in required_variables:
            if var not in provided_keys:
                missing.append(var)
        
        return missing
    
    def _check_balanced_braces(self, text: str) -> bool:
        """Check if braces are balanced in template."""
        single_braces = 0
        double_braces = 0
        
        i = 0
        while i < len(text):
            if text[i] == '{':
                if i + 1 < len(text) and text[i + 1] == '{':
                    double_braces += 1
                    i += 2
                else:
                    single_braces += 1
                    i += 1
            elif text[i] == '}':
                if i + 1 < len(text) and text[i + 1] == '}':
                    double_braces -= 1
                    i += 2
                else:
                    single_braces -= 1
                    i += 1
            else:
                i += 1
        
        return single_braces == 0 and double_braces == 0
