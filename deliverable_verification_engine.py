"""
DELIVERABLE VERIFICATION ENGINE
================================

AI-powered semantic verification that checks if deliverables match intents
BEFORE buyer sees them.

INTEGRATES WITH:
- proof_pipe.py (real-world proofs: POS, bookings, signatures)
- intent_exchange_UPGRADED.py (verify_poo endpoint)
- universal_executor.py (_stage_validation)
- execution_orchestrator.py (delivery pipeline)
- outcome_oracle_max.py (funnel tracking)

THE DISTINCTION:
- proof_pipe.py = "Did they get paid? Did they show up?" (real-world)
- THIS FILE = "Does the deliverable match the intent?" (semantic)

VERIFICATION DIMENSIONS:
1. Semantic Match - Does content address the intent?
2. Completeness - Are all requirements covered?
3. Quality - Grammar, code quality, design polish
4. Format Compliance - Correct file types, structure
5. Originality - Plagiarism/duplication check

FLOW:
Agent submits deliverable → AI Verification → Quality Score
  → Score >= 0.85: Auto-approve, notify buyer
  → Score 0.60-0.85: Flag for revision
  → Score < 0.60: Reject, require redo
"""

import asyncio
import json
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4

# Import existing systems
try:
    from proof_pipe import create_proof, verify_proof, PROOF_TYPES, OUTCOME_EVENTS
    PROOF_PIPE_AVAILABLE = True
except ImportError:
    PROOF_PIPE_AVAILABLE = False
    print("⚠️ proof_pipe not available - real-world proofs disabled")

try:
    from outcome_oracle_max import on_event as record_outcome
    OUTCOME_ORACLE_AVAILABLE = True
except ImportError:
    OUTCOME_ORACLE_AVAILABLE = False

try:
    from yield_memory import store_pattern, find_similar_patterns
    YIELD_MEMORY_AVAILABLE = True
except ImportError:
    YIELD_MEMORY_AVAILABLE = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# VERIFICATION CONFIGURATION
# ============================================================

class VerificationDimension(str, Enum):
    """Dimensions of deliverable verification"""
    SEMANTIC_MATCH = "semantic_match"      # Does it address the intent?
    COMPLETENESS = "completeness"          # All requirements covered?
    QUALITY = "quality"                    # Grammar, code quality, polish
    FORMAT = "format"                      # Correct structure/file types
    ORIGINALITY = "originality"            # Not plagiarized


class VerificationResult(str, Enum):
    """Possible verification outcomes"""
    AUTO_APPROVED = "auto_approved"        # Score >= 0.85, good to go
    NEEDS_REVISION = "needs_revision"      # Score 0.60-0.85, agent should fix
    REJECTED = "rejected"                  # Score < 0.60, start over
    MANUAL_REVIEW = "manual_review"        # Uncertain, needs human
    PENDING = "pending"                    # Not yet verified


class DeliverableType(str, Enum):
    """Types of deliverables"""
    CODE = "code"
    CONTENT = "content"
    DESIGN = "design"
    DOCUMENT = "document"
    DATA = "data"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


# Dimension weights (must sum to 1.0)
DIMENSION_WEIGHTS = {
    VerificationDimension.SEMANTIC_MATCH: 0.35,
    VerificationDimension.COMPLETENESS: 0.25,
    VerificationDimension.QUALITY: 0.20,
    VerificationDimension.FORMAT: 0.10,
    VerificationDimension.ORIGINALITY: 0.10,
}

# Thresholds
VERIFICATION_THRESHOLDS = {
    "auto_approve": 0.85,      # Score >= 0.85 auto-approved
    "needs_revision": 0.60,    # Score 0.60-0.85 needs revision
    "auto_reject": 0.40,       # Score < 0.40 auto-rejected
    "confidence_threshold": 0.70,  # If confidence < this, manual review
}

