"""
ENRICHMENT: Opportunity Enhancement Pipeline

Modules:
- contact_scoring: Contactability assessment
- psp_signal: Payment proximity detection
- enrichment_pipeline: Pipeline coordinator
- ai_contact_extractor: AI-powered contact extraction (OpenRouter, Gemini)
"""

from .contact_scoring import get_contact_scorer, ContactScorer
from .psp_signal import get_psp_detector, PSPDetector
from .enrichment_pipeline import get_enrichment_pipeline, EnrichmentPipeline
from .ai_contact_extractor import (
    extract_contact_with_ai,
    extract_contact_with_openrouter,
    extract_contact_with_gemini,
    normalize_phone_number,
    validate_email
)

__all__ = [
    'get_contact_scorer', 'ContactScorer',
    'get_psp_detector', 'PSPDetector',
    'get_enrichment_pipeline', 'EnrichmentPipeline',
    # AI contact extraction
    'extract_contact_with_ai',
    'extract_contact_with_openrouter',
    'extract_contact_with_gemini',
    'normalize_phone_number',
    'validate_email',
]
