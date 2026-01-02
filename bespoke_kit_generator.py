# bespoke_kit_generator.py
# ═══════════════════════════════════════════════════════════════════════════════
# 
# BESPOKE BUSINESS KIT GENERATOR
# Analyzes user's custom business idea and generates a tailored kit with:
# - Appropriate base kit selection
# - Custom offerings based on their description
# - Tailored first moves
# - Specific revenue paths
# - Actionable templates
#
# ═══════════════════════════════════════════════════════════════════════════════

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

# Try to import LLM for advanced analysis
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    HAS_LLM = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
except:
    HAS_LLM = False


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORD DETECTION FOR BASE KIT
# ═══════════════════════════════════════════════════════════════════════════════

BASE_KIT_KEYWORDS = {
    "saas": [
        "software", "app", "tool", "api", "saas", "platform", "automation",
        "dashboard", "analytics", "integration", "plugin", "extension",
        "bot", "script", "code", "developer", "tech", "ai tool", "workflow"
    ],
    "legal": [
        "legal", "law", "attorney", "lawyer", "contract", "nda", "ip",
        "intellectual property", "compliance", "regulation", "license",
        "trademark", "copyright", "patent", "paralegal", "notary"
    ],
    "marketing": [
        "marketing", "seo", "ads", "advertising", "growth", "traffic",
        "leads", "funnel", "email", "campaign", "ppc", "social ads",
        "conversion", "landing page", "copywriting", "branding"
    ],
    "social": [
        "social media", "content", "creator", "influencer", "youtube",
        "tiktok", "instagram", "reels", "video", "podcast", "streaming",
        "community", "followers", "engagement", "viral"
    ],
    "ecommerce": [
        "ecommerce", "store", "shop", "product", "dropship", "amazon",
        "etsy", "shopify", "physical product", "inventory", "fulfillment",
        "wholesale", "retail", "merchandise"
    ],
    "consulting": [
        "consulting", "coach", "advisor", "mentor", "strategy", "expert",
        "freelance", "agency", "service", "b2b", "enterprise"
    ],
    "creative": [
        "design", "art", "music", "writing", "photography", "video production",
        "animation", "illustration", "graphic", "creative", "portfolio"
    ],
    "education": [
        "course", "training", "teaching", "tutoring", "education", "learn",
        "workshop", "bootcamp", "certification", "coaching", "curriculum"
    ],
    "finance": [
        "finance", "accounting", "bookkeeping", "tax", "investment",
        "trading", "crypto", "fintech", "payments", "billing"
    ],
    "health": [
        "health", "wellness", "fitness", "nutrition", "therapy", "medical",
        "healthcare", "telehealth", "mental health", "coaching"
    ]
}

# Blocked/restricted business types
RESTRICTED_KEYWORDS = [
    "adult", "xxx", "porn", "gambling", "casino", "weapons", "drugs",
    "illegal", "hack", "scam", "fraud", "counterfeit"
]


@dataclass
class BespokeKit:
    """Generated bespoke kit for a custom business"""
    kit_id: str
    username: str
    custom_input: str
    base_kit: str  # The closest standard kit
    business_name: str
    business_type: str
    you_are: str
    offerings: List[Dict[str, Any]]
    targets: List[str]
    first_moves: List[str]
    revenue_path: str
    first_pitch: str
    templates: List[Dict[str, str]]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 0.0
    flags: List[str] = field(default_factory=list)


def detect_base_kit(custom_input: str) -> tuple[str, float]:
    """
    Analyze custom input and determine the best base kit.
    Returns (kit_name, confidence_score)
    """
    if not custom_input:
        return "general", 0.0
    
    text = custom_input.lower()
    
    # Check for restricted content first
    for keyword in RESTRICTED_KEYWORDS:
        if keyword in text:
            return "restricted", 1.0
    
    # Score each kit based on keyword matches
    scores = {}
    for kit, keywords in BASE_KIT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        # Boost for exact phrase matches
        score += sum(2 for kw in keywords if f" {kw} " in f" {text} ")
        scores[kit] = score
    
    if not scores or max(scores.values()) == 0:
        return "general", 0.3
    
    best_kit = max(scores, key=scores.get)
    max_score = scores[best_kit]
    
    # Calculate confidence (0-1)
    confidence = min(1.0, max_score / 5)  # 5+ matches = 100% confidence
    
    return best_kit, confidence


