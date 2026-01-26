"""
ENRICHMENT: Opportunity Enhancement Pipeline

Modules:
- contact_scoring: Contactability assessment
- psp_signal: Payment proximity detection
- enrichment_pipeline: Pipeline coordinator
"""

from .contact_scoring import get_contact_scorer, ContactScorer
from .psp_signal import get_psp_detector, PSPDetector
from .enrichment_pipeline import get_enrichment_pipeline, EnrichmentPipeline

__all__ = [
    'get_contact_scorer', 'ContactScorer',
    'get_psp_detector', 'PSPDetector',
    'get_enrichment_pipeline', 'EnrichmentPipeline',
]
