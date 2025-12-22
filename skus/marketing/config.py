"""
MARKETING SKU CONFIGURATION
Complete marketing agency with autonomous campaigns, partnerships, and competitive intelligence
"""

MARKETING_SKU_CONFIG = {
    'sku_id': 'marketing',
    'sku_name': 'Marketing - Launch Assets Pack',
    'sku_version': '2.1.0',
    'sku_type': 'template',
    'industry': 'marketing',
    'description': 'Complete marketing agency with autonomous campaigns, partnerships, and competitive intelligence',
    
    # Storefront templates (user picks one on signup)
    'storefront_templates': {
        'professional': {
            'file': 'variation-1-professional.html',
            'name': 'Professional/Direct',
            'best_for': 'B2B, SaaS, agencies'
        },
        'boutique': {
            'file': 'variation-2-boutique.html',
            'name': 'Boutique/Aspirational',
            'best_for': 'Coaching, consulting, premium services'
        },
        'disruptive': {
            'file': 'variation-3-disruptive.html',
            'name': 'Disruptive/Bold',
            'best_for': 'Startups, tech companies'
        }
    },
    
    # Email sequences (AME uses these)
    'email_sequences': {
        'welcome': [
            {
                'subject': 'Welcome to {business_name}!',
                'body': 'Hi {first_name}, Welcome! Your marketing agency is live. Dashboard: {dashboard_url}',
                'send_delay_hours': 0
            }
        ],
        'partnership_proposal': [
            {
                'subject': 'Partnership opportunity: {partner_name}',
                'body': 'Hi {partner_name}, I see an opportunity to collaborate...',
                'requires_approval': True
            }
        ]
    },
    
    # C-Suite configuration
    'csuite_agents': {
        'cmo': {
            'class': 'MarketingCMO',
            'capabilities': ['partnership_proposals', 'competitive_alerts', 'email_sequences']
        },
        'cfo': {'class': 'BaseCFO', 'traditional_cost': 180000},
        'ceo': {'class': 'MarketingCEO', 'capabilities': ['strategic_analysis', 'partnership_strategy']},
        'coo': {'class': 'BaseCOO', 'monitors': ['ame', 'amg', 'campaigns']}
    },
    
    # Autonomous systems
    'autonomous_systems': {
        'ame': {'enabled': True, 'auto_pitch_delay_hours': 4},
        'amg': {'enabled': True, 'platforms': 8, 'scan_frequency': 'hourly'},
        'campaign_optimizer': {'enabled': True, 'frequency': 'continuous'},
        'competitive_intel': {'enabled': True, 'monitors': 'competitors'},
        'partnership_matcher': {'enabled': True, 'min_match_score': 0.75}
    },
    
    # Dashboard widgets
    'dashboard_widgets': {
        'campaigns': True,
        'partnerships': True,
        'competitive_intel': True,
        'revenue_tracking': True
    }
}