def extract_business_elements(custom_input: str) -> Dict[str, Any]:
    """
    Extract business elements from the custom input using pattern matching.
    """
    text = custom_input.lower()
    
    elements = {
        "has_target_audience": False,
        "target_hints": [],
        "has_pricing": False,
        "price_hints": [],
        "has_deliverable": False,
        "deliverable_hints": [],
        "has_platform": False,
        "platform_hints": []
    }
    
    # Target audience patterns
    target_patterns = [
        r"for\s+([\w\s]+?)(?:\.|,|who|that)",
        r"help\s+([\w\s]+?)(?:\s+with|\s+to|\.|,)",
        r"(small business|startup|enterprise|creator|freelancer|agency)",
    ]
    for pattern in target_patterns:
        matches = re.findall(pattern, text)
        if matches:
            elements["has_target_audience"] = True
            elements["target_hints"].extend(matches)
    
    # Pricing patterns
    price_patterns = [
        r"\$(\d+)",
        r"(\d+)\s*(?:dollars|usd|per month|/mo|/month)",
        r"(free|freemium|subscription|one-time|hourly)"
    ]
    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        if matches:
            elements["has_pricing"] = True
            elements["price_hints"].extend(matches)
    
    # Deliverable patterns
    deliverable_patterns = [
        r"(build|create|make|deliver|provide|offer)\s+([\w\s]+?)(?:\.|,|for|to)",
        r"(tool|app|service|product|course|template|guide)"
    ]
    for pattern in deliverable_patterns:
        matches = re.findall(pattern, text)
        if matches:
            elements["has_deliverable"] = True
            elements["deliverable_hints"].extend([m[-1] if isinstance(m, tuple) else m for m in matches])
    
    # Platform patterns
    platform_patterns = [
        r"(shopify|wordpress|notion|airtable|zapier|stripe|gumroad)",
        r"(instagram|tiktok|youtube|twitter|linkedin|facebook)",
        r"(upwork|fiverr|toptal|freelancer)"
    ]
    for pattern in platform_patterns:
        matches = re.findall(pattern, text)
        if matches:
            elements["has_platform"] = True
            elements["platform_hints"].extend(matches)
    
    return elements


