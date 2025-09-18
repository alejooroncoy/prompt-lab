"""
Prompt template domain entity.
Manages predefined prompt templates for different use cases.
"""
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import uuid


class TemplateCategory(Enum):
    """Prompt template categories."""
    GENERAL = "general"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"
    BUSINESS = "business"


class TemplateComplexity(Enum):
    """Template complexity levels."""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass(frozen=True)
class PromptTemplate:
    """
    Immutable prompt template entity.
    Defines reusable prompt structures with variables.
    """
    id: str
    name: str
    description: str
    category: TemplateCategory
    complexity: TemplateComplexity
    template: str
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate template invariants."""
        if not self.name.strip():
            raise ValueError("Template name cannot be empty")
        
        if not self.template.strip():
            raise ValueError("Template content cannot be empty")
        
        if len(self.template) > 50000:
            raise ValueError("Template too long (max 50000 characters)")
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        category: TemplateCategory,
        template: str,
        complexity: TemplateComplexity = TemplateComplexity.SIMPLE,
        variables: Dict[str, str] = None,
        metadata: Dict[str, Any] = None
    ) -> "PromptTemplate":
        """Factory method for creating prompt templates."""
        return cls(
            id=str(uuid.uuid4()),
            name=name.strip(),
            description=description.strip(),
            category=category,
            complexity=complexity,
            template=template.strip(),
            variables=variables or {},
            metadata=metadata or {}
        )
    
    def render(self, **kwargs) -> str:
        """
        Render template with provided variables.
        Supports both {{variable}} and {variable} syntax.
        """
        rendered = self.template
        
        # Handle {{variable}} syntax (double braces)
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(value))
        
        # Handle {variable} syntax (single braces)
        try:
            rendered = rendered.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
        
        return rendered
    
    def get_required_variables(self) -> list[str]:
        """Extract required variables from template."""
        import re
        
        # Find {{variable}} patterns
        double_brace_vars = re.findall(r'\{\{(\w+)\}\}', self.template)
        
        # Find {variable} patterns
        single_brace_vars = re.findall(r'\{(\w+)\}', self.template)
        
        # Combine and deduplicate
        all_vars = list(set(double_brace_vars + single_brace_vars))
        
        # Remove any variables that have default values
        required_vars = [var for var in all_vars if var not in self.variables]
        
        return required_vars
    
    @property
    def estimated_tokens(self) -> int:
        """Estimate token count for template (rough approximation)."""
        # Simple estimation: ~4 characters per token
        return len(self.template) // 4
    
    @property
    def is_complex(self) -> bool:
        """Check if template is complex."""
        return self.complexity == TemplateComplexity.ADVANCED
    
    def validate_variables(self, provided_vars: Dict[str, Any]) -> bool:
        """Validate that all required variables are provided."""
        required = self.get_required_variables()
        provided = set(provided_vars.keys())
        
        return all(var in provided for var in required)


# Predefined template collection
DEFAULT_TEMPLATES = [
    PromptTemplate.create(
        name="Análisis de Sentimiento",
        description="Analiza el sentimiento de un texto dado",
        category=TemplateCategory.ANALYTICAL,
        template="Analiza el sentimiento del siguiente texto y proporciona una evaluación detallada:\n\nTexto: {text}\n\nPor favor, evalúa:\n1. Sentimiento general (positivo/negativo/neutral)\n2. Nivel de confianza (0-100%)\n3. Palabras clave que influyen en el sentimiento\n4. Sugerencias para mejorar si es negativo",
        complexity=TemplateComplexity.INTERMEDIATE,
        variables={"text": "El texto a analizar"}
    ),
    
    PromptTemplate.create(
        name="Generación Creativa",
        description="Genera contenido creativo basado en un tema",
        category=TemplateCategory.CREATIVE,
        template="Crea contenido creativo sobre el tema: {topic}\n\nTipo de contenido: {content_type}\nTono: {tone}\nLongitud: {length}\n\nPor favor, genera contenido que sea:\n- Original y creativo\n- Apropiado para el tono especificado\n- De la longitud solicitada\n- Atractivo para el público objetivo",
        complexity=TemplateComplexity.INTERMEDIATE,
        variables={
            "topic": "El tema principal",
            "content_type": "artículo, historia, poema, etc.",
            "tone": "formal, informal, humorístico, etc.",
            "length": "corto, medio, largo"
        }
    ),
    
    PromptTemplate.create(
        name="Resumen Ejecutivo",
        description="Crea un resumen ejecutivo de información compleja",
        category=TemplateCategory.BUSINESS,
        template="Crea un resumen ejecutivo del siguiente contenido:\n\n{content}\n\nEl resumen debe incluir:\n1. Puntos clave principales (máximo 5)\n2. Conclusiones importantes\n3. Recomendaciones de acción\n4. Riesgos o consideraciones\n\nFormato: Máximo 200 palabras, lenguaje claro y directo",
        complexity=TemplateComplexity.INTERMEDIATE,
        variables={"content": "El contenido a resumir"}
    ),
    
    PromptTemplate.create(
        name="Análisis Técnico",
        description="Realiza análisis técnico detallado",
        category=TemplateCategory.TECHNICAL,
        template="Realiza un análisis técnico detallado de:\n\n{subject}\n\nAspectos a cubrir:\n1. Arquitectura y diseño\n2. Fortalezas y debilidades\n3. Mejores prácticas aplicadas\n4. Recomendaciones de mejora\n5. Consideraciones de escalabilidad\n\nNivel técnico: {technical_level}",
        complexity=TemplateComplexity.ADVANCED,
        variables={
            "subject": "El tema técnico a analizar",
            "technical_level": "básico, intermedio, avanzado"
        }
    ),
    
    PromptTemplate.create(
        name="Tutor Educativo",
        description="Proporciona explicación educativa paso a paso",
        category=TemplateCategory.EDUCATIONAL,
        template="Actúa como un tutor educativo y explica el concepto: {concept}\n\nNivel del estudiante: {student_level}\nContexto: {context}\n\nProporciona:\n1. Definición clara y simple\n2. Ejemplos prácticos\n3. Analogías o metáforas\n4. Ejercicios de práctica\n5. Recursos adicionales\n\nUsa un lenguaje apropiado para el nivel del estudiante.",
        complexity=TemplateComplexity.INTERMEDIATE,
        variables={
            "concept": "El concepto a explicar",
            "student_level": "principiante, intermedio, avanzado",
            "context": "El contexto de aprendizaje"
        }
    )
]
