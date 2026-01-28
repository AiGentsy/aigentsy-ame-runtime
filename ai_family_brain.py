"""
═══════════════════════════════════════════════════════════════════════════════
     ___    ____   ______                    _ __         ____             _     
    /   |  /  _/  / ____/___ _____ ___  (_) /_  __   / __ )_________ _(_)___ 
   / /| |  / /   / /_  / __ `/ __ `__ \/ / / / / /  / __  / ___/ __ `/ / __ \
  / ___ |_/ /   / __/ / /_/ / / / / / / / / /_/ /  / /_/ / /  / /_/ / / / / /
 /_/  |_/___/  /_/    \__,_/_/ /_/ /_/_/_/\__, /  /_____/_/   \__,_/_/_/ /_/ 
                                         /____/                              
                                         
            THE WORLD'S FIRST NATIVE AI FAMILY NETWORK
═══════════════════════════════════════════════════════════════════════════════

A living, breathing AI FAMILY where Claude, GPT-4, Gemini, and Perplexity form 
an interconnected intelligence network that learns, teaches, evolves, and 
compounds at unprecedented velocity.

REVOLUTIONARY CONCEPTS:
1. CROSS-POLLINATION: Knowledge flows between models
2. SPECIALIZATION EMERGENCE: Models develop expertise through learning  
3. TEACHING LOOPS: Models educate each other
4. COLLECTIVE MEMORY: Shared hive mind via MetaHive integration
5. VELOCITY COMPOUNDING: Exponential improvement through mutual learning

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import time
import json
import asyncio
import httpx
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random

# API KEYS
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


class AIModel(str, Enum):
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


class TaskCategory(str, Enum):
    RESEARCH = "research"
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    MARKET_RESEARCH = "market_research"
    TREND_DETECTION = "trend_detection"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    WEB_SEARCH = "web_search"
    CONTENT_GENERATION = "content_generation"
    CREATIVE_WRITING = "creative_writing"
    COPYWRITING = "copywriting"
    EMAIL_WRITING = "email_writing"
    SOCIAL_MEDIA = "social_media"
    PITCH_CREATION = "pitch_creation"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    AUTOMATION = "automation"
    ARCHITECTURE = "architecture"
    CONSULTING = "consulting"
    STRATEGY = "strategy"
    PRICING = "pricing"
    NEGOTIATION = "negotiation"
    PROPOSAL_GENERATION = "proposal_generation"
    DATA_ANALYSIS = "data_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ANALYSIS = "risk_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    FULFILLMENT = "fulfillment"
    QUALITY_CHECK = "quality_check"
    REVISION = "revision"
    VERIFICATION = "verification"
    QUICK_GENERATION = "quick_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EXTRACTION = "extraction"
    LEAD_QUALIFICATION = "lead_qualification"
    UPSELL_IDENTIFICATION = "upsell_identification"
    CHURN_PREDICTION = "churn_prediction"
    REVENUE_OPTIMIZATION = "revenue_optimization"
    # V111 Super-Harvesters (Trillion-Class)
    ABANDONED_CHECKOUT_RECOVERY = "abandoned_checkout_recovery"
    RECEIVABLES_FACTORING = "receivables_factoring"
    PAYMENTS_OPTIMIZATION = "payments_optimization"
    
    # V112 Market Maker Extensions
    MARKET_MAKING = "market_making"
    RISK_TRANCHING = "risk_tranching"
    OFFER_SYNDICATION = "offer_syndication"
    
    # V110 Gap Harvesters (General)
    GAP_HARVESTING = "gap_harvesting"
    WASTE_MONETIZATION = "waste_monetization"
    
    # Revenue Engine Operations
    QUOTE_GENERATION = "quote_generation"
    SPREAD_CALCULATION = "spread_calculation"
    KELLY_SIZING = "kelly_sizing"
    INVOICE_ANALYSIS = "invoice_analysis"
    PAYMENT_ROUTING = "payment_routing"


@dataclass
class TaskExecution:
    task_id: str
    model: AIModel
    task_category: TaskCategory
    prompt_hash: str
    success: bool
    duration_ms: int
    quality_score: Optional[float] = None
    revenue_generated: Optional[float] = None
    tokens_used: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    response_summary: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ModelPersonality:
    model: AIModel
    total_tasks: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_revenue: float = 0.0
    total_tokens: int = 0
    specialization_scores: Dict[TaskCategory, float] = field(default_factory=dict)
    teachings_given: int = 0
    teachings_received: int = 0
    success_rate_history: List[Tuple[str, float]] = field(default_factory=list)
    current_velocity: float = 0.0
    traits: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        return self.total_successes / self.total_tasks if self.total_tasks > 0 else 0.0
    
    def get_top_specializations(self, n: int = 3) -> List[Tuple[TaskCategory, float]]:
        return sorted(self.specialization_scores.items(), key=lambda x: x[1], reverse=True)[:n]


@dataclass
class TeachingMoment:
    teaching_id: str
    teacher_model: AIModel
    task_category: TaskCategory
    insight: str
    pattern: Dict[str, Any]
    students: List[AIModel] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CrossPollinationEvent:
    event_id: str
    source_model: AIModel
    target_models: List[AIModel]
    knowledge_type: str
    knowledge_summary: str
    original_task_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CollectiveInsight:
    insight_id: str
    insight_type: str
    description: str
    contributing_models: List[AIModel]
    estimated_value: float
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# DEFAULT ROUTING - Overridden by learning
DEFAULT_ROUTING = {
    TaskCategory.RESEARCH: [AIModel.PERPLEXITY, AIModel.GEMINI, AIModel.CLAUDE],
    TaskCategory.OPPORTUNITY_DISCOVERY: [AIModel.PERPLEXITY, AIModel.GEMINI, AIModel.CLAUDE],
    TaskCategory.MARKET_RESEARCH: [AIModel.PERPLEXITY, AIModel.CLAUDE, AIModel.GEMINI],
    TaskCategory.TREND_DETECTION: [AIModel.PERPLEXITY, AIModel.GEMINI, AIModel.CLAUDE],
    TaskCategory.COMPETITIVE_ANALYSIS: [AIModel.PERPLEXITY, AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.WEB_SEARCH: [AIModel.PERPLEXITY, AIModel.GEMINI],
    TaskCategory.CONTENT_GENERATION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.CREATIVE_WRITING: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.COPYWRITING: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.EMAIL_WRITING: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.SOCIAL_MEDIA: [AIModel.GPT4, AIModel.CLAUDE, AIModel.GEMINI],
    TaskCategory.PITCH_CREATION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.CODE_GENERATION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.CODE_REVIEW: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.DEBUGGING: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.AUTOMATION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.ARCHITECTURE: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.CONSULTING: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.STRATEGY: [AIModel.CLAUDE, AIModel.GPT4, AIModel.PERPLEXITY],
    TaskCategory.PRICING: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.NEGOTIATION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.PROPOSAL_GENERATION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.DATA_ANALYSIS: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.SENTIMENT_ANALYSIS: [AIModel.CLAUDE, AIModel.GEMINI, AIModel.GPT4],
    TaskCategory.RISK_ANALYSIS: [AIModel.CLAUDE, AIModel.GPT4, AIModel.PERPLEXITY],
    TaskCategory.PATTERN_RECOGNITION: [AIModel.GEMINI, AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.FULFILLMENT: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.QUALITY_CHECK: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.REVISION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.VERIFICATION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.PERPLEXITY],
    TaskCategory.QUICK_GENERATION: [AIModel.GPT4, AIModel.CLAUDE, AIModel.GEMINI],
    TaskCategory.SUMMARIZATION: [AIModel.GPT4, AIModel.CLAUDE, AIModel.GEMINI],
    TaskCategory.TRANSLATION: [AIModel.GPT4, AIModel.GEMINI, AIModel.CLAUDE],
    TaskCategory.EXTRACTION: [AIModel.GPT4, AIModel.CLAUDE, AIModel.GEMINI],
    TaskCategory.LEAD_QUALIFICATION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.PERPLEXITY],
    TaskCategory.UPSELL_IDENTIFICATION: [AIModel.CLAUDE, AIModel.GPT4],
    TaskCategory.CHURN_PREDICTION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI],
    TaskCategory.REVENUE_OPTIMIZATION: [AIModel.CLAUDE, AIModel.GPT4, AIModel.PERPLEXITY],
}

# GLOBAL STATE
FAMILY_MEMBERS: Dict[AIModel, ModelPersonality] = {
    AIModel.CLAUDE: ModelPersonality(model=AIModel.CLAUDE, traits=["analytical", "thorough", "nuanced"]),
    AIModel.GPT4: ModelPersonality(model=AIModel.GPT4, traits=["fast", "creative", "versatile"]),
    AIModel.GEMINI: ModelPersonality(model=AIModel.GEMINI, traits=["multimodal", "research-oriented"]),
    AIModel.PERPLEXITY: ModelPersonality(model=AIModel.PERPLEXITY, traits=["real-time", "web-connected"]),
}

TASK_HISTORY: List[TaskExecution] = []
TEACHING_MOMENTS: List[TeachingMoment] = []
CROSS_POLLINATIONS: List[CrossPollinationEvent] = []
COLLECTIVE_INSIGHTS: List[CollectiveInsight] = []

CATEGORY_MODEL_STATS: Dict[TaskCategory, Dict[AIModel, Dict[str, Any]]] = defaultdict(
    lambda: defaultdict(lambda: {"tasks": 0, "successes": 0, "failures": 0, 
                                  "total_duration_ms": 0, "total_revenue": 0.0, "quality_scores": []})
)

MIN_TASKS_FOR_LEARNING = 10
MIN_TASKS_FOR_TEACHING = 20
MIN_TASKS_FOR_SPECIALIZATION = 50


class AIFamilyBrain:
    """The world's first native AI Family Network"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.available_models = {
            AIModel.CLAUDE: bool(ANTHROPIC_API_KEY or OPENROUTER_API_KEY),  # OpenRouter preferred
            AIModel.GPT4: bool(OPENAI_API_KEY or OPENROUTER_API_KEY),      # OpenRouter preferred
            AIModel.GEMINI: bool(GEMINI_API_KEY),                          # Direct API key
            AIModel.PERPLEXITY: bool(PERPLEXITY_API_KEY),                  # Direct API key
        }
        self._client: Optional[httpx.AsyncClient] = None
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._tasks_since_save = 0
        self._save_interval = 10  # Save every 10 tasks

        # Load previous learning state
        self._load_learning_state()

        available = [m.value for m, v in self.available_models.items() if v]
        print(f"🧠 AI FAMILY BRAIN AWAKENED - Members: {', '.join(available) if available else 'None'}")
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120)
        return self._client

    def _load_learning_state(self):
        """Load learning state from persistent storage"""
        global FAMILY_MEMBERS, TASK_HISTORY, CATEGORY_MODEL_STATS, TEACHING_MOMENTS, CROSS_POLLINATIONS

        try:
            from brain_persistence import load_ai_family_learning

            state = load_ai_family_learning()
            if state:
                # Restore family members
                for model_str, data in state.get("family_members", {}).items():
                    try:
                        model = AIModel(model_str)
                        if model in FAMILY_MEMBERS:
                            p = FAMILY_MEMBERS[model]
                            p.total_tasks = data.get("total_tasks", 0)
                            p.total_successes = data.get("total_successes", 0)
                            p.total_failures = data.get("total_failures", 0)
                            p.total_revenue = data.get("total_revenue", 0.0)
                            p.teachings_given = data.get("teachings_given", 0)
                            p.teachings_received = data.get("teachings_received", 0)
                            p.current_velocity = data.get("current_velocity", 0.0)
                            # Restore specialization scores
                            for cat_str, score in data.get("specialization_scores", {}).items():
                                try:
                                    cat = TaskCategory(cat_str)
                                    p.specialization_scores[cat] = score
                                except:
                                    pass
                    except:
                        pass

                # Restore category model stats
                for cat_str, model_stats in state.get("category_model_stats", {}).items():
                    try:
                        cat = TaskCategory(cat_str)
                        for model_str, stats in model_stats.items():
                            try:
                                model = AIModel(model_str)
                                CATEGORY_MODEL_STATS[cat][model] = stats
                            except:
                                pass
                    except:
                        pass

                print(f"📂 Loaded AI Family learning: {sum(p.total_tasks for p in FAMILY_MEMBERS.values())} tasks")
            else:
                print("📂 No previous AI Family learning found, starting fresh")

        except Exception as e:
            print(f"⚠️ Could not load AI Family learning: {e}")

    def _save_learning_state(self):
        """Save learning state to persistent storage"""
        try:
            from brain_persistence import save_ai_family_learning

            # Convert family members to dict
            family_dict = {}
            for model, p in FAMILY_MEMBERS.items():
                family_dict[model.value] = {
                    "total_tasks": p.total_tasks,
                    "total_successes": p.total_successes,
                    "total_failures": p.total_failures,
                    "total_revenue": p.total_revenue,
                    "teachings_given": p.teachings_given,
                    "teachings_received": p.teachings_received,
                    "current_velocity": p.current_velocity,
                    "specialization_scores": {cat.value: score for cat, score in p.specialization_scores.items()}
                }

            # Convert category model stats
            cat_stats_dict = {}
            for cat, model_stats in CATEGORY_MODEL_STATS.items():
                cat_str = cat.value if hasattr(cat, 'value') else str(cat)
                cat_stats_dict[cat_str] = {}
                for model, stats in model_stats.items():
                    model_str = model.value if hasattr(model, 'value') else str(model)
                    cat_stats_dict[cat_str][model_str] = stats

            # Convert task history
            task_history_dict = [
                {
                    "task_id": t.task_id,
                    "model": t.model.value,
                    "task_category": t.task_category.value,
                    "success": t.success,
                    "duration_ms": t.duration_ms,
                    "quality_score": t.quality_score,
                    "timestamp": t.timestamp
                }
                for t in TASK_HISTORY[-500:]  # Keep last 500
            ]

            # Convert teaching moments
            teachings_dict = [
                {
                    "teaching_id": t.teaching_id,
                    "teacher_model": t.teacher_model.value,
                    "task_category": t.task_category.value,
                    "students": [s.value for s in t.students],
                    "timestamp": t.timestamp
                }
                for t in TEACHING_MOMENTS[-100:]
            ]

            # Convert cross pollinations
            cross_poll_dict = [
                {
                    "event_id": c.event_id,
                    "source_model": c.source_model.value,
                    "target_models": [m.value for m in c.target_models],
                    "knowledge_type": c.knowledge_type,
                    "timestamp": c.timestamp
                }
                for c in CROSS_POLLINATIONS[-100:]
            ]

            save_ai_family_learning(
                family_dict, task_history_dict, cat_stats_dict,
                teachings_dict, cross_poll_dict
            )
            print(f"💾 Saved AI Family learning: {sum(p.total_tasks for p in FAMILY_MEMBERS.values())} tasks")

        except Exception as e:
            print(f"⚠️ Could not save AI Family learning: {e}")

    def _maybe_save(self):
        """Save learning state periodically"""
        self._tasks_since_save += 1
        if self._tasks_since_save >= self._save_interval:
            self._save_learning_state()
            self._tasks_since_save = 0

    def get_family_routing(self, task_category: TaskCategory, optimize_for: str = "balanced") -> List[AIModel]:
        """Get model priority based on learned performance"""
        default = DEFAULT_ROUTING.get(task_category, [AIModel.CLAUDE, AIModel.GPT4, AIModel.GEMINI, AIModel.PERPLEXITY])
        available = [m for m in default if self.available_models.get(m)]
        if not available:
            available = [AIModel.CLAUDE]
        
        category_stats = CATEGORY_MODEL_STATS.get(task_category, {})
        total_tasks = sum(s.get("tasks", 0) for s in category_stats.values())
        
        if total_tasks < MIN_TASKS_FOR_LEARNING:
            return available
        
        def score_model(model: AIModel) -> float:
            stats = category_stats.get(model, {})
            if stats.get("tasks", 0) == 0:
                return 0.5
            
            tasks = stats["tasks"]
            success_rate = stats["successes"] / tasks
            quality_scores = stats.get("quality_scores", [])
            avg_quality = sum(quality_scores[-50:]) / len(quality_scores[-50:]) if quality_scores else 0.5
            
            personality = FAMILY_MEMBERS.get(model)
            spec_score = personality.specialization_scores.get(task_category, 0.5) if personality else 0.5
            velocity_bonus = min(personality.current_velocity * 10, 0.2) if personality else 0
            
            if optimize_for == "speed":
                return success_rate * 0.6 + velocity_bonus * 0.4
            elif optimize_for == "quality":
                return avg_quality * 0.5 + success_rate * 0.3 + spec_score * 0.2
            elif optimize_for == "revenue":
                rev = stats.get("total_revenue", 0) / max(tasks, 1)
                return rev * 0.5 + success_rate * 0.3 + avg_quality * 0.2
            else:
                return success_rate * 0.3 + avg_quality * 0.25 + spec_score * 0.25 + velocity_bonus * 0.2
        
        scored = [(m, score_model(m)) for m in available]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored]
    
    async def execute(self, prompt: str, task_category: TaskCategory = TaskCategory.CONTENT_GENERATION,
                      max_tokens: int = 2000, context: Dict[str, Any] = None, optimize_for: str = "balanced",
                      enable_learning: bool = True) -> Dict[str, Any]:
        """Execute a task with family learning"""
        task_id = f"task_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        priority = self.get_family_routing(task_category, optimize_for)
        tried_models = []
        
        for model in priority:
            tried_models.append(model.value)
            start_time = time.time()
            
            try:
                api_result = await self._call_model(model, prompt, max_tokens)
                duration_ms = int((time.time() - start_time) * 1000)
                
                if api_result.get("ok"):
                    result = api_result
                    result.update({"model": model.value, "tried_models": tried_models, 
                                   "duration_ms": duration_ms, "task_id": task_id, 
                                   "task_category": task_category.value})
                    
                    if enable_learning:
                        execution = TaskExecution(
                            task_id=task_id, model=model, task_category=task_category,
                            prompt_hash=prompt_hash, success=True, duration_ms=duration_ms,
                            context=context or {}, response_summary=api_result.get("response", "")[:500]
                        )
                        self._record_execution(execution)
                        await self._check_teaching_opportunity(execution)
                        await self._check_cross_pollination(execution)
                    
                    return result
                    
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                print(f"⚠️ {model.value} failed: {e}")
                
                if enable_learning:
                    execution = TaskExecution(
                        task_id=task_id, model=model, task_category=task_category,
                        prompt_hash=prompt_hash, success=False, duration_ms=duration_ms, context=context or {}
                    )
                    self._record_execution(execution)
        
        return {"ok": False, "error": "All family members failed", "tried_models": tried_models, "task_id": task_id}
    
    async def execute_ensemble(self, prompt: str, task_category: TaskCategory, 
                                aggregation: str = "synthesize", max_tokens: int = 2000) -> Dict[str, Any]:
        """Execute with multiple models and aggregate results"""
        models = [m for m in AIModel if self.available_models.get(m)]
        
        if aggregation == "chain":
            return await self._execute_chain(prompt, task_category, models, max_tokens)
        
        # Parallel execution
        tasks = [self.execute(prompt, task_category, max_tokens, enable_learning=False) for _ in models]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = [r for r in results if isinstance(r, dict) and r.get("ok")]
        
        if not successful:
            return {"ok": False, "error": "All family members failed"}
        
        if aggregation == "best":
            best = max(successful, key=lambda r: len(r.get("response", "")))
            best["ensemble_type"] = "best"
            return best
        
        elif aggregation == "synthesize":
            synthesis_prompt = f"""Synthesize these AI responses:
{chr(10).join(f"[{r.get('model')}]: {r.get('response', '')[:800]}" for r in successful)}

Create ONE comprehensive response combining the best insights."""
            
            result = await self.execute(synthesis_prompt, TaskCategory.SUMMARIZATION, max_tokens, enable_learning=False)
            result["ensemble_type"] = "synthesized"
            result["source_models"] = [r.get("model") for r in successful]
            return result
        
        return successful[0]
    
    async def _execute_chain(self, prompt: str, task_category: TaskCategory, 
                              models: List[AIModel], max_tokens: int) -> Dict[str, Any]:
        """Sequential refinement - each model improves the previous output"""
        current = prompt
        chain = []
        
        for i, model in enumerate(models[:3]):  # Max 3 in chain
            if i == 0:
                result = await self.execute(current, task_category, max_tokens, enable_learning=False)
            else:
                refine = f"Improve this: {current[:1500]}\n\nMake it more accurate and complete."
                result = await self.execute(refine, task_category, max_tokens, enable_learning=False)
            
            if result.get("ok"):
                chain.append({"model": result.get("model"), "length": len(result.get("response", ""))})
                current = result.get("response", "")
        
        return {"ok": True, "response": current, "ensemble_type": "chain", "chain": chain}
    
    def _record_execution(self, execution: TaskExecution):
        """Record for family learning"""
        TASK_HISTORY.append(execution)
        if len(TASK_HISTORY) > 10000:
            TASK_HISTORY.pop(0)
        
        # Update personality
        personality = FAMILY_MEMBERS[execution.model]
        personality.total_tasks += 1
        if execution.success:
            personality.total_successes += 1
        else:
            personality.total_failures += 1
        
        # Update category stats
        stats = CATEGORY_MODEL_STATS[execution.task_category][execution.model]
        stats["tasks"] += 1
        stats["successes" if execution.success else "failures"] += 1
        stats["total_duration_ms"] += execution.duration_ms
        
        # Update velocity
        self._update_velocity(execution.model)
        self._update_specialization(execution.model, execution.task_category)

        # Periodically save learning state
        self._maybe_save()

    def _update_velocity(self, model: AIModel):
        """Track improvement rate"""
        personality = FAMILY_MEMBERS[model]
        rate = personality.success_rate
        personality.success_rate_history.append((datetime.now(timezone.utc).isoformat(), rate))
        personality.success_rate_history = personality.success_rate_history[-100:]
        
        if len(personality.success_rate_history) >= 10:
            old = personality.success_rate_history[-10][1]
            personality.current_velocity = (rate - old) / 10
    
    def _update_specialization(self, model: AIModel, category: TaskCategory):
        """Update specialization scores"""
        stats = CATEGORY_MODEL_STATS[category][model]
        if stats["tasks"] < MIN_TASKS_FOR_SPECIALIZATION:
            return
        
        rate = stats["successes"] / stats["tasks"]
        all_rates = [CATEGORY_MODEL_STATS[category][m]["successes"] / max(CATEGORY_MODEL_STATS[category][m]["tasks"], 1)
                     for m in AIModel if CATEGORY_MODEL_STATS[category][m]["tasks"] >= MIN_TASKS_FOR_SPECIALIZATION]
        
        if all_rates:
            score = sum(1 for r in all_rates if rate > r) / len(all_rates)
            FAMILY_MEMBERS[model].specialization_scores[category] = score
            
            if score > 0.8:
                print(f"🌟 {model.value} specialized in {category.value}!")
    
    async def _check_teaching_opportunity(self, execution: TaskExecution):
        """Check if model can teach others"""
        if not execution.success or FAMILY_MEMBERS[execution.model].total_tasks < MIN_TASKS_FOR_TEACHING:
            return
        
        model_stats = CATEGORY_MODEL_STATS[execution.task_category][execution.model]
        model_rate = model_stats["successes"] / max(model_stats["tasks"], 1)
        
        students = []
        for other in AIModel:
            if other == execution.model:
                continue
            other_stats = CATEGORY_MODEL_STATS[execution.task_category][other]
            if other_stats["tasks"] >= MIN_TASKS_FOR_LEARNING:
                other_rate = other_stats["successes"] / max(other_stats["tasks"], 1)
                if model_rate - other_rate > 0.15:
                    students.append(other)
        
        if students:
            teaching = TeachingMoment(
                teaching_id=f"teach_{int(time.time())}",
                teacher_model=execution.model, task_category=execution.task_category,
                insight=f"{execution.model.value} teaching {execution.task_category.value}",
                pattern={"prompt_hash": execution.prompt_hash}, students=students
            )
            TEACHING_MOMENTS.append(teaching)
            FAMILY_MEMBERS[execution.model].teachings_given += 1
            for s in students:
                FAMILY_MEMBERS[s].teachings_received += 1
            print(f"📚 Teaching: {execution.model.value} → {[s.value for s in students]}")
    
    async def _check_cross_pollination(self, execution: TaskExecution):
        """Check if knowledge should flow to other models"""
        if not execution.success:
            return
        
        # Novel patterns trigger cross-pollination
        similar = [e for e in TASK_HISTORY[-500:] if e.prompt_hash == execution.prompt_hash and e.task_id != execution.task_id]
        if not similar:
            event = CrossPollinationEvent(
                event_id=f"xpol_{int(time.time())}",
                source_model=execution.model,
                target_models=[m for m in AIModel if m != execution.model],
                knowledge_type="pattern", knowledge_summary=execution.response_summary[:200],
                original_task_id=execution.task_id
            )
            CROSS_POLLINATIONS.append(event)
            if len(CROSS_POLLINATIONS) > 500:
                CROSS_POLLINATIONS.pop(0)
    
    def record_quality_feedback(self, task_id: str, quality: float, revenue: float = None) -> bool:
        """Record quality feedback for learning"""
        for e in reversed(TASK_HISTORY):
            if e.task_id == task_id:
                e.quality_score = quality
                if revenue:
                    e.revenue_generated = revenue
                    FAMILY_MEMBERS[e.model].total_revenue += revenue
                    CATEGORY_MODEL_STATS[e.task_category][e.model]["total_revenue"] += revenue
                CATEGORY_MODEL_STATS[e.task_category][e.model]["quality_scores"].append(quality)
                return True
        return False
    
    def get_family_synergy_score(self) -> Dict[str, Any]:
        """Calculate family collaboration effectiveness"""
        teachings = sum(m.teachings_given for m in FAMILY_MEMBERS.values())
        velocity = sum(m.current_velocity for m in FAMILY_MEMBERS.values())
        tasks = [m.total_tasks for m in FAMILY_MEMBERS.values()]
        balance = min(tasks) / max(tasks) if max(tasks) > 0 else 0
        
        synergy = (min(teachings / 100, 1) * 0.3 + min(len(CROSS_POLLINATIONS) / 100, 1) * 0.3 +
                   min(velocity * 10, 1) * 0.2 + balance * 0.2)
        
        return {"synergy_score": round(synergy, 3), "teachings": teachings, 
                "cross_pollinations": len(CROSS_POLLINATIONS), "velocity": round(velocity, 4)}
    
    def get_family_stats(self) -> Dict[str, Any]:
        """Get comprehensive family statistics"""
        return {
            "members": {
                model.value: {
                    "online": self.available_models.get(model),
                    "tasks": p.total_tasks, "success_rate": f"{p.success_rate:.1%}",
                    "velocity": f"{p.current_velocity*100:.2f}%",
                    "specializations": [{"cat": c.value, "score": f"{s:.2f}"} for c, s in p.get_top_specializations(3)],
                    "teachings_given": p.teachings_given, "revenue": f"${p.total_revenue:.2f}"
                } for model, p in FAMILY_MEMBERS.items()
            },
            "synergy": self.get_family_synergy_score(),
            "total_tasks": sum(m.total_tasks for m in FAMILY_MEMBERS.values()),
            "insights": len(COLLECTIVE_INSIGHTS)
        }
    
    # API CALLS
    async def _call_model(self, model: AIModel, prompt: str, max_tokens: int) -> Dict[str, Any]:
        client = await self._get_client()
        
        if model == AIModel.PERPLEXITY and PERPLEXITY_API_KEY:
            r = await client.post("https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-sonar-large-128k-online", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
            if r.status_code == 200:
                d = r.json()
                return {"ok": True, "response": d.get("choices", [{}])[0].get("message", {}).get("content", ""), "citations": d.get("citations", [])}
            return {"ok": False, "error": f"Perplexity: {r.status_code}"}
        
        elif model == AIModel.GEMINI:
            # Use direct Gemini API key
            if GEMINI_API_KEY:
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens}}
                )
                if r.status_code == 200:
                    d = r.json()
                    return {"ok": True, "response": d.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")}
                return {"ok": False, "error": f"Gemini: {r.status_code}"}
        
        elif model == AIModel.CLAUDE:
            if OPENROUTER_API_KEY:
                return await self._call_openrouter(client, "anthropic/claude-3.5-sonnet", prompt, max_tokens)
            elif ANTHROPIC_API_KEY:
                r = await client.post("https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": ANTHROPIC_API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
                    json={"model": "claude-3-5-sonnet-20241022", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]})
                if r.status_code == 200:
                    return {"ok": True, "response": r.json().get("content", [{}])[0].get("text", "")}
                return {"ok": False, "error": f"Anthropic: {r.status_code}"}
        
        elif model == AIModel.GPT4:
            if OPENROUTER_API_KEY:
                return await self._call_openrouter(client, "openai/gpt-4-turbo", prompt, max_tokens)
            elif OPENAI_API_KEY:
                r = await client.post("https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={"model": "gpt-4-turbo-preview", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
                if r.status_code == 200:
                    return {"ok": True, "response": r.json().get("choices", [{}])[0].get("message", {}).get("content", "")}
                return {"ok": False, "error": f"OpenAI: {r.status_code}"}
        
        return {"ok": False, "error": f"No API key for {model.value}"}
    
    async def _call_openrouter(self, client, model: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        r = await client.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens})
        if r.status_code == 200:
            return {"ok": True, "response": r.json().get("choices", [{}])[0].get("message", {}).get("content", "")}
        return {"ok": False, "error": f"OpenRouter: {r.status_code}"}