def generate_bespoke_offerings(base_kit: str, custom_input: str, elements: Dict) -> List[Dict[str, Any]]:
    """
    Generate custom offerings based on base kit and extracted elements.
    """
    # Base offerings by kit
    base_offerings = {
        "saas": [
            {"name": "Micro-Tool", "price_range": "$50-200/mo", "type": "subscription"},
            {"name": "API Access", "price_range": "$200-500/mo", "type": "subscription"},
            {"name": "Custom Integration", "price_range": "$2,000-10,000", "type": "project"},
            {"name": "White-Label License", "price_range": "$5,000-20,000", "type": "license"}
        ],
        "legal": [
            {"name": "NDA Draft", "price_range": "$200", "type": "fixed"},
            {"name": "Contract Review", "price_range": "$300-500", "type": "fixed"},
            {"name": "IP Assignment", "price_range": "$500-1,000", "type": "fixed"},
            {"name": "Compliance Audit", "price_range": "$1,500-3,000", "type": "project"}
        ],
        "marketing": [
            {"name": "SEO Audit", "price_range": "$500", "type": "fixed"},
            {"name": "Ad Campaign Setup", "price_range": "$1,000-2,000", "type": "project"},
            {"name": "Monthly Retainer", "price_range": "$2,000-5,000/mo", "type": "subscription"},
            {"name": "Landing Page", "price_range": "$500-1,500", "type": "project"}
        ],
        "social": [
            {"name": "Content Package", "price_range": "$200-500", "type": "fixed"},
            {"name": "Monthly Management", "price_range": "$1,000-3,000/mo", "type": "subscription"},
            {"name": "Sponsored Post", "price_range": "$500-5,000", "type": "fixed"},
            {"name": "Creator Kit", "price_range": "$100-300", "type": "product"}
        ],
        "consulting": [
            {"name": "Strategy Session", "price_range": "$200-500", "type": "fixed"},
            {"name": "Hourly Consulting", "price_range": "$150-300/hr", "type": "hourly"},
            {"name": "Monthly Advisory", "price_range": "$2,000-5,000/mo", "type": "subscription"},
            {"name": "Workshop", "price_range": "$1,000-3,000", "type": "fixed"}
        ],
        "education": [
            {"name": "Mini-Course", "price_range": "$50-200", "type": "product"},
            {"name": "Full Course", "price_range": "$500-2,000", "type": "product"},
            {"name": "Coaching Package", "price_range": "$1,000-5,000", "type": "fixed"},
            {"name": "Group Program", "price_range": "$200-500/person", "type": "cohort"}
        ],
        "ecommerce": [
            {"name": "Product", "price_range": "varies", "type": "product"},
            {"name": "Bundle", "price_range": "varies", "type": "product"},
            {"name": "Subscription Box", "price_range": "$30-100/mo", "type": "subscription"},
            {"name": "Wholesale", "price_range": "bulk pricing", "type": "b2b"}
        ],
        "creative": [
            {"name": "Design Package", "price_range": "$500-2,000", "type": "project"},
            {"name": "Custom Commission", "price_range": "$200-1,000", "type": "fixed"},
            {"name": "Template/Asset", "price_range": "$20-100", "type": "product"},
            {"name": "Retainer", "price_range": "$1,500-4,000/mo", "type": "subscription"}
        ],
        "general": [
            {"name": "Consultation", "price_range": "$100-300", "type": "fixed"},
            {"name": "Custom Project", "price_range": "quote-based", "type": "project"},
            {"name": "Hourly Service", "price_range": "$50-150/hr", "type": "hourly"},
            {"name": "Package Deal", "price_range": "$500-2,000", "type": "fixed"}
        ]
    }
    
    offerings = base_offerings.get(base_kit, base_offerings["general"]).copy()
    
    # Customize based on extracted elements
    if elements.get("price_hints"):
        # Try to incorporate user's price ideas
        pass  # Could enhance offerings with detected prices
    
    if elements.get("deliverable_hints"):
        # Add a custom offering based on what they want to deliver
        deliverable = elements["deliverable_hints"][0] if elements["deliverable_hints"] else "service"
        offerings.insert(0, {
            "name": f"Custom {deliverable.title()}",
            "price_range": "quote-based",
            "type": "custom",
            "from_input": True
        })
    
    return offerings


