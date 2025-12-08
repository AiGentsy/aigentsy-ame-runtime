"""
Template Library - Best-in-class document templates
Each template is industry-standard, professionally vetted, and battle-tested

Sources:
- Legal: Y Combinator, SBA, Open Source Legal
- SaaS: Stripe-style, OpenAPI, ReadMe.io
- Marketing: HubSpot, Google Marketing Platform
- Social: Buffer, Hootsuite, AspireIQ
"""

from typing import Dict, List
from datetime import datetime

# ===================================================================
# LEGAL KIT TEMPLATES
# ===================================================================

LEGAL_TEMPLATES = {
    "safe_cap": {
        "name": "SAFE Agreement (with Valuation Cap)",
        "source": "Y Combinator (official)",
        "source_url": "https://www.ycombinator.com/documents",
        "retail_value": 500,
        "description": "Industry-standard startup investment agreement with valuation cap. The actual YC template used by thousands of startups.",
        "use_cases": ["Early-stage fundraising", "Seed rounds", "Angel investments"],
        "base_template_path": "/home/claude/templates/legal/yc_safe_cap.docx",
        "smart_fields": {
            "[Company Name]": "company_name",
            "[Investor Name]": "investor_name", 
            "$[_____________]": "purchase_amount",
            "[Date of Safe]": "date",
            "[State of Incorporation]": "state_of_incorporation",
            "[Governing Law Jurisdiction]": "governing_law",
            "[name]": "signatory_name",
            "[title]": "signatory_title"
        },
        "jurisdictions": ["all_us", "delaware_corp"],
        "quality_score": 99,  # YC standard = gold standard
        "estimated_time_to_customize": "3 minutes",
        "category": "Investment"
    },
    
    "safe_discount": {
        "name": "SAFE Agreement (with Discount)",
        "source": "Y Combinator (official)",
        "source_url": "https://www.ycombinator.com/documents",
        "retail_value": 500,
        "description": "SAFE with discount rate instead of valuation cap. Used when valuation is uncertain.",
        "use_cases": ["Pre-seed funding", "Early angel rounds", "Friends & family"],
        "base_template_path": "/home/claude/templates/legal/yc_safe_discount.docx",
        "smart_fields": {
            "[Company Name]": "company_name",
            "[Investor Name]": "investor_name",
            "$[_____________]": "purchase_amount",
            "[Date of Safe]": "date",
            "[State of Incorporation]": "state_of_incorporation",
            "[Governing Law Jurisdiction]": "governing_law",
            "[name]": "signatory_name",
            "[title]": "signatory_title"
        },
        "jurisdictions": ["all_us", "delaware_corp"],
        "quality_score": 99,
        "estimated_time_to_customize": "3 minutes",
        "category": "Investment"
    },
    
    "safe_mfn": {
        "name": "SAFE Agreement (MFN - Most Favored Nation)",
        "source": "Y Combinator (official)",
        "source_url": "https://www.ycombinator.com/documents",
        "retail_value": 500,
        "description": "SAFE with MFN provision - investor gets best terms given to any future investor.",
        "use_cases": ["Lead investors", "Strategic angels", "Early rounds with uncertain terms"],
        "base_template_path": "/home/claude/templates/legal/yc_safe_mfn.docx",
        "smart_fields": {
            "[Company Name]": "company_name",
            "[Investor Name]": "investor_name",
            "$[_____________]": "purchase_amount",
            "[Date of Safe]": "date",
            "[State of Incorporation]": "state_of_incorporation",
            "[Governing Law Jurisdiction]": "governing_law",
            "[name]": "signatory_name",
            "[title]": "signatory_title"
        },
        "jurisdictions": ["all_us", "delaware_corp"],
        "quality_score": 99,
        "estimated_time_to_customize": "3 minutes",
        "category": "Investment"
    },
    
    "pro_rata_side_letter": {
        "name": "Pro Rata Side Letter",
        "source": "Y Combinator (official)",
        "source_url": "https://www.ycombinator.com/documents",
        "retail_value": 300,
        "description": "Grants investor right to participate in future funding rounds to maintain ownership percentage.",
        "use_cases": ["SAFE agreements", "Early investor rights", "Maintaining equity stakes"],
        "base_template_path": "/home/claude/templates/legal/pro_rata_side_letter.docx",
        "smart_fields": {
            "[Company Name]": "company_name",
            "[Investor Name]": "investor_name",
            "[Date]": "date",
            "[State of Incorporation]": "state_of_incorporation",
            "[name]": "signatory_name",
            "[title]": "signatory_title"
        },
        "jurisdictions": ["all_us", "delaware_corp"],
        "quality_score": 98,
        "estimated_time_to_customize": "2 minutes",
        "category": "Investment"
    },
    
    "nda_mutual": {
        "name": "Mutual Non-Disclosure Agreement",
        "source": "Law Insider (community-vetted)",
        "source_url": "https://www.lawinsider.com/contracts",
        "retail_value": 300,
        "description": "Two-way confidentiality protection for business partnerships",
        "use_cases": ["Joint ventures", "Partnership discussions", "M&A preliminary talks"],
        "base_template_path": "templates/legal/nda_mutual.docx",
        "smart_fields": {
            "party_a_name": "First Party Name",
            "party_b_name": "Second Party Name",
            "effective_date": "Effective Date",
            "term_months": "Agreement Term (months)",
            "jurisdiction": "Governing Jurisdiction"
        },
        "jurisdictions": ["all_us", "uk", "canada"],
        "quality_score": 95,
        "estimated_time_to_customize": "3 minutes",
        "category": "Confidentiality"
    },
    
    "nda_oneway": {
        "name": "One-Way NDA (Disclosing Party Protected)",
        "source": "SBA Public Domain",
        "source_url": "https://www.sba.gov/business-guide",
        "retail_value": 200,
        "description": "Protects your confidential information when disclosed to contractors/vendors",
        "use_cases": ["Hiring contractors", "Vendor relationships", "Pitch meetings"],
        "base_template_path": "templates/legal/nda_oneway.docx",
        "smart_fields": {
            "disclosing_party": "Your Company Name",
            "receiving_party": "Recipient Name",
            "purpose": "Purpose of Disclosure",
            "effective_date": "Effective Date",
            "term_years": "Agreement Term (years)"
        },
        "jurisdictions": ["all_us"],
        "quality_score": 92,
        "estimated_time_to_customize": "2 minutes",
        "category": "Confidentiality"
    },
    
    "service_agreement": {
        "name": "Professional Services Agreement",
        "source": "AIGA-style (design industry standard)",
        "source_url": "https://www.aiga.org/resources",
        "retail_value": 400,
        "description": "Comprehensive service contract with IP protection and payment terms",
        "use_cases": ["Client projects", "Consulting engagements", "Professional services"],
        "base_template_path": "templates/legal/service_agreement.docx",
        "smart_fields": {
            "service_provider": "Your Company Name",
            "client_name": "Client Name",
            "services_description": "Description of Services",
            "total_fee": "Total Project Fee",
            "payment_schedule": "Payment Terms",
            "start_date": "Project Start Date",
            "completion_date": "Expected Completion"
        },
        "jurisdictions": ["all_us"],
        "quality_score": 96,
        "estimated_time_to_customize": "8 minutes",
        "category": "Service Contract"
    },
    
    "ip_assignment": {
        "name": "Intellectual Property Assignment",
        "source": "Open Source Legal Templates",
        "source_url": "https://github.com/docassemble",
        "retail_value": 350,
        "description": "Transfers IP ownership from contractor to company",
        "use_cases": ["Contractor work", "Work-for-hire", "IP acquisition"],
        "base_template_path": "templates/legal/ip_assignment.docx",
        "smart_fields": {
            "assignor_name": "Contractor/Creator Name",
            "assignee_name": "Company Receiving IP",
            "work_description": "Description of Work/IP",
            "effective_date": "Assignment Date",
            "consideration": "Payment/Consideration"
        },
        "jurisdictions": ["all_us", "copyright_standard"],
        "quality_score": 93,
        "estimated_time_to_customize": "4 minutes",
        "category": "Intellectual Property"
    }
}

