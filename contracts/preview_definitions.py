"""
PREVIEW DEFINITIONS: ~20% Preview Specs Per Fulfillment Type
============================================================

Defines what a "preview" means for each fulfillment type.
Preview = ~20% of the total work, watermarked, to demonstrate capability.

Updated: Jan 2026
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class PreviewSpec:
    """Specification for a preview deliverable"""
    fulfillment_type: str
    preview_percentage: float  # ~20%
    description: str
    artifacts: List[Dict[str, str]]  # [{name, type, description}]
    watermark_text: str = "PREVIEW - AiGentsy"
    preview_badge: str = "PREVIEW"


# Preview definitions by fulfillment type
PREVIEW_DEFINITIONS: Dict[str, PreviewSpec] = {
    "development": PreviewSpec(
        fulfillment_type="development",
        preview_percentage=0.20,
        description="Wireframe/PoC demonstrating architecture and key functionality",
        artifacts=[
            {
                "name": "wireframe.png",
                "type": "image",
                "description": "UI wireframe showing main screens/flows",
            },
            {
                "name": "structure.md",
                "type": "document",
                "description": "Project structure, tech stack, and architecture overview",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Development",
    ),

    "automation": PreviewSpec(
        fulfillment_type="automation",
        preview_percentage=0.20,
        description="Workflow diagram and sample trigger demonstrating automation logic",
        artifacts=[
            {
                "name": "workflow_diagram.png",
                "type": "image",
                "description": "Visual workflow diagram showing automation flow",
            },
            {
                "name": "sample_trigger.json",
                "type": "document",
                "description": "Sample trigger configuration and expected output",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Automation",
    ),

    "design": PreviewSpec(
        fulfillment_type="design",
        preview_percentage=0.20,
        description="Mood board and initial mockup demonstrating design direction",
        artifacts=[
            {
                "name": "mood_board.png",
                "type": "image",
                "description": "Mood board with colors, typography, and visual direction",
            },
            {
                "name": "mockup_preview.png",
                "type": "image",
                "description": "Low-fidelity mockup of main design elements",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Design",
    ),

    "content": PreviewSpec(
        fulfillment_type="content",
        preview_percentage=0.20,
        description="Outline and sample section demonstrating content quality",
        artifacts=[
            {
                "name": "outline.md",
                "type": "document",
                "description": "Full content outline with sections and key points",
            },
            {
                "name": "sample_section.md",
                "type": "document",
                "description": "Fully written sample section (~20% of content)",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Content",
    ),

    "data": PreviewSpec(
        fulfillment_type="data",
        preview_percentage=0.20,
        description="Sample analysis and visualization demonstrating data capabilities",
        artifacts=[
            {
                "name": "sample_analysis.md",
                "type": "document",
                "description": "Analysis methodology and initial findings",
            },
            {
                "name": "sample_chart.png",
                "type": "image",
                "description": "Sample visualization/chart from the data",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Data",
    ),

    "backend": PreviewSpec(
        fulfillment_type="backend",
        preview_percentage=0.20,
        description="API design and sample endpoint demonstrating backend architecture",
        artifacts=[
            {
                "name": "api_design.md",
                "type": "document",
                "description": "API endpoints, data models, and architecture",
            },
            {
                "name": "sample_endpoint.json",
                "type": "document",
                "description": "Sample endpoint request/response",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Backend",
    ),

    "frontend": PreviewSpec(
        fulfillment_type="frontend",
        preview_percentage=0.20,
        description="Component mockup and interaction flow demonstrating UI approach",
        artifacts=[
            {
                "name": "component_mockup.png",
                "type": "image",
                "description": "Key component mockups and layout",
            },
            {
                "name": "interaction_flow.md",
                "type": "document",
                "description": "User interaction flow and state management approach",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Frontend",
    ),

    "marketing": PreviewSpec(
        fulfillment_type="marketing",
        preview_percentage=0.20,
        description="Strategy overview and sample campaign asset",
        artifacts=[
            {
                "name": "strategy_overview.md",
                "type": "document",
                "description": "Marketing strategy, channels, and messaging",
            },
            {
                "name": "sample_asset.png",
                "type": "image",
                "description": "Sample marketing asset (ad, social post, etc.)",
            },
        ],
        watermark_text="PREVIEW - AiGentsy Marketing",
    ),
}

# Default preview spec for unknown types
DEFAULT_PREVIEW_SPEC = PreviewSpec(
    fulfillment_type="default",
    preview_percentage=0.20,
    description="Sample work demonstrating capability and approach",
    artifacts=[
        {
            "name": "preview_sample.md",
            "type": "document",
            "description": "Overview of approach and sample deliverable",
        },
        {
            "name": "preview_visual.png",
            "type": "image",
            "description": "Visual representation of the deliverable",
        },
    ],
    watermark_text="PREVIEW - AiGentsy",
)


def get_preview_spec(fulfillment_type: str) -> PreviewSpec:
    """
    Get preview specification for a fulfillment type.

    Args:
        fulfillment_type: Type of fulfillment (development, design, etc.)

    Returns:
        PreviewSpec for the type, or default if not found
    """
    return PREVIEW_DEFINITIONS.get(
        fulfillment_type.lower(),
        DEFAULT_PREVIEW_SPEC
    )


def get_preview_artifacts(fulfillment_type: str) -> List[Dict[str, str]]:
    """Get list of artifacts for a preview"""
    spec = get_preview_spec(fulfillment_type)
    return spec.artifacts


def get_watermark_text(fulfillment_type: str) -> str:
    """Get watermark text for a preview"""
    spec = get_preview_spec(fulfillment_type)
    return spec.watermark_text


def get_all_fulfillment_types() -> List[str]:
    """Get all supported fulfillment types"""
    return list(PREVIEW_DEFINITIONS.keys())


def preview_to_dict(spec: PreviewSpec) -> Dict[str, Any]:
    """Convert PreviewSpec to dictionary"""
    return {
        "fulfillment_type": spec.fulfillment_type,
        "preview_percentage": spec.preview_percentage,
        "description": spec.description,
        "artifacts": spec.artifacts,
        "watermark_text": spec.watermark_text,
        "preview_badge": spec.preview_badge,
    }