def generate_first_moves(base_kit: str, custom_input: str, elements: Dict) -> List[str]:
    """
    Generate actionable first moves based on the business type.
    """
    base_moves = {
        "saas": [
            "Identify ONE pain point your tool solves",
            "Build an MVP in a weekend (or use no-code)",
            "Get 5 beta users for feedback",
            "Set up Stripe for $50/mo subscriptions",
            "Launch on Product Hunt or social"
        ],
        "legal": [
            "Create 3 template documents (NDA, contract, agreement)",
            "Price your NDA at $200 (market is $500+)",
            "Find 5 startups who need legal docs",
            "Deliver fast (24-48 hours) to build reputation",
            "Get testimonials for your storefront"
        ],
        "marketing": [
            "Offer a free audit to get in the door",
            "Find 3 quick wins they're missing",
            "Package the fix at $500",
            "Show ROI in 30 days",
            "Upsell to monthly retainer"
        ],
        "social": [
            "Package your content as a productized service",
            "Create a '10 posts for $200' offer",
            "Find 3 businesses who need content",
            "Batch create to maximize efficiency",
            "Build a portfolio of wins"
        ],
        "consulting": [
            "Define your specific expertise",
            "Create a signature framework",
            "Offer a $200 strategy session",
            "Deliver actionable insights",
            "Convert to retainer or project"
        ],
        "education": [
            "Outline your course in 5-7 modules",
            "Create the first module as a lead magnet",
            "Price at $200-500 for first cohort",
            "Get 10 students for validation",
            "Iterate based on feedback"
        ],
        "ecommerce": [
            "Validate demand before inventory",
            "Start with 1-3 products max",
            "Set up Shopify or Etsy",
            "Create product photos that sell",
            "Run small test ads ($50-100)"
        ],
        "creative": [
            "Build a portfolio of 5-10 pieces",
            "Create a signature style",
            "Price based on value, not time",
            "Find your ideal client type",
            "Package services for easy buying"
        ],
        "general": [
            "Identify your #1 monetizable skill",
            "Find someone with a problem that skill solves",
            "Offer to solve it for a fair price",
            "Deliver, get testimonial",
            "Repeat and refine"
        ]
    }
    
    moves = base_moves.get(base_kit, base_moves["general"]).copy()
    
    # Customize based on extracted targets
    if elements.get("target_hints"):
        target = elements["target_hints"][0]
        moves[2] = f"Find 5 {target}s who need this"
    
    return moves


def generate_templates(base_kit: str, custom_input: str) -> List[Dict[str, str]]:
    """
    Generate relevant templates for the bespoke kit.
    """
    base_templates = {
        "saas": [
            {"id": "pricing_page", "name": "SaaS Pricing Page Template", "type": "html"},
            {"id": "onboarding_email", "name": "User Onboarding Sequence", "type": "email"},
            {"id": "api_docs", "name": "API Documentation Template", "type": "md"},
            {"id": "terms_of_service", "name": "SaaS Terms of Service", "type": "legal"},
            {"id": "changelog", "name": "Product Changelog Template", "type": "md"}
        ],
        "legal": [
            {"id": "nda", "name": "NDA Template", "type": "docx"},
            {"id": "service_agreement", "name": "Service Agreement", "type": "docx"},
            {"id": "ip_assignment", "name": "IP Assignment", "type": "docx"},
            {"id": "privacy_policy", "name": "Privacy Policy Template", "type": "md"},
            {"id": "engagement_letter", "name": "Client Engagement Letter", "type": "docx"}
        ],
        "marketing": [
            {"id": "seo_audit", "name": "SEO Audit Template", "type": "xlsx"},
            {"id": "campaign_brief", "name": "Campaign Brief", "type": "docx"},
            {"id": "email_sequence", "name": "Email Sequence Templates", "type": "md"},
            {"id": "landing_page", "name": "Landing Page Wireframe", "type": "html"},
            {"id": "analytics_report", "name": "Monthly Analytics Report", "type": "xlsx"}
        ],
        "social": [
            {"id": "content_calendar", "name": "Content Calendar", "type": "xlsx"},
            {"id": "caption_templates", "name": "Caption Templates", "type": "md"},
            {"id": "brand_guidelines", "name": "Brand Voice Guidelines", "type": "docx"},
            {"id": "media_kit", "name": "Media Kit Template", "type": "pptx"},
            {"id": "collab_contract", "name": "Brand Collaboration Contract", "type": "docx"}
        ],
        "consulting": [
            {"id": "proposal", "name": "Consulting Proposal Template", "type": "docx"},
            {"id": "discovery_call", "name": "Discovery Call Script", "type": "md"},
            {"id": "strategy_deck", "name": "Strategy Presentation", "type": "pptx"},
            {"id": "retainer_agreement", "name": "Retainer Agreement", "type": "docx"},
            {"id": "case_study", "name": "Case Study Template", "type": "md"}
        ],
        "education": [
            {"id": "course_outline", "name": "Course Outline Template", "type": "md"},
            {"id": "lesson_plan", "name": "Lesson Plan Template", "type": "docx"},
            {"id": "student_workbook", "name": "Student Workbook", "type": "docx"},
            {"id": "certificate", "name": "Completion Certificate", "type": "pptx"},
            {"id": "feedback_form", "name": "Student Feedback Form", "type": "md"}
        ],
        "ecommerce": [
            {"id": "product_listing", "name": "Product Listing Template", "type": "md"},
            {"id": "shipping_policy", "name": "Shipping Policy", "type": "md"},
            {"id": "return_policy", "name": "Return Policy", "type": "md"},
            {"id": "inventory_tracker", "name": "Inventory Tracker", "type": "xlsx"},
            {"id": "supplier_agreement", "name": "Supplier Agreement", "type": "docx"}
        ],
        "creative": [
            {"id": "project_brief", "name": "Creative Brief Template", "type": "docx"},
            {"id": "portfolio_page", "name": "Portfolio Page Template", "type": "html"},
            {"id": "quote_template", "name": "Project Quote Template", "type": "docx"},
            {"id": "revision_policy", "name": "Revision Policy", "type": "md"},
            {"id": "license_agreement", "name": "Asset License Agreement", "type": "docx"}
        ],
        "general": [
            {"id": "proposal", "name": "General Proposal Template", "type": "docx"},
            {"id": "invoice", "name": "Invoice Template", "type": "xlsx"},
            {"id": "contract", "name": "Basic Service Contract", "type": "docx"},
            {"id": "onboarding", "name": "Client Onboarding Checklist", "type": "md"},
            {"id": "testimonial", "name": "Testimonial Request Template", "type": "email"}
        ]
    }
    
    return base_templates.get(base_kit, base_templates["general"])