# ===================================================================
# SAAS KIT TEMPLATES
# ===================================================================

SAAS_TEMPLATES = {
    "api_documentation": {
        "name": "API Documentation (Stripe-Style)",
        "source": "Modeled after Stripe API Docs",
        "source_url": "https://stripe.com/docs/api",
        "retail_value": 2000,
        "description": "Developer-friendly API documentation with code examples",
        "use_cases": ["API launches", "Developer onboarding", "Technical documentation"],
        "base_template_path": "templates/saas/api_docs_stripe_style.docx",
        "smart_fields": {
            "api_name": "API Name",
            "base_url": "Base API URL",
            "auth_method": "Authentication Method",
            "company_name": "Company Name",
            "support_email": "Support Email"
        },
        "quality_score": 99,
        "estimated_time_to_customize": "30 minutes",
        "category": "Technical Documentation"
    },
    
    "sla_template": {
        "name": "Service Level Agreement",
        "source": "Industry standard SLA structure",
        "source_url": "https://www.atlassian.com/",
        "retail_value": 800,
        "description": "Uptime guarantees, support response times, and remediation terms",
        "use_cases": ["Enterprise sales", "B2B SaaS", "Managed services"],
        "base_template_path": "templates/saas/sla_template.docx",
        "smart_fields": {
            "service_name": "Service/Product Name",
            "uptime_guarantee": "Uptime % (e.g., 99.9%)",
            "support_hours": "Support Availability",
            "response_time": "Ticket Response Time",
            "provider_name": "Service Provider"
        },
        "quality_score": 94,
        "estimated_time_to_customize": "10 minutes",
        "category": "Service Agreement"
    },
    
    "technical_spec": {
        "name": "Technical Specification Document",
        "source": "Engineering documentation best practices",
        "source_url": "https://swagger.io/resources/",
        "retail_value": 1500,
        "description": "Detailed technical requirements and system architecture",
        "use_cases": ["Product development", "Engineering handoffs", "Stakeholder alignment"],
        "base_template_path": "templates/saas/technical_spec.docx",
        "smart_fields": {
            "project_name": "Project Name",
            "author": "Document Author",
            "date": "Creation Date",
            "version": "Version Number",
            "stakeholders": "Key Stakeholders"
        },
        "quality_score": 91,
        "estimated_time_to_customize": "45 minutes",
        "category": "Technical Documentation"
    },
    
    "saas_terms": {
        "name": "SaaS Terms of Service",
        "source": "Industry-standard SaaS terms",
        "source_url": "https://termly.io/resources/templates/",
        "retail_value": 600,
        "description": "Legal terms for SaaS subscription service",
        "use_cases": ["Product launches", "User agreements", "Legal compliance"],
        "base_template_path": "templates/saas/saas_terms.docx",
        "smart_fields": {
            "company_name": "Company Name",
            "service_name": "Service Name",
            "governing_law": "Governing State/Country",
            "contact_email": "Legal Contact Email"
        },
        "quality_score": 90,
        "estimated_time_to_customize": "5 minutes",
        "category": "Legal"
    }
}