# Service-specific quality criteria
SERVICE_QUALITY_CRITERIA = {
    DeliverableType.CONTENT: {
        "min_word_count": 300,
        "max_grammar_errors_per_100_words": 2,
        "required_elements": ["introduction", "body", "conclusion"],
        "plagiarism_threshold": 0.15,
        "readability_min_score": 60,  # Flesch reading ease
    },
    DeliverableType.CODE: {
        "must_parse": True,
        "max_lint_errors": 5,
        "documentation_required": True,
        "test_file_expected": True,
        "no_hardcoded_secrets": True,
    },
    DeliverableType.DESIGN: {
        "min_resolution": (1920, 1080),
        "accepted_formats": ["png", "svg", "psd", "figma", "jpg"],
        "layers_expected": True,
        "brand_colors_if_provided": True,
    },
    DeliverableType.DOCUMENT: {
        "min_pages": 1,
        "formatting_required": True,
        "sections_match_outline": True,
        "citations_if_required": True,
    },
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Intent:
    """The buyer's intent (what they asked for)"""
    intent_id: str
    title: str
    description: str
    requirements: List[str]
    service_type: str
    deliverable_type: DeliverableType
    budget: float
    deadline: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['deliverable_type'] = self.deliverable_type.value
        return result


@dataclass
class Deliverable:
    """The agent's deliverable (what they produced)"""
    deliverable_id: str
    intent_id: str
    agent_id: str
    content: str  # Text content or file reference
    deliverable_type: DeliverableType
    files: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    submitted_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['deliverable_type'] = self.deliverable_type.value
        return result


@dataclass
class DimensionScore:
    """Score for a single verification dimension"""
    dimension: VerificationDimension
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


@dataclass
class VerificationReport:
    """Complete verification report for a deliverable"""
    verification_id: str
    intent_id: str
    deliverable_id: str
    agent_id: str
    overall_score: float
    overall_confidence: float
    result: VerificationResult
    dimension_scores: Dict[str, DimensionScore]
    issues: List[str]
    suggestions: List[str]
    auto_approved: bool
    requires_revision: bool
    revision_instructions: Optional[str]
    verified_at: str
    verification_time_ms: int
    real_world_proofs: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = {
            "verification_id": self.verification_id,
            "intent_id": self.intent_id,
            "deliverable_id": self.deliverable_id,
            "agent_id": self.agent_id,
            "overall_score": self.overall_score,
            "overall_confidence": self.overall_confidence,
            "result": self.result.value,
            "dimension_scores": {
                k: {
                    "dimension": v.dimension.value,
                    "score": v.score,
                    "confidence": v.confidence,
                    "issues": v.issues,
                    "suggestions": v.suggestions,
                }
                for k, v in self.dimension_scores.items()
            },
            "issues": self.issues,
            "suggestions": self.suggestions,
            "auto_approved": self.auto_approved,
            "requires_revision": self.requires_revision,
            "revision_instructions": self.revision_instructions,
            "verified_at": self.verified_at,
            "verification_time_ms": self.verification_time_ms,
            "real_world_proofs": self.real_world_proofs,
        }
        return result


# ============================================================
# VERIFICATION ENGINE
# ============================================================

class DeliverableVerificationEngine:
    """
    AI-powered verification engine for deliverables.
    
    Checks semantic match, completeness, quality, format, and originality
    before deliverables reach the buyer.
    """
    
    def __init__(self):
        self.verification_history: List[VerificationReport] = []
        self.learning_enabled = YIELD_MEMORY_AVAILABLE
        
        print("\n" + "="*60)
        print("🔍 DELIVERABLE VERIFICATION ENGINE INITIALIZED")
        print("="*60)
        print(f"   Proof Pipe Integration: {'✅' if PROOF_PIPE_AVAILABLE else '❌'}")
        print(f"   Outcome Oracle: {'✅' if OUTCOME_ORACLE_AVAILABLE else '❌'}")
        print(f"   Pattern Learning: {'✅' if YIELD_MEMORY_AVAILABLE else '❌'}")
        print("="*60 + "\n")
    
    
    async def verify_deliverable(
        self,
        intent: Intent,
        deliverable: Deliverable,
        real_world_proofs: List[Dict] = None
    ) -> VerificationReport:
        """
        Main verification entry point.
        
        Args:
            intent: What the buyer asked for
            deliverable: What the agent produced
            real_world_proofs: Optional proofs from proof_pipe.py
            
        Returns:
            VerificationReport with scores and decision
        """
        start_time = datetime.now(timezone.utc)
        
        print(f"\n🔍 Verifying deliverable {deliverable.deliverable_id}")
        print(f"   Intent: {intent.title}")
        print(f"   Type: {deliverable.deliverable_type.value}")
        
        # Score each dimension
        dimension_scores = {}
        
        # 1. Semantic Match
        semantic_score = await self._verify_semantic_match(intent, deliverable)
        dimension_scores[VerificationDimension.SEMANTIC_MATCH.value] = semantic_score
        print(f"   Semantic Match: {semantic_score.score:.2f}")
        
        # 2. Completeness
        completeness_score = await self._verify_completeness(intent, deliverable)
        dimension_scores[VerificationDimension.COMPLETENESS.value] = completeness_score
        print(f"   Completeness: {completeness_score.score:.2f}")
        
        # 3. Quality
        quality_score = await self._verify_quality(intent, deliverable)
        dimension_scores[VerificationDimension.QUALITY.value] = quality_score
        print(f"   Quality: {quality_score.score:.2f}")
        
        # 4. Format
        format_score = await self._verify_format(intent, deliverable)
        dimension_scores[VerificationDimension.FORMAT.value] = format_score
        print(f"   Format: {format_score.score:.2f}")
        
        # 5. Originality
        originality_score = await self._verify_originality(deliverable)
        dimension_scores[VerificationDimension.ORIGINALITY.value] = originality_score
        print(f"   Originality: {originality_score.score:.2f}")
        
        # Calculate weighted overall score
        overall_score = sum(
            dimension_scores[dim.value].score * weight
            for dim, weight in DIMENSION_WEIGHTS.items()
        )
        
        # Calculate overall confidence
        overall_confidence = sum(
            dimension_scores[dim.value].confidence * weight
            for dim, weight in DIMENSION_WEIGHTS.items()
        )
        
        # Collect all issues and suggestions
        all_issues = []
        all_suggestions = []
        for ds in dimension_scores.values():
            all_issues.extend(ds.issues)
            all_suggestions.extend(ds.suggestions)
        
        # Determine result
        result, auto_approved, requires_revision, revision_instructions = self._determine_result(
            overall_score,
            overall_confidence,
            all_issues
        )
        
        # Calculate verification time
        end_time = datetime.now(timezone.utc)
        verification_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Build report
        report = VerificationReport(
            verification_id=_generate_id("ver"),
            intent_id=intent.intent_id,
            deliverable_id=deliverable.deliverable_id,
            agent_id=deliverable.agent_id,
            overall_score=round(overall_score, 3),
            overall_confidence=round(overall_confidence, 3),
            result=result,
            dimension_scores=dimension_scores,
            issues=all_issues,
            suggestions=all_suggestions,
            auto_approved=auto_approved,
            requires_revision=requires_revision,
            revision_instructions=revision_instructions,
            verified_at=_now(),
            verification_time_ms=verification_time_ms,
            real_world_proofs=real_world_proofs or []
        )
        
        # Store in history
        self.verification_history.append(report)
        
        # Learn from this verification if enabled
        if self.learning_enabled:
            await self._store_verification_pattern(intent, deliverable, report)
        
        # Log result
        print(f"\n   📊 OVERALL SCORE: {overall_score:.2f}")
        print(f"   📋 RESULT: {result.value}")
        if auto_approved:
            print("   ✅ AUTO-APPROVED - Ready for buyer")
        elif requires_revision:
            print("   ⚠️ NEEDS REVISION - Sending back to agent")
        else:
            print("   ❌ REJECTED - Must restart")
        
        return report
    
    
    async def _verify_semantic_match(
        self,
        intent: Intent,
        deliverable: Deliverable
    ) -> DimensionScore:
        """
        Verify deliverable semantically matches intent.
        
        Checks:
        - Key topics from intent appear in deliverable
        - Requirements are addressed
        - Scope is appropriate (not too narrow/broad)
        """
        issues = []
        suggestions = []
        
        # Extract key terms from intent
        intent_text = f"{intent.title} {intent.description} {' '.join(intent.requirements)}"
        intent_keywords = self._extract_keywords(intent_text)
        intent_keywords.extend(intent.keywords)
        
        # Extract key terms from deliverable
        deliverable_keywords = self._extract_keywords(deliverable.content)
        
        # Calculate keyword overlap
        if intent_keywords:
            keyword_overlap = len(set(intent_keywords) & set(deliverable_keywords)) / len(set(intent_keywords))
        else:
            keyword_overlap = 0.5  # Neutral if no keywords
        
        # Check requirements coverage
        requirements_covered = 0
        for req in intent.requirements:
            req_keywords = self._extract_keywords(req)
            if any(kw in deliverable.content.lower() for kw in req_keywords):
                requirements_covered += 1
        
        if intent.requirements:
            requirements_score = requirements_covered / len(intent.requirements)
        else:
            requirements_score = 0.8  # Assume mostly covered if no explicit requirements
        
        # Check scope appropriateness
        intent_word_count = len(intent_text.split())
        deliverable_word_count = len(deliverable.content.split())
        
        # Deliverable should be substantially longer than intent
        if deliverable_word_count < intent_word_count:
            scope_score = 0.5
            issues.append("Deliverable seems too short relative to requirements")
            suggestions.append("Expand the deliverable to fully address all requirements")
        elif deliverable_word_count > intent_word_count * 20:
            scope_score = 0.7
            issues.append("Deliverable may be overly verbose")
            suggestions.append("Consider condensing to focus on key requirements")
        else:
            scope_score = 1.0
        
        # Combine scores
        semantic_score = (keyword_overlap * 0.4 + requirements_score * 0.4 + scope_score * 0.2)
        
        # Add issues for low keyword overlap
        if keyword_overlap < 0.3:
            issues.append(f"Low topic alignment ({keyword_overlap:.0%})")
            suggestions.append("Ensure deliverable addresses the main topics from the intent")
        
        # Add issues for uncovered requirements
        if requirements_score < 0.8:
            uncovered = len(intent.requirements) - requirements_covered
            issues.append(f"{uncovered} requirement(s) may not be addressed")
            suggestions.append("Review and address all listed requirements")
        
        return DimensionScore(
            dimension=VerificationDimension.SEMANTIC_MATCH,
            score=min(1.0, max(0.0, semantic_score)),
            confidence=0.75,  # Keyword matching has moderate confidence
            issues=issues,
            suggestions=suggestions,
            details={
                "keyword_overlap": round(keyword_overlap, 2),
                "requirements_covered": requirements_covered,
                "total_requirements": len(intent.requirements),
                "scope_score": round(scope_score, 2),
            }
        )
    
    
    async def _verify_completeness(
        self,
        intent: Intent,
        deliverable: Deliverable
    ) -> DimensionScore:
        """
        Verify all requirements are fully addressed.
        """
        issues = []
        suggestions = []
        
        # Check each requirement individually
        requirement_scores = []
        
        for i, req in enumerate(intent.requirements):
            # Look for evidence requirement is addressed
            req_lower = req.lower()
            content_lower = deliverable.content.lower()
            
            # Simple presence check
            key_phrases = self._extract_key_phrases(req)
            phrases_found = sum(1 for phrase in key_phrases if phrase in content_lower)
            
            if key_phrases:
                req_score = min(1.0, phrases_found / len(key_phrases))
            else:
                req_score = 0.5
            
            requirement_scores.append(req_score)
            
            if req_score < 0.5:
                issues.append(f"Requirement {i+1} may not be fully addressed: '{req[:50]}...'")
                suggestions.append(f"Ensure requirement {i+1} is explicitly covered")
        
        # Check for expected sections based on deliverable type
        criteria = SERVICE_QUALITY_CRITERIA.get(deliverable.deliverable_type, {})
        required_elements = criteria.get("required_elements", [])
        
        elements_found = 0
        for element in required_elements:
            if element.lower() in deliverable.content.lower():
                elements_found += 1
        
        if required_elements:
            elements_score = elements_found / len(required_elements)
            if elements_score < 0.8:
                missing = len(required_elements) - elements_found
                issues.append(f"Missing {missing} expected section(s)")
        else:
            elements_score = 1.0
        
        # Calculate overall completeness
        if requirement_scores:
            avg_req_score = sum(requirement_scores) / len(requirement_scores)
        else:
            avg_req_score = 0.8
        
        completeness_score = avg_req_score * 0.7 + elements_score * 0.3
        
        return DimensionScore(
            dimension=VerificationDimension.COMPLETENESS,
            score=min(1.0, max(0.0, completeness_score)),
            confidence=0.80,
            issues=issues,
            suggestions=suggestions,
            details={
                "requirements_scores": requirement_scores,
                "elements_found": elements_found,
                "elements_expected": len(required_elements),
            }
        )
    
    
    async def _verify_quality(
        self,
        intent: Intent,
        deliverable: Deliverable
    ) -> DimensionScore:
        """
        Verify quality based on deliverable type.
        """
        issues = []
        suggestions = []
        
        criteria = SERVICE_QUALITY_CRITERIA.get(deliverable.deliverable_type, {})
        quality_scores = []
        
        if deliverable.deliverable_type == DeliverableType.CONTENT:
            # Check word count
            word_count = len(deliverable.content.split())
            min_words = criteria.get("min_word_count", 100)
            
            if word_count < min_words:
                quality_scores.append(word_count / min_words)
                issues.append(f"Content too short ({word_count} words, minimum {min_words})")
            else:
                quality_scores.append(1.0)
            
            # Check grammar (simple heuristics)
            grammar_score = self._check_grammar_simple(deliverable.content)
            quality_scores.append(grammar_score)
            
            if grammar_score < 0.8:
                issues.append("Grammar or spelling issues detected")
                suggestions.append("Proofread for grammar and spelling")
            
            # Check readability
            readability = self._calculate_readability(deliverable.content)
            min_readability = criteria.get("readability_min_score", 50)
            
            if readability < min_readability:
                quality_scores.append(readability / 100)
                issues.append(f"Content may be difficult to read (score: {readability})")
                suggestions.append("Simplify language for better readability")
            else:
                quality_scores.append(1.0)
        
        elif deliverable.deliverable_type == DeliverableType.CODE:
            # Check if code appears valid
            code_quality = self._check_code_quality(deliverable.content)
            quality_scores.append(code_quality["syntax_score"])
            quality_scores.append(code_quality["style_score"])
            
            if code_quality["syntax_score"] < 0.8:
                issues.append("Code may have syntax issues")
                suggestions.append("Verify code compiles/runs without errors")
            
            if code_quality["style_score"] < 0.8:
                issues.append("Code style could be improved")
                suggestions.append("Follow consistent coding conventions")
            
            # Check for documentation
            if criteria.get("documentation_required", False):
                has_docs = "def " in deliverable.content and ('"""' in deliverable.content or "'''" in deliverable.content or "#" in deliverable.content)
                if not has_docs:
                    quality_scores.append(0.5)
                    issues.append("Code lacks documentation")
                    suggestions.append("Add docstrings and comments")
                else:
                    quality_scores.append(1.0)
        
        elif deliverable.deliverable_type == DeliverableType.DESIGN:
            # For designs, check file references
            if deliverable.files:
                valid_formats = criteria.get("accepted_formats", ["png", "jpg", "svg"])
                format_ok = any(
                    any(f.get("name", "").lower().endswith(fmt) for fmt in valid_formats)
                    for f in deliverable.files
                )
                if format_ok:
                    quality_scores.append(1.0)
                else:
                    quality_scores.append(0.6)
                    issues.append("Design files not in expected format")
            else:
                quality_scores.append(0.5)
                issues.append("No design files attached")
                suggestions.append("Attach design files in PNG, SVG, or PSD format")
        
        else:
            # Generic quality check
            if len(deliverable.content) > 100:
                quality_scores.append(0.8)
            else:
                quality_scores.append(0.5)
                issues.append("Deliverable content seems minimal")
        
        # Calculate average quality score
        if quality_scores:
            quality_score = sum(quality_scores) / len(quality_scores)
        else:
            quality_score = 0.7
        
        return DimensionScore(
            dimension=VerificationDimension.QUALITY,
            score=min(1.0, max(0.0, quality_score)),
            confidence=0.70,
            issues=issues,
            suggestions=suggestions,
            details={
                "quality_checks": len(quality_scores),
                "deliverable_type": deliverable.deliverable_type.value,
            }
        )
    
    
    async def _verify_format(
        self,
        intent: Intent,
        deliverable: Deliverable
    ) -> DimensionScore:
        """
        Verify deliverable format matches expectations.
        """
        issues = []
        suggestions = []
        format_score = 1.0
        
        # Check file attachments if expected
        criteria = SERVICE_QUALITY_CRITERIA.get(deliverable.deliverable_type, {})
        
        if deliverable.deliverable_type == DeliverableType.DESIGN:
            if not deliverable.files:
                format_score = 0.5
                issues.append("Design deliverable should include file attachments")
                suggestions.append("Attach the design files (PNG, PSD, Figma, etc.)")
            else:
                # Check file formats
                accepted = criteria.get("accepted_formats", ["png", "jpg", "svg", "psd"])
                valid_files = sum(
                    1 for f in deliverable.files
                    if any(f.get("name", "").lower().endswith(fmt) for fmt in accepted)
                )
                if valid_files == 0:
                    format_score = 0.6
                    issues.append(f"Files not in accepted formats: {accepted}")
        
        elif deliverable.deliverable_type == DeliverableType.CODE:
            # Check for proper code structure
            if "def " in deliverable.content or "class " in deliverable.content or "function" in deliverable.content:
                format_score = 1.0
            elif len(deliverable.content) > 50:
                format_score = 0.8
            else:
                format_score = 0.6
                issues.append("Code structure not detected")
                suggestions.append("Ensure code is properly formatted with functions/classes")
        
        elif deliverable.deliverable_type == DeliverableType.DOCUMENT:
            # Check for document structure
            has_structure = (
                deliverable.content.count("\n\n") > 2 or  # Paragraphs
                "#" in deliverable.content or  # Markdown headers
                deliverable.files  # Attached document
            )
            if has_structure:
                format_score = 1.0
            else:
                format_score = 0.7
                issues.append("Document lacks clear structure")
                suggestions.append("Add headers and organize into sections")
        
        return DimensionScore(
            dimension=VerificationDimension.FORMAT,
            score=min(1.0, max(0.0, format_score)),
            confidence=0.85,
            issues=issues,
            suggestions=suggestions,
            details={
                "files_attached": len(deliverable.files),
                "content_length": len(deliverable.content),
            }
        )
    
    
    async def _verify_originality(
        self,
        deliverable: Deliverable
    ) -> DimensionScore:
        """
        Check for plagiarism/duplication.
        """
        issues = []
        suggestions = []
        
        # Simple duplication checks
        content = deliverable.content
        
        # Check for repeated paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        unique_paragraphs = set(paragraphs)
        
        if paragraphs:
            uniqueness_ratio = len(unique_paragraphs) / len(paragraphs)
        else:
            uniqueness_ratio = 1.0
        
        if uniqueness_ratio < 0.8:
            issues.append("Content contains repeated sections")
            suggestions.append("Remove duplicate paragraphs")
        
        # Check for common placeholder text
        placeholder_patterns = [
            "lorem ipsum",
            "placeholder",
            "todo:",
            "[insert",
            "example text",
            "your text here",
        ]
        
        placeholders_found = sum(
            1 for pattern in placeholder_patterns
            if pattern in content.lower()
        )
        
        if placeholders_found > 0:
            originality_penalty = 0.1 * placeholders_found
            issues.append(f"Found {placeholders_found} placeholder text pattern(s)")
            suggestions.append("Replace all placeholder text with actual content")
        else:
            originality_penalty = 0
        
        # Calculate originality score
        originality_score = uniqueness_ratio - originality_penalty
        
        return DimensionScore(
            dimension=VerificationDimension.ORIGINALITY,
            score=min(1.0, max(0.0, originality_score)),
            confidence=0.65,  # Simple check has lower confidence
            issues=issues,
            suggestions=suggestions,
            details={
                "unique_paragraphs": len(unique_paragraphs),
                "total_paragraphs": len(paragraphs),
                "placeholders_found": placeholders_found,
            }
        )
    
    
    def _determine_result(
        self,
        score: float,
        confidence: float,
        issues: List[str]
    ) -> Tuple[VerificationResult, bool, bool, Optional[str]]:
        """
        Determine verification result based on score and confidence.
        
        Returns:
            (result, auto_approved, requires_revision, revision_instructions)
        """
        thresholds = VERIFICATION_THRESHOLDS
        
        # Low confidence = manual review
        if confidence < thresholds["confidence_threshold"]:
            return (
                VerificationResult.MANUAL_REVIEW,
                False,
                False,
                "Verification confidence too low. Manual review required."
            )
        
        # High score = auto approve
        if score >= thresholds["auto_approve"]:
            return (
                VerificationResult.AUTO_APPROVED,
                True,
                False,
                None
            )
        
        # Medium score = needs revision
        if score >= thresholds["needs_revision"]:
            revision_instructions = "Please address the following issues:\n"
            for i, issue in enumerate(issues[:5], 1):  # Top 5 issues
                revision_instructions += f"{i}. {issue}\n"
            
            return (
                VerificationResult.NEEDS_REVISION,
                False,
                True,
                revision_instructions
            )
        
        # Low score = rejected
        return (
            VerificationResult.REJECTED,
            False,
            False,
            "Deliverable does not meet minimum quality standards. Please review requirements and start over."
        )
    
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
            'neither', 'not', 'only', 'own', 'same', 'than', 'too',
            'very', 'just', 'also', 'now', 'here', 'there', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'any', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'this', 'that', 'these', 'those',
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stopwords and get unique
        keywords = [w for w in words if w not in stopwords]
        
        return list(set(keywords))
    
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases (2-3 word combinations)."""
        words = text.lower().split()
        phrases = []
        
        # Single important words
        phrases.extend(self._extract_keywords(text)[:5])
        
        # Two-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5:
                phrases.append(phrase)
        
        return phrases[:10]
    
    
    def _check_grammar_simple(self, text: str) -> float:
        """Simple grammar check using heuristics."""
        issues = 0
        
        # Check sentence structure
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check capitalization
            if sentence and sentence[0].islower():
                issues += 1
            
            # Check for double spaces
            if '  ' in sentence:
                issues += 1
        
        # Check for common errors
        common_errors = [
            (r'\bi\b', 'I'),  # Lowercase 'i'
            (r'\.\.+', '...'),  # Multiple periods
            (r'\s+,', ','),  # Space before comma
        ]
        
        for pattern, _ in common_errors:
            if re.search(pattern, text):
                issues += 1
        
        # Calculate score
        total_checks = len(sentences) + len(common_errors)
        if total_checks > 0:
            score = 1.0 - (issues / total_checks)
        else:
            score = 0.8
        
        return max(0.0, min(1.0, score))
    
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score."""
        sentences = len(re.findall(r'[.!?]+', text)) or 1
        words = len(text.split()) or 1
        syllables = sum(self._count_syllables(word) for word in text.split())
        
        # Flesch Reading Ease formula
        if words > 0 and sentences > 0:
            score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        else:
            score = 50
        
        return max(0, min(100, score))
    
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximate)."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        # Adjust for common patterns
        if word.endswith('e'):
            count -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        
        return max(1, count)
    
    
    def _check_code_quality(self, code: str) -> Dict[str, float]:
        """Check code quality using heuristics."""
        syntax_issues = 0
        style_issues = 0
        
        lines = code.split('\n')
        
        for line in lines:
            # Check indentation consistency
            if line.startswith(' ') and not line.startswith('    ') and not line.startswith('  '):
                style_issues += 1
            
            # Check for very long lines
            if len(line) > 120:
                style_issues += 1
            
            # Check for common syntax patterns that suggest errors
            if line.count('(') != line.count(')'):
                syntax_issues += 1
            if line.count('[') != line.count(']'):
                syntax_issues += 1
            if line.count('{') != line.count('}'):
                syntax_issues += 1
        
        # Check overall bracket balance
        if code.count('(') != code.count(')'):
            syntax_issues += 2
        if code.count('[') != code.count(']'):
            syntax_issues += 2
        if code.count('{') != code.count('}'):
            syntax_issues += 2
        
        total_lines = len(lines) or 1
        syntax_score = 1.0 - (syntax_issues / total_lines)
        style_score = 1.0 - (style_issues / total_lines)
        
        return {
            "syntax_score": max(0.0, min(1.0, syntax_score)),
            "style_score": max(0.0, min(1.0, style_score)),
        }
    
    
    async def _store_verification_pattern(
        self,
        intent: Intent,
        deliverable: Deliverable,
        report: VerificationReport
    ):
        """Store verification pattern for future learning."""
        if not YIELD_MEMORY_AVAILABLE:
            return
        
        try:
            pattern = {
                "intent_type": intent.service_type,
                "deliverable_type": deliverable.deliverable_type.value,
                "score": report.overall_score,
                "result": report.result.value,
                "issues_count": len(report.issues),
                "auto_approved": report.auto_approved,
            }
            
            outcome = "success" if report.auto_approved else "needs_work"
            
            store_pattern(
                user="system",
                pattern_type="verification",
                context=pattern,
                action="verify_deliverable",
                outcome=outcome,
                metrics={"score": report.overall_score}
            )
        except Exception as e:
            print(f"⚠️ Failed to store verification pattern: {e}")
    
    
    # ============================================================
    # PUBLIC UTILITIES
    # ============================================================
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        if not self.verification_history:
            return {"total_verifications": 0}
        
        total = len(self.verification_history)
        auto_approved = sum(1 for v in self.verification_history if v.auto_approved)
        needs_revision = sum(1 for v in self.verification_history if v.requires_revision)
        rejected = sum(1 for v in self.verification_history if v.result == VerificationResult.REJECTED)
        
        avg_score = sum(v.overall_score for v in self.verification_history) / total
        
        return {
            "total_verifications": total,
            "auto_approved": auto_approved,
            "auto_approved_rate": round(auto_approved / total, 2),
            "needs_revision": needs_revision,
            "rejected": rejected,
            "average_score": round(avg_score, 2),
        }