async def generate_bespoke_kit_with_llm(username: str, custom_input: str) -> Optional[BespokeKit]:
    """
    Use LLM to generate a more sophisticated bespoke kit.
    Falls back to rule-based generation if LLM unavailable.
    """
    if not HAS_LLM:
        return generate_bespoke_kit(username, custom_input)
    
    try:
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        system_prompt = """You are a business strategist helping create a bespoke business kit.
        
Given a user's business idea, generate:
1. A clear business_name (2-4 words)
2. A you_are statement (who they are as a business owner)
3. 4 specific offerings with prices
4. 3 target customer types
5. 5 actionable first moves
6. A revenue_path (how they'll make money)
7. A first_pitch (30 words max, what they'd say to get their first customer)

Keep it practical, achievable, and focused on getting to revenue quickly.
Avoid anything explicit, illegal, or harmful.

Respond in JSON format:
{
  "business_name": "...",
  "you_are": "...",
  "offerings": [{"name": "...", "price": "...", "type": "..."}],
  "targets": ["...", "...", "..."],
  "first_moves": ["...", "...", "...", "...", "..."],
  "revenue_path": "...",
  "first_pitch": "..."
}"""

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Business idea: {custom_input}")
        ])
        
        import json
        result = json.loads(response.content)
        
        base_kit, confidence = detect_base_kit(custom_input)
        
        return BespokeKit(
            kit_id=f"bespoke_{username}_{int(datetime.now().timestamp())}",
            username=username,
            custom_input=custom_input,
            base_kit=base_kit,
            business_name=result.get("business_name", "Custom Business"),
            business_type=base_kit,
            you_are=result.get("you_are", "a business owner with valuable skills"),
            offerings=[{"name": o["name"], "price_range": o["price"], "type": o["type"]} for o in result.get("offerings", [])],
            targets=result.get("targets", []),
            first_moves=result.get("first_moves", []),
            revenue_path=result.get("revenue_path", "Provide value, get paid"),
            first_pitch=result.get("first_pitch", "Let me help you solve this problem."),
            templates=generate_templates(base_kit, custom_input),
            confidence=confidence,
            flags=["llm_generated"]
        )
        
    except Exception as e:
        print(f"LLM generation failed: {e}, falling back to rules")
        return generate_bespoke_kit(username, custom_input)