# ===================================================================
# MARKETING KIT TEMPLATES
# ===================================================================

MARKETING_TEMPLATES = {
    "campaign_brief": {
        "name": "Marketing Campaign Brief",
        "source": "HubSpot Marketing Framework",
        "source_url": "https://www.hubspot.com/resources",
        "retail_value": 500,
        "description": "Strategic campaign planning document with objectives and KPIs",
        "use_cases": ["Campaign planning", "Client presentations", "Team alignment"],
        "base_template_path": "templates/marketing/campaign_brief.docx",
        "smart_fields": {
            "campaign_name": "Campaign Name",
            "client_brand": "Client/Brand Name",
            "objectives": "Campaign Objectives",
            "target_audience": "Target Audience",
            "budget": "Total Budget",
            "timeline": "Campaign Timeline"
        },
        "quality_score": 96,
        "estimated_time_to_customize": "15 minutes",
        "category": "Strategy"
    },
    
    "seo_audit": {
        "name": "SEO Audit Report",
        "source": "Google Marketing Platform style",
        "source_url": "https://marketingplatform.google.com/",
        "retail_value": 800,
        "description": "Comprehensive SEO analysis with actionable recommendations",
        "use_cases": ["Client deliverables", "Website optimization", "Technical SEO"],
        "base_template_path": "templates/marketing/seo_audit.docx",
        "smart_fields": {
            "website_url": "Website URL",
            "audit_date": "Audit Date",
            "analyst_name": "SEO Analyst",
            "client_name": "Client Name"
        },
        "quality_score": 93,
        "estimated_time_to_customize": "20 minutes",
        "category": "Analysis"
    },
    
    "content_strategy": {
        "name": "Content Strategy Deck",
        "source": "Agency content planning framework",
        "source_url": "https://contentmarketinginstitute.com/",
        "retail_value": 1200,
        "description": "12-month content plan with distribution strategy",
        "use_cases": ["Content planning", "Editorial calendars", "Marketing strategy"],
        "base_template_path": "templates/marketing/content_strategy.docx",
        "smart_fields": {
            "brand_name": "Brand Name",
            "timeframe": "Planning Period",
            "content_pillars": "Key Content Themes",
            "distribution_channels": "Distribution Channels"
        },
        "quality_score": 94,
        "estimated_time_to_customize": "25 minutes",
        "category": "Strategy"
    },
    
    "media_plan": {
        "name": "Media Planning Template",
        "source": "Nielsen media planning structure",
        "source_url": "https://www.nielsen.com/",
        "retail_value": 1000,
        "description": "Media mix planning with budget allocation and reach metrics",
        "use_cases": ["Paid media", "Budget planning", "Channel strategy"],
        "base_template_path": "templates/marketing/media_plan.docx",
        "smart_fields": {
            "campaign_name": "Campaign Name",
            "total_budget": "Total Media Budget",
            "flight_dates": "Campaign Flight Dates",
            "target_audience": "Target Demographics"
        },
        "quality_score": 92,
        "estimated_time_to_customize": "30 minutes",
        "category": "Planning"
    }
}

