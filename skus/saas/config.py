"""
SAAS SKU CONFIGURATION
Complete API/developer platform with autonomous onboarding, documentation, and support
"""

SAAS_SKU_CONFIG = {
    'sku_id': 'saas',
    'sku_name': 'SaaS - API Documentation System',
    'sku_version': '2.1.0',
    'sku_type': 'template',
    'industry': 'saas_tech',
    'description': 'Complete SaaS platform with developer onboarding, auto-generated docs, and 24/7 support',
    
    # Storefront templates (user picks one on signup)
    'storefront_templates': {
        'technical': {
            'file': 'saas-technical.html',
            'name': 'Technical/Developer-First',
            'best_for': 'Developer tools, APIs, technical products'
        },
        'modern': {
            'file': 'saas-modern.html',
            'name': 'Modern SaaS',
            'best_for': 'B2B SaaS, productivity tools'
        },
        'enterprise': {
            'file': 'saas-enterprise.html',
            'name': 'Enterprise/Professional',
            'best_for': 'Enterprise SaaS, large organizations'
        }
    },
    
    # Email sequences (AME uses these)
    'email_sequences': {
        'developer_onboarding': [
            {
                'subject': 'Welcome to {product_name} API',
                'body': 'Hi {first_name}, Your API keys are ready. Get started in 5 minutes: {docs_url}',
                'send_delay_hours': 0
            },
            {
                'subject': 'Your first API call',
                'body': 'Hi {first_name}, Make your first call in 60 seconds: curl {api_endpoint}',
                'send_delay_hours': 24
            }
        ],
        'activation_sequence': [
            {
                'subject': 'You haven\'t made your first API call yet',
                'body': 'Hi {first_name}, Need help getting started? Our docs walk you through it: {docs_url}',
                'send_delay_hours': 72
            }
        ],
        'support_followup': [
            {
                'subject': 'How\'s {product_name} working for you?',
                'body': 'Hi {first_name}, It\'s been a week. Any questions? Reply to this email or check docs: {docs_url}',
                'send_delay_hours': 168
            }
        ],
        'upgrade_nudge': [
            {
                'subject': 'You\'re close to your API limit',
                'body': 'Hi {first_name}, You\'ve used {usage_percentage}% of your {plan} plan. Upgrade now to avoid interruptions.',
                'trigger': 'usage_80_percent'
            }
        ]
    },
    
    # C-Suite configuration
    'csuite_agents': {
        'cmo': {
            'class': 'SaaSCMO',
            'capabilities': ['developer_onboarding', 'activation_campaigns', 'churn_prevention', 'upgrade_nudges']
        },
        'cfo': {
            'class': 'BaseCFO',
            'traditional_cost': 180000  # $15K/month dev team
        },
        'ceo': {
            'class': 'SaaSCEO',
            'capabilities': ['product_strategy', 'integration_opportunities', 'enterprise_expansion']
        },
        'coo': {
            'class': 'BaseCOO',
            'monitors': ['api_uptime', 'response_times', 'error_rates', 'developer_satisfaction']
        }
    },
    
    # Autonomous systems
    'autonomous_systems': {
        'ame': {
            'enabled': True,
            'developer_onboarding': True,
            'activation_campaigns': True,
            'churn_prevention': True
        },
        'developer_onboarding': {
            'enabled': True,
            'instant_api_keys': True,
            'auto_generated_examples': True,
            'interactive_tutorials': True
        },
        'documentation_generator': {
            'enabled': True,
            'auto_generate': True,
            'languages': ['curl', 'python', 'javascript', 'ruby', 'go', 'java'],
            'update_frequency': 'on_api_change'
        },
        'support_bot': {
            'enabled': True,
            'avg_response_time': 30,  # seconds
            'operates_24_7': True,
            'escalates_to_human': 'when_needed'
        },
        'api_monitor': {
            'enabled': True,
            'monitors': ['uptime', 'response_time', 'error_rate', 'rate_limits'],
            'frequency': 'continuous',
            'alerts': True
        },
        'integration_matcher': {
            'enabled': True,
            'finds_complementary_apis': True,
            'suggests_integrations': True
        },
        'amg': {
            'enabled': True,
            'platforms': ['Product Hunt', 'HackerNews', 'Reddit', 'Twitter', 'LinkedIn'],
            'scan_frequency': 'hourly'
        }
    },
    
    # Dashboard widgets
    'dashboard_widgets': {
        'api_usage': True,
        'active_developers': True,
        'error_rates': True,
        'documentation_views': True,
        'support_tickets': True,
        'revenue_by_plan': True
    }
}
