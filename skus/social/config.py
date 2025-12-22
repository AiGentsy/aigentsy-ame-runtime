"""
SOCIAL SKU CONFIGURATION
Complete creator business with content automation, brand deals, and audience growth
"""

SOCIAL_SKU_CONFIG = {
    'sku_id': 'social',
    'sku_name': 'Social - Creator Growth Pack',
    'sku_version': '2.1.0',
    'sku_type': 'template',
    'industry': 'social_media',
    'description': 'Complete creator business with content scheduling, brand deal matching, and audience growth automation',
    
    # Storefront templates (user picks one on signup)
    'storefront_templates': {
        'influencer': {
            'file': 'social-influencer.html',
            'name': 'Influencer/Lifestyle',
            'best_for': 'Lifestyle influencers, personal brands'
        },
        'creator': {
            'file': 'social-creator.html',
            'name': 'Creator/Artist',
            'best_for': 'Content creators, artists, musicians'
        },
        'entertainer': {
            'file': 'social-entertainer.html',
            'name': 'Entertainer/Personality',
            'best_for': 'Comedians, entertainers, personalities'
        }
    },
    
    # Email sequences (AME uses these)
    'email_sequences': {
        'creator_onboarding': [
            {
                'subject': 'Welcome to {business_name}!',
                'body': 'Hi {first_name}, Your creator business is live! Dashboard: {dashboard_url}',
                'send_delay_hours': 0
            },
            {
                'subject': 'Your first week: {follower_count} followers',
                'body': 'Hi {first_name}, Quick stats: +{followers_gained} followers, {engagement_rate}% engagement. Keep going!',
                'send_delay_hours': 168
            }
        ],
        'content_calendar': [
            {
                'subject': 'Your content schedule for this week',
                'body': 'Hi {first_name}, Here\'s what\'s scheduled: {content_list}. Need to adjust?',
                'send_delay_hours': 0,
                'frequency': 'weekly'
            }
        ],
        'brand_deal_sequence': [
            {
                'subject': 'Brand deal opportunity: {brand_name}',
                'body': 'Hi {first_name}, {brand_name} wants to work with you! Estimated value: ${deal_value}',
                'requires_approval': True
            }
        ],
        'growth_optimization': [
            {
                'subject': 'Your audience grew {percentage}% this month',
                'body': 'Hi {first_name}, Great work! Top performing content: {top_content}. Keep doing more of this.',
                'frequency': 'monthly'
            }
        ]
    },
    
    # C-Suite configuration
    'csuite_agents': {
        'cmo': {
            'class': 'SocialCMO',
            'capabilities': ['content_strategy', 'brand_deal_negotiations', 'audience_growth', 'engagement_optimization']
        },
        'cfo': {
            'class': 'BaseCFO',
            'traditional_cost': 120000  # Social media manager + agent
        },
        'ceo': {
            'class': 'SocialCEO',
            'capabilities': ['platform_expansion', 'monetization_strategy', 'brand_partnerships']
        },
        'coo': {
            'class': 'BaseCOO',
            'monitors': ['content_performance', 'audience_metrics', 'brand_deal_pipeline']
        }
    },
    
    # Autonomous systems
    'autonomous_systems': {
        'ame': {
            'enabled': True,
            'content_reminders': True,
            'brand_deal_outreach': True,
            'audience_engagement': True
        },
        'content_scheduler': {
            'enabled': True,
            'platforms': ['Instagram', 'TikTok', 'YouTube', 'Twitter', 'LinkedIn'],
            'auto_post': False,  # Requires approval
            'optimal_timing': True,
            'cross_posting': True
        },
        'brand_deal_matcher': {
            'enabled': True,
            'match_algorithm': 'audience_alignment',
            'min_deal_value': 500,
            'auto_pitch': False  # Requires approval
        },
        'content_idea_generator': {
            'enabled': True,
            'analyzes_trends': True,
            'suggests_topics': True,
            'frequency': 'daily'
        },
        'engagement_bot': {
            'enabled': True,
            'responds_to_comments': True,
            'avg_response_time': 60,  # seconds
            'operates_24_7': True
        },
        'growth_tracker': {
            'enabled': True,
            'tracks': ['followers', 'engagement', 'reach', 'impressions'],
            'frequency': 'hourly',
            'alerts_on': 'viral_content'
        },
        'hashtag_optimizer': {
            'enabled': True,
            'suggests_hashtags': True,
            'analyzes_performance': True,
            'update_frequency': 'per_post'
        },
        'amg': {
            'enabled': True,
            'platforms': ['Instagram', 'TikTok', 'YouTube', 'Twitter', 'LinkedIn', 'Facebook'],
            'scan_frequency': 'hourly',
            'finds': ['brand_opportunities', 'trending_topics', 'collaboration_opportunities']
        }
    },
    
    # Dashboard widgets
    'dashboard_widgets': {
        'audience_growth': True,
        'content_performance': True,
        'brand_deals': True,
        'engagement_metrics': True,
        'content_calendar': True,
        'platform_breakdown': True,
        'revenue_by_platform': True
    }
}
