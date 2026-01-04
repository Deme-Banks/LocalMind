"""
Video Templates - Predefined templates and presets for video generation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoTemplate:
    """Video generation template"""
    id: str
    name: str
    description: str
    prompt_template: str
    default_duration: int = 5
    default_aspect_ratio: str = "16:9"
    default_resolution: str = "1080p"
    suggested_backend: Optional[str] = None
    suggested_model: Optional[str] = None
    tags: List[str] = None
    category: str = "general"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def generate_prompt(self, **kwargs) -> str:
        """
        Generate prompt from template
        
        Args:
            **kwargs: Variables to fill in template
        
        Returns:
            Generated prompt
        """
        prompt = self.prompt_template
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "default_duration": self.default_duration,
            "default_aspect_ratio": self.default_aspect_ratio,
            "default_resolution": self.default_resolution,
            "suggested_backend": self.suggested_backend,
            "suggested_model": self.suggested_model,
            "tags": self.tags,
            "category": self.category
        }


class VideoTemplateManager:
    """Manages video generation templates"""
    
    def __init__(self):
        """Initialize template manager"""
        self.templates: Dict[str, VideoTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates"""
        default_templates = [
            # Nature & Landscape
            VideoTemplate(
                id="sunset_ocean",
                name="Sunset Over Ocean",
                description="A serene sunset over a calm ocean",
                prompt_template="A breathtaking sunset over a calm ocean, {style}, cinematic lighting, {mood}",
                default_duration=8,
                default_aspect_ratio="16:9",
                tags=["nature", "ocean", "sunset", "landscape"],
                category="nature"
            ),
            VideoTemplate(
                id="mountain_range",
                name="Mountain Range",
                description="Majestic mountain range with dramatic skies",
                prompt_template="A majestic mountain range at {time_of_day}, dramatic clouds, {weather}, cinematic, epic scale",
                default_duration=10,
                default_aspect_ratio="16:9",
                tags=["nature", "mountains", "landscape"],
                category="nature"
            ),
            
            # Urban & City
            VideoTemplate(
                id="city_timelapse",
                name="City Timelapse",
                description="Time-lapse of a bustling city",
                prompt_template="Time-lapse of a {city_type} city, {time_of_day}, traffic flowing, lights twinkling, {mood}",
                default_duration=15,
                default_aspect_ratio="16:9",
                tags=["urban", "city", "timelapse"],
                category="urban"
            ),
            VideoTemplate(
                id="street_scene",
                name="Street Scene",
                description="Vibrant street scene with people",
                prompt_template="A vibrant {city_type} street scene, {time_of_day}, people walking, {weather}, {mood}",
                default_duration=6,
                default_aspect_ratio="16:9",
                tags=["urban", "street", "people"],
                category="urban"
            ),
            
            # Abstract & Artistic
            VideoTemplate(
                id="abstract_flow",
                name="Abstract Flow",
                description="Abstract flowing patterns and colors",
                prompt_template="Abstract flowing patterns, {color_scheme} colors, {style} style, mesmerizing, {mood}",
                default_duration=10,
                default_aspect_ratio="1:1",
                tags=["abstract", "artistic", "colors"],
                category="artistic"
            ),
            VideoTemplate(
                id="particle_effects",
                name="Particle Effects",
                description="Dynamic particle effects and motion",
                prompt_template="Dynamic particle effects, {color_scheme} particles, {motion_type} motion, {style}, {mood}",
                default_duration=8,
                default_aspect_ratio="16:9",
                tags=["abstract", "particles", "effects"],
                category="artistic"
            ),
            
            # Character & Animation
            VideoTemplate(
                id="character_walk",
                name="Character Walk Cycle",
                description="Animated character walking",
                prompt_template="A {character_type} character walking, {style} animation style, {background}, {mood}",
                default_duration=5,
                default_aspect_ratio="16:9",
                tags=["character", "animation", "walk"],
                category="animation"
            ),
            VideoTemplate(
                id="character_dance",
                name="Character Dance",
                description="Animated character dancing",
                prompt_template="A {character_type} character dancing, {dance_style}, {style} animation, {background}, energetic",
                default_duration=8,
                default_aspect_ratio="16:9",
                tags=["character", "animation", "dance"],
                category="animation"
            ),
            
            # Product & Commercial
            VideoTemplate(
                id="product_showcase",
                name="Product Showcase",
                description="Professional product showcase",
                prompt_template="Professional product showcase, {product_type}, {lighting} lighting, {background}, commercial quality",
                default_duration=6,
                default_aspect_ratio="16:9",
                tags=["product", "commercial", "showcase"],
                category="commercial"
            ),
            VideoTemplate(
                id="logo_animation",
                name="Logo Animation",
                description="Animated logo reveal",
                prompt_template="Animated logo reveal, {logo_style} style, {animation_type} animation, {background}, professional",
                default_duration=5,
                default_aspect_ratio="16:9",
                tags=["logo", "animation", "brand"],
                category="commercial"
            ),
            
            # Sci-Fi & Fantasy
            VideoTemplate(
                id="sci_fi_city",
                name="Sci-Fi City",
                description="Futuristic sci-fi cityscape",
                prompt_template="A futuristic sci-fi cityscape, {time_of_day}, flying vehicles, neon lights, {mood}, cinematic",
                default_duration=12,
                default_aspect_ratio="16:9",
                tags=["sci-fi", "futuristic", "city"],
                category="sci-fi"
            ),
            VideoTemplate(
                id="space_scene",
                name="Space Scene",
                description="Epic space scene with planets and stars",
                prompt_template="Epic space scene, {planet_type} planet, stars, nebula, {mood}, cinematic, 4K quality",
                default_duration=15,
                default_aspect_ratio="16:9",
                tags=["space", "sci-fi", "planets"],
                category="sci-fi"
            ),
            
            # Food & Lifestyle
            VideoTemplate(
                id="food_preparation",
                name="Food Preparation",
                description="Beautiful food preparation scene",
                prompt_template="Beautiful {food_type} preparation, {cooking_style}, {lighting} lighting, appetizing, {mood}",
                default_duration=8,
                default_aspect_ratio="16:9",
                tags=["food", "cooking", "lifestyle"],
                category="lifestyle"
            ),
            VideoTemplate(
                id="cozy_interior",
                name="Cozy Interior",
                description="Warm and cozy interior scene",
                prompt_template="A cozy {room_type} interior, {time_of_day}, warm lighting, {style} style, {mood}",
                default_duration=10,
                default_aspect_ratio="16:9",
                tags=["interior", "lifestyle", "cozy"],
                category="lifestyle"
            ),
        ]
        
        for template in default_templates:
            self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[VideoTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[VideoTemplate]:
        """
        List templates with optional filters
        
        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            search: Search in name and description
        
        Returns:
            List of matching templates
        """
        templates = list(self.templates.values())
        
        # Filter by category
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filter by tags
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        # Search filter
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if (search_lower in t.name.lower() or
                    search_lower in t.description.lower())
            ]
        
        return templates
    
    def get_categories(self) -> List[str]:
        """Get all template categories"""
        categories = set(t.category for t in self.templates.values())
        return sorted(categories)
    
    def get_tags(self) -> List[str]:
        """Get all template tags"""
        tags = set()
        for template in self.templates.values():
            tags.update(template.tags)
        return sorted(tags)
    
    def add_template(self, template: VideoTemplate):
        """Add a custom template"""
        self.templates[template.id] = template
        logger.info(f"Added template: {template.id}")
    
    def remove_template(self, template_id: str) -> bool:
        """Remove a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Removed template: {template_id}")
            return True
        return False