# ===================================================================
# SOCIAL KIT TEMPLATES
# ===================================================================

SOCIAL_TEMPLATES = {
    "content_calendar": {
        "name": "Social Media Content Calendar",
        "source": "Buffer best practices",
        "source_url": "https://buffer.com/resources/",
        "retail_value": 300,
        "description": "30-day content calendar with post scheduling and themes",
        "use_cases": ["Social planning", "Client management", "Team coordination"],
        "base_template_path": "templates/social/content_calendar.docx",
        "smart_fields": {
            "brand_name": "Brand Name",
            "month_year": "Planning Month",
            "platforms": "Social Platforms",
            "posting_frequency": "Posts per Week"
        },
        "quality_score": 95,
        "estimated_time_to_customize": "10 minutes",
        "category": "Planning"
    },
    
    "influencer_brief": {
        "name": "Influencer Campaign Brief",
        "source": "Creator marketplace standard",
        "source_url": "https://www.aspireiq.com/",
        "retail_value": 600,
        "description": "Campaign brief for influencer partnerships",
        "use_cases": ["Influencer outreach", "Campaign management", "Partnership terms"],
        "base_template_path": "templates/social/influencer_brief.docx",
        "smart_fields": {
            "brand_name": "Brand Name",
            "campaign_name": "Campaign Name",
            "deliverables": "Content Deliverables",
            "compensation": "Compensation Terms",
            "timeline": "Campaign Timeline"
        },
        "quality_score": 93,
        "estimated_time_to_customize": "12 minutes",
        "category": "Partnership"
    },
    
    "rate_card": {
        "name": "Creator Rate Card",
        "source": "Influencer Marketing Hub standard",
        "source_url": "https://influencermarketinghub.com/",
        "retail_value": 200,
        "description": "Professional rate card for social media services",
        "use_cases": ["Client pricing", "Service packages", "Influencer bookings"],
        "base_template_path": "templates/social/rate_card.docx",
        "smart_fields": {
            "creator_name": "Creator/Brand Name",
            "instagram_handle": "Instagram Handle",
            "followers": "Follower Count",
            "engagement_rate": "Avg. Engagement Rate"
        },
        "quality_score": 91,
        "estimated_time_to_customize": "5 minutes",
        "category": "Pricing"
    },
    
    "brand_guidelines": {
        "name": "Social Media Brand Guidelines",
        "source": "Agency brand standards",
        "source_url": "https://www.canva.com/templates/",
        "retail_value": 800,
        "description": "Visual and voice guidelines for social media presence",
        "use_cases": ["Brand consistency", "Team training", "Agency handoffs"],
        "base_template_path": "templates/social/brand_guidelines.docx",
        "smart_fields": {
            "brand_name": "Brand Name",
            "primary_colors": "Brand Colors",
            "fonts": "Brand Fonts",
            "tone_of_voice": "Brand Voice Description"
        },
        "quality_score": 94,
        "estimated_time_to_customize": "20 minutes",
        "category": "Brand"
    }
}

# ===================================================================
# GENERAL KIT (HYBRID)
# ===================================================================

