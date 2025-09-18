"""
Memory Prompt Template Repository Implementation.
In-memory storage for prompt templates (for demo purposes).
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.ports.repository_port import PromptTemplateRepositoryPort
from app.core.entities.prompt_template import PromptTemplate, TemplateCategory, DEFAULT_TEMPLATES

logger = logging.getLogger(__name__)


class MemoryPromptTemplateRepository(PromptTemplateRepositoryPort):
    """
    In-memory implementation of prompt template repository.
    Uses default templates for demo purposes.
    """
    
    def __init__(self):
        """Initialize memory template repository with default templates."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize with default templates."""
        for template in DEFAULT_TEMPLATES:
            self._templates[template.id] = template
        logger.info(f"Initialized with {len(DEFAULT_TEMPLATES)} default templates")
    
    async def save_template(self, template: PromptTemplate) -> None:
        """Save or update prompt template."""
        self._templates[template.id] = template
        logger.debug(f"Saved template: {template.name}")
    
    async def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID."""
        return self._templates.get(template_id)
    
    async def get_templates_by_category(
        self, 
        category: str, 
        limit: int = 50
    ) -> List[PromptTemplate]:
        """Get templates by category."""
        try:
            category_enum = TemplateCategory(category)
            templates = [
                template for template in self._templates.values()
                if template.category == category_enum
            ]
            return templates[:limit]
        except ValueError:
            logger.warning(f"Invalid category: {category}")
            return []
    
    async def get_all_templates(self, limit: int = 100) -> List[PromptTemplate]:
        """Get all available templates."""
        templates = list(self._templates.values())
        return templates[:limit]
    
    async def search_templates(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[PromptTemplate]:
        """Search templates by name or description."""
        query_lower = query.lower()
        matching_templates = []
        
        for template in self._templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                query_lower in template.template.lower()):
                matching_templates.append(template)
        
        return matching_templates[:limit]