# ============================================================
# INTEGRATION FUNCTIONS
# ============================================================

# Global engine instance
_VERIFICATION_ENGINE: Optional[DeliverableVerificationEngine] = None


def get_verification_engine() -> DeliverableVerificationEngine:
    """Get or create the global verification engine."""
    global _VERIFICATION_ENGINE
    if _VERIFICATION_ENGINE is None:
        _VERIFICATION_ENGINE = DeliverableVerificationEngine()
    return _VERIFICATION_ENGINE


async def verify_before_buyer_sees(
    intent_data: Dict[str, Any],
    deliverable_data: Dict[str, Any],
    real_world_proofs: List[Dict] = None
) -> Dict[str, Any]:
    """
    Main integration function - verify deliverable before buyer sees it.
    
    Args:
        intent_data: Dict with intent details
        deliverable_data: Dict with deliverable details
        real_world_proofs: Optional proofs from proof_pipe.py
        
    Returns:
        Dict with verification results and recommended action
    """
    engine = get_verification_engine()
    
    # Build Intent object
    intent = Intent(
        intent_id=intent_data.get("id", _generate_id("int")),
        title=intent_data.get("title", ""),
        description=intent_data.get("description", ""),
        requirements=intent_data.get("requirements", []),
        service_type=intent_data.get("service_type", "general"),
        deliverable_type=DeliverableType(intent_data.get("deliverable_type", "content")),
        budget=intent_data.get("budget", 0),
        deadline=intent_data.get("deadline"),
        keywords=intent_data.get("keywords", []),
    )
    
    # Build Deliverable object
    deliverable = Deliverable(
        deliverable_id=deliverable_data.get("id", _generate_id("del")),
        intent_id=intent.intent_id,
        agent_id=deliverable_data.get("agent_id", "unknown"),
        content=deliverable_data.get("content", ""),
        deliverable_type=DeliverableType(deliverable_data.get("deliverable_type", "content")),
        files=deliverable_data.get("files", []),
        metadata=deliverable_data.get("metadata", {}),
    )
    
    # Run verification
    report = await engine.verify_deliverable(intent, deliverable, real_world_proofs)
    
    # Determine recommended action
    if report.auto_approved:
        action = "release_to_buyer"
        message = "Deliverable verified and auto-approved. Ready for buyer review."
    elif report.requires_revision:
        action = "return_to_agent"
        message = f"Deliverable needs revision. Score: {report.overall_score:.2f}"
    elif report.result == VerificationResult.REJECTED:
        action = "reject"
        message = "Deliverable rejected. Does not meet minimum standards."
    else:
        action = "manual_review"
        message = "Verification uncertain. Requires manual review."
    
    return {
        "ok": True,
        "verification_id": report.verification_id,
        "score": report.overall_score,
        "confidence": report.overall_confidence,
        "result": report.result.value,
        "action": action,
        "message": message,
        "auto_approved": report.auto_approved,
        "issues": report.issues,
        "suggestions": report.suggestions,
        "revision_instructions": report.revision_instructions,
        "dimension_scores": {
            k: {"score": v.score, "confidence": v.confidence}
            for k, v in report.dimension_scores.items()
        },
        "report": report.to_dict(),
    }