def generate_bespoke_kit(username: str, custom_input: str) -> BespokeKit:
    """
    Generate a bespoke kit using rule-based analysis.
    """
    # Detect base kit
    base_kit, confidence = detect_base_kit(custom_input)
    
    # Check for restricted content
    if base_kit == "restricted":
        return BespokeKit(
            kit_id=f"restricted_{username}",
            username=username,
            custom_input=custom_input,
            base_kit="restricted",
            business_name="Restricted",
            business_type="restricted",
            you_are="This business type is not supported",
            offerings=[],
            targets=[],
            first_moves=["Please choose a different business type"],
            revenue_path="N/A",
            first_pitch="N/A",
            templates=[],
            confidence=1.0,
            flags=["restricted_content"]
        )
    
    # Extract elements from input
    elements = extract_business_elements(custom_input)
    
    # Generate kit components
    offerings = generate_bespoke_offerings(base_kit, custom_input, elements)
    first_moves = generate_first_moves(base_kit, custom_input, elements)
    templates = generate_templates(base_kit, custom_input)
    
    # Generate you_are and other text
    you_are_templates = {
        "saas": "a software builder who creates tools people pay for monthly",
        "legal": "a legal services provider who protects businesses with the right documents",
        "marketing": "a growth expert who helps businesses get more customers",
        "social": "a content creator who turns attention into revenue",
        "consulting": "an expert advisor who solves high-value problems",
        "education": "an educator who packages knowledge into sellable courses",
        "ecommerce": "a product seller who creates and fulfills customer demand",
        "creative": "a creative professional who turns ideas into valuable assets",
        "general": "a business owner with valuable skills to monetize"
    }
    
    revenue_paths = {
        "saas": "Build once, sell subscriptions forever. Your AiGentsy finds users while you improve the product.",
        "legal": "Legal docs are repeat business. One happy client refers more. Automate templates, scale delivery.",
        "marketing": "Land monthly retainers. One client at $2k/mo = $24k/year. Stack 5 clients = $120k.",
        "social": "Content compounds. Build audience, monetize through sponsors, products, and services.",
        "consulting": "Charge for expertise. $200/hr x 20hrs/week = $200k/year. Package into programs to scale.",
        "education": "Create once, sell forever. A $500 course to 100 students = $50k. Build a catalog.",
        "ecommerce": "Profit per unit x volume. Find winners, scale ads, automate fulfillment.",
        "creative": "Retainers for stability, projects for upside. Build portfolio that sells while you sleep.",
        "general": "Start with services for cash flow, productize for scale. Your AiGentsy finds both."
    }
    
    first_pitches = {
        "saas": "What's one task you do every week that should be automated? I'll build the tool.",
        "legal": "Need an NDA or contract? I'll have it ready in 24 hours for $200 flat.",
        "marketing": "I'll audit your marketing and show you 3 quick wins - free. Fixing them is $500.",
        "social": "I'll create 10 posts with captions for your next 2 weeks - $200.",
        "consulting": "What's the #1 problem slowing down your business? Let's solve it together.",
        "education": "I'll teach you [skill] in 4 weeks. You'll be able to [outcome] by the end.",
        "ecommerce": "I've got [product] that solves [problem]. Want to try it?",
        "creative": "I'll create [deliverable] that makes your [thing] stand out. Here's my portfolio.",
        "general": "What's eating up your time? Tell me and I'll see if I can help."
    }
    
    # Build the kit
    return BespokeKit(
        kit_id=f"bespoke_{username}_{int(datetime.now().timestamp())}",
        username=username,
        custom_input=custom_input,
        base_kit=base_kit,
        business_name=f"Custom {base_kit.title()} Business",
        business_type=base_kit,
        you_are=you_are_templates.get(base_kit, you_are_templates["general"]),
        offerings=offerings,
        targets=elements.get("target_hints", ["small businesses", "startups", "entrepreneurs"])[:3] or ["small businesses", "startups", "entrepreneurs"],
        first_moves=first_moves,
        revenue_path=revenue_paths.get(base_kit, revenue_paths["general"]),
        first_pitch=first_pitches.get(base_kit, first_pitches["general"]),
        templates=templates,
        confidence=confidence,
        flags=["rule_generated"] + (["has_targets"] if elements.get("has_target_audience") else [])
    )