GENERAL_TEMPLATES = {
    "proposal_template": {
        "name": "Business Proposal Template",
        "source": "Professional services standard",
        "retail_value": 400,
        "description": "Comprehensive proposal for services or projects",
        "use_cases": ["Client proposals", "Project bids", "Service offerings"],
        "base_template_path": "templates/general/business_proposal.docx",
        "smart_fields": {
            "your_company": "Your Company Name",
            "client_name": "Client Name",
            "project_name": "Project/Service Name",
            "total_investment": "Total Investment",
            "timeline": "Project Timeline"
        },
        "quality_score": 92,
        "estimated_time_to_customize": "20 minutes",
        "category": "Sales"
    },
    
    "invoice_template": {
        "name": "Professional Invoice",
        "source": "Industry standard",
        "retail_value": 50,
        "description": "Clean, professional invoice template",
        "use_cases": ["Client billing", "Payment collection", "Record keeping"],
        "base_template_path": "templates/general/invoice.docx",
        "smart_fields": {
            "company_name": "Your Company",
            "client_name": "Bill To",
            "invoice_number": "Invoice #",
            "invoice_date": "Date",
            "due_date": "Due Date",
            "total_amount": "Amount Due"
        },
        "quality_score": 90,
        "estimated_time_to_customize": "2 minutes",
        "category": "Finance"
    }
}

# ===================================================================
# KIT MAPPINGS
# ===================================================================

KIT_TEMPLATE_MAP = {
    "legal": LEGAL_TEMPLATES,
    "saas": SAAS_TEMPLATES,
    "marketing": MARKETING_TEMPLATES,
    "social": SOCIAL_TEMPLATES,
    "general": {
        **GENERAL_TEMPLATES,
        # Include subset of other kits
        "nda_oneway": LEGAL_TEMPLATES["nda_oneway"],
        "service_agreement": LEGAL_TEMPLATES["service_agreement"],
        "proposal_template": GENERAL_TEMPLATES["proposal_template"]
    }
}

def get_kit_templates(kit_type: str) -> Dict:
    """Get all templates for a specific kit"""
    return KIT_TEMPLATE_MAP.get(kit_type, GENERAL_TEMPLATES)

def calculate_kit_value(kit_type: str) -> int:
    """Calculate total retail value of all templates in kit"""
    templates = get_kit_templates(kit_type)
    return sum(t["retail_value"] for t in templates.values())

def get_template_count(kit_type: str) -> int:
    """Get number of templates in kit"""
    return len(get_kit_templates(kit_type))

# ===================================================================
# KIT SUMMARY (For Dashboard Display)
# ===================================================================

KIT_SUMMARY = {
    "legal": {
        "name": "Legal Kit",
        "template_count": len(LEGAL_TEMPLATES),
        "total_retail_value": calculate_kit_value("legal"),
        "headline": "Professional legal documents ready to sell",
        "key_deliverables": ["SAFE Agreements", "NDAs", "Service Contracts", "IP Assignments"]
    },
    "saas": {
        "name": "SaaS Kit",
        "template_count": len(SAAS_TEMPLATES),
        "total_retail_value": calculate_kit_value("saas"),
        "headline": "Enterprise-grade technical documentation",
        "key_deliverables": ["API Documentation", "SLAs", "Technical Specs", "Terms of Service"]
    },
    "marketing": {
        "name": "Marketing Kit",
        "template_count": len(MARKETING_TEMPLATES),
        "total_retail_value": calculate_kit_value("marketing"),
        "headline": "Agency-quality marketing deliverables",
        "key_deliverables": ["Campaign Briefs", "SEO Audits", "Content Strategy", "Media Plans"]
    },
    "social": {
        "name": "Social Kit",
        "template_count": len(SOCIAL_TEMPLATES),
        "total_retail_value": calculate_kit_value("social"),
        "headline": "Creator-focused social media templates",
        "key_deliverables": ["Content Calendars", "Brand Guidelines", "Rate Cards", "Influencer Briefs"]
    },
    "general": {
        "name": "General Kit",
        "template_count": len(GENERAL_TEMPLATES) + 3,  # Includes subset from other kits
        "total_retail_value": calculate_kit_value("general"),
        "headline": "Essential business templates for any venture",
        "key_deliverables": ["Proposals", "Invoices", "NDAs", "Service Agreements"]
    }
}