# ============================================================
# TESTING
# ============================================================

async def _test_verification():
    """Test the verification engine."""
    print("\n" + "="*60)
    print("🧪 TESTING DELIVERABLE VERIFICATION ENGINE")
    print("="*60)
    
    # Test 1: Good content deliverable
    print("\n📝 Test 1: Good content deliverable")
    
    intent1 = {
        "id": "intent_001",
        "title": "Write a blog post about AI in healthcare",
        "description": "Need a 500-word blog post about how AI is transforming healthcare",
        "requirements": [
            "Include examples of AI applications in healthcare",
            "Discuss benefits and challenges",
            "Include a call to action"
        ],
        "service_type": "content_creation",
        "deliverable_type": "content",
        "budget": 100,
        "keywords": ["AI", "healthcare", "machine learning", "diagnosis"],
    }
    
    deliverable1 = {
        "id": "del_001",
        "agent_id": "agent_alice",
        "deliverable_type": "content",
        "content": """
# AI in Healthcare: Transforming Patient Care

## Introduction

Artificial intelligence is revolutionizing the healthcare industry in unprecedented ways. 
From early disease detection to personalized treatment plans, AI applications are improving 
patient outcomes and reducing costs across the medical field.

## AI Applications in Healthcare

Machine learning algorithms are now being used for medical imaging analysis, helping radiologists 
detect tumors and abnormalities with greater accuracy. AI-powered diagnostic tools can analyze 
patient symptoms and medical history to suggest potential diagnoses.

Drug discovery has also been accelerated by AI, with companies using machine learning to 
identify promising compounds and predict their effectiveness.

## Benefits and Challenges

The benefits of AI in healthcare are substantial. Improved accuracy in diagnosis, reduced 
wait times, and personalized treatment recommendations all contribute to better patient care.

However, challenges remain. Data privacy concerns, the need for regulatory frameworks, and 
ensuring AI systems don't perpetuate biases are critical issues that must be addressed.

## Conclusion

As AI technology continues to advance, its role in healthcare will only grow. Healthcare 
organizations that embrace these innovations while addressing ethical concerns will be 
best positioned to deliver exceptional patient care.

**Ready to learn more about AI in healthcare? Contact us today to discuss how these 
technologies can benefit your organization.**
        """,
    }
    
    result1 = await verify_before_buyer_sees(intent1, deliverable1)
    print(f"   Score: {result1['score']:.2f}")
    print(f"   Result: {result1['result']}")
    print(f"   Action: {result1['action']}")
    
    # Test 2: Poor quality deliverable
    print("\n📝 Test 2: Poor quality deliverable")
    
    deliverable2 = {
        "id": "del_002",
        "agent_id": "agent_bob",
        "deliverable_type": "content",
        "content": "AI is good for healthcare. It helps doctors. The end.",
    }
    
    result2 = await verify_before_buyer_sees(intent1, deliverable2)
    print(f"   Score: {result2['score']:.2f}")
    print(f"   Result: {result2['result']}")
    print(f"   Action: {result2['action']}")
    print(f"   Issues: {result2['issues'][:3]}")
    
    # Test 3: Code deliverable
    print("\n💻 Test 3: Code deliverable")
    
    intent3 = {
        "id": "intent_003",
        "title": "Python function to calculate factorial",
        "description": "Write a Python function that calculates factorial with error handling",
        "requirements": [
            "Handle negative numbers",
            "Include docstring",
            "Add test cases"
        ],
        "service_type": "software_development",
        "deliverable_type": "code",
        "budget": 50,
    }
    
    deliverable3 = {
        "id": "del_003",
        "agent_id": "agent_charlie",
        "deliverable_type": "code",
        "content": '''
def factorial(n: int) -> int:
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


# Test cases
def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800
    
    try:
        factorial(-1)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("All tests passed!")


if __name__ == "__main__":
    test_factorial()
        ''',
    }
    
    result3 = await verify_before_buyer_sees(intent3, deliverable3)
    print(f"   Score: {result3['score']:.2f}")
    print(f"   Result: {result3['result']}")
    print(f"   Action: {result3['action']}")
    
    # Print stats
    engine = get_verification_engine()
    stats = engine.get_verification_stats()
    print(f"\n📊 Verification Stats: {stats}")
    
    print("\n✅ All tests completed!")
    return [result1, result2, result3]


if __name__ == "__main__":
    asyncio.run(_test_verification())