# ═══════════════════════════════════════════════════════════════════════════════
# API INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def integrate_bespoke_kit_at_mint(username: str, custom_input: str, company_type: str) -> Dict[str, Any]:
    """
    Called at /mint endpoint to generate bespoke kit for custom businesses.
    Returns kit data to store with user.
    """
    # If not custom/general, just return the standard kit
    if company_type not in ["custom", "general", "whitelabel", ""]:
        return {
            "bespoke": False,
            "kit": company_type,
            "base_kit": company_type
        }
    
    # Generate bespoke kit
    if custom_input and len(custom_input) > 10:
        kit = generate_bespoke_kit(username, custom_input)
        
        if kit.base_kit == "restricted":
            return {
                "bespoke": False,
                "kit": "general",
                "base_kit": "general",
                "error": "Business type not supported"
            }
        
        return {
            "bespoke": True,
            "kit": kit.base_kit,  # Use detected kit as the companyType
            "base_kit": kit.base_kit,
            "bespoke_kit": asdict(kit),
            "confidence": kit.confidence
        }
    
    return {
        "bespoke": False,
        "kit": "general",
        "base_kit": "general"
    }


def get_kit_context_for_agent(user_data: Dict) -> Dict[str, Any]:
    """
    Get the kit context for the growth agent.
    Checks for bespoke kit first, falls back to standard kit.
    """
    bespoke = user_data.get("bespoke_kit")
    
    if bespoke:
        return {
            "is_bespoke": True,
            "kit_name": bespoke.get("business_name", "Custom Business"),
            "business_type": bespoke.get("base_kit", "general"),
            "you_are": bespoke.get("you_are", ""),
            "offerings": bespoke.get("offerings", []),
            "targets": bespoke.get("targets", []),
            "first_moves": bespoke.get("first_moves", []),
            "revenue_path": bespoke.get("revenue_path", ""),
            "first_pitch": bespoke.get("first_pitch", ""),
            "templates": bespoke.get("templates", []),
            "custom_input": bespoke.get("custom_input", "")
        }
    
    # Fall back to standard kit
    return {
        "is_bespoke": False,
        "business_type": user_data.get("companyType", "general")
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test with various inputs
    test_inputs = [
        "I want to build a tool that helps freelancers track their time and invoice clients automatically",
        "I'm a lawyer and want to offer affordable contract reviews for startups",
        "I make TikToks and want to monetize my audience with brand deals",
        "I want to teach people how to use AI for their small business",
        "I have an idea for a dropshipping store selling pet accessories",
        "I'm just exploring, not sure what I want to do yet",
        "I want to sell adult content",  # Should be restricted
    ]
    
    for input_text in test_inputs:
        print(f"\n{'='*60}")
        print(f"INPUT: {input_text[:50]}...")
        kit = generate_bespoke_kit("testuser", input_text)
        print(f"BASE KIT: {kit.base_kit} (confidence: {kit.confidence:.0%})")
        print(f"BUSINESS: {kit.business_name}")
        print(f"YOU ARE: {kit.you_are}")
        print(f"FIRST PITCH: {kit.first_pitch}")
        print(f"FLAGS: {kit.flags}")