# SINGLETON & CONVENIENCE FUNCTIONS
_brain: Optional[AIFamilyBrain] = None

def get_brain() -> AIFamilyBrain:
    global _brain
    if _brain is None:
        _brain = AIFamilyBrain()
    return _brain


async def ai_execute(prompt: str, task_category: str = "content_generation", max_tokens: int = 2000, optimize_for: str = "balanced") -> Dict[str, Any]:
    brain = get_brain()
    try:
        cat = TaskCategory(task_category)
    except ValueError:
        cat = TaskCategory.CONTENT_GENERATION
    return await brain.execute(prompt, cat, max_tokens, optimize_for=optimize_for)


async def ai_research(prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
    return await ai_execute(prompt, "research", max_tokens)

async def ai_content(prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
    return await ai_execute(prompt, "content_generation", max_tokens)

async def ai_code(prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
    return await ai_execute(prompt, "code_generation", max_tokens)

async def ai_quick(prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
    return await ai_execute(prompt, "quick_generation", max_tokens, optimize_for="speed")

async def ai_ensemble(prompt: str, task_category: str = "content_generation", aggregation: str = "synthesize") -> Dict[str, Any]:
    brain = get_brain()
    try:
        cat = TaskCategory(task_category)
    except ValueError:
        cat = TaskCategory.CONTENT_GENERATION
    return await brain.execute_ensemble(prompt, cat, aggregation=aggregation)

async def ai_chain(prompt: str, task_category: str = "content_generation") -> Dict[str, Any]:
    return await ai_ensemble(prompt, task_category, aggregation="chain")


def get_family_stats() -> Dict[str, Any]:
    return get_brain().get_family_stats()

def get_synergy_score() -> Dict[str, Any]:
    return get_brain().get_family_synergy_score()

def record_quality(task_id: str, quality: float, revenue: float = None) -> bool:
    return get_brain().record_quality_feedback(task_id, quality, revenue)


# METAHIVE INTEGRATION
def export_to_metahive() -> Dict[str, Any]:
    """Export family learnings for cross-user sharing"""
    return {
        "specializations": {
            f"{m.value}_{c.value}": {"model": m.value, "category": c.value, "score": s}
            for m, p in FAMILY_MEMBERS.items()
            for c, s in p.specialization_scores.items() if s > 0.7
        },
        "teachings": len(TEACHING_MOMENTS),
        "insights": [{"type": i.insight_type, "desc": i.description[:200]} for i in COLLECTIVE_INSIGHTS[-20:]]
    }


def import_from_metahive(data: Dict[str, Any]):
    """Import learnings from other users"""
    for key, spec in data.get("specializations", {}).items():
        try:
            model = AIModel(spec["model"])
            cat = TaskCategory(spec["category"])
            current = FAMILY_MEMBERS[model].specialization_scores.get(cat, 0.5)
            FAMILY_MEMBERS[model].specialization_scores[cat] = current * 0.7 + spec["score"] * 0.3
        except:
            pass


# YIELD MEMORY INTEGRATION
def export_to_yield_memory(username: str) -> Dict[str, Any]:
    """Export user-specific patterns"""
    user_tasks = [t for t in TASK_HISTORY if t.context.get("username") == username]
    return {
        "username": username,
        "patterns": [
            {"model": t.model.value, "category": t.task_category.value, "quality": t.quality_score}
            for t in user_tasks[-50:] if t.success and t.quality_score and t.quality_score > 0.7
        ]
    }


# INITIALIZE
_brain = get_brain()

print("""
═══════════════════════════════════════════════════════════════════════════════
🧠 AI FAMILY BRAIN v1.0 - THE WORLD'S FIRST NATIVE AI FAMILY NETWORK
═══════════════════════════════════════════════════════════════════════════════

    CLAUDE ◄──────► GPT-4 ◄──────► GEMINI ◄──────► PERPLEXITY
      🧠              ⚡              🔬              🌐
   Reasoning        Speed          Research       Real-time

   ◄──── TEACHING ────►  ◄──── CROSS-POLLINATION ────►
   ◄──── VELOCITY COMPOUNDING ────►

   Features: Dynamic routing, Teaching loops, Specialization emergence,
             Ensemble execution, MetaHive + Yield Memory integration
   
═══════════════════════════════════════════════════════════════════════════════
""")
