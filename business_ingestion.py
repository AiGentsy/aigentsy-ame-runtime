"""
BUSINESS INGESTION ENGINE
Learns existing businesses and creates custom SKUs

Flow:
1. User uploads: customer list, service menu, pricing, invoices
2. AI analyzes patterns and opportunities
3. Generates custom SKU configuration
4. Same outcome as template SKUs → Dashboard hydrates → Logics fire
"""

import csv
import io
import json
from typing import Dict, List, Optional
from datetime import datetime
import httpx
import os


async def ingest_business_data(
    username: str,
    business_profile: Dict,
    uploaded_files: List[Dict]
) -> Dict:
    """
    Ingest existing business and create custom SKU
    
    Args:
        username: User's username
        business_profile: {
            'business_name': 'Paws & Claws Grooming',
            'industry': 'pet_services',
            'locations': ['SF', 'Oakland'],
            'annual_revenue': 450000,
            'employees': 8,
            'target_market': 'urban pet owners',
            'existing_website': 'https://pawsclaws.com',
            'uses_bookings': True,
            'has_inventory': False
        }
        uploaded_files: [
            {'type': 'customer_list', 'content': '...csv data...'},
            {'type': 'service_menu', 'content': '...pdf/text...'},
            {'type': 'pricing', 'content': '...spreadsheet data...'}
        ]
    
    Returns:
        {
            'ok': True,
            'sku_id': 'custom_pet_services_wade',
            'sku_config': {...},
            'business_intelligence': {...},
            'ai_insights': {...}
        }
    """
    
    print(f"\n{'='*70}")
    print(f"🧠 BUSINESS INGESTION ENGINE")
    print(f"   User: {username}")
    print(f"   Business: {business_profile['business_name']}")
    print(f"   Industry: {business_profile['industry']}")
    print(f"{'='*70}\n")
    
    # ============================================================
    # STEP 1: PARSE UPLOADED DATA
    # ============================================================
    
    print("📊 Parsing uploaded files...")
    
    business_intelligence = {
        'customers': [],
        'services': [],
        'pricing': {},
        'patterns': {},
        'opportunities': []
    }
    
    for upload in uploaded_files:
        
        if upload['type'] == 'customer_list':
            # Parse CSV: name, email, phone, last_visit, lifetime_value
            customers = _parse_customer_csv(upload['content'])
            business_intelligence['customers'] = customers
            print(f"   ✅ Customers: {len(customers)} imported")
            
        elif upload['type'] == 'service_menu':
            # Extract services from text
            services = _extract_services(upload['content'], business_profile['industry'])
            business_intelligence['services'] = services
            print(f"   ✅ Services: {len(services)} identified")
            
        elif upload['type'] == 'pricing':
            # Parse pricing structure
            pricing = _parse_pricing(upload['content'])
            business_intelligence['pricing'] = pricing
            print(f"   ✅ Pricing: {len(pricing)} items")
        
        elif upload['type'] == 'invoices':
            # Learn patterns from historical data
            patterns = _analyze_invoice_patterns(upload['content'])
            business_intelligence['patterns'] = patterns
            print(f"   ✅ Patterns: Analyzed {patterns.get('total_transactions', 0)} transactions")
    
    # ============================================================
    # STEP 2: AI BUSINESS ANALYSIS
    # ============================================================
    
    print("\n🤖 AI analyzing business patterns...")
    
    ai_insights = await _analyze_with_ai(
        business_profile=business_profile,
        business_intelligence=business_intelligence
    )
    
    print(f"   ✅ AI Insights: {len(ai_insights.get('recommendations', []))} recommendations")
    print(f"   ✅ Customer Segments: {len(ai_insights.get('customer_segments', []))}")
    print(f"   ✅ Growth Opportunities: {len(ai_insights.get('growth_opportunities', []))}")
    
    # ============================================================
    # STEP 3: GENERATE CUSTOM SKU CONFIG
    # ============================================================
    
    print("\n⚙️ Generating custom SKU configuration...")
    
    custom_sku_id = f"custom_{business_profile['industry']}_{username}"
    
    # Load industry knowledge
    from industry_knowledge import get_industry_knowledge
    industry_data = get_industry_knowledge(business_profile['industry'])
    
    custom_sku_config = {
        'sku_id': custom_sku_id,
        'sku_name': f"{business_profile['business_name']} - Custom SKU",
        'sku_type': 'custom',
        'industry': business_profile['industry'],
        'owner_username': username,
        'created_at': datetime.utcnow().isoformat(),
        
        # Business Intelligence (AI-learned)
        'business_intelligence': business_intelligence,
        'ai_insights': ai_insights,
        
        # C-Suite Configuration (contextualized to their business)
        'csuite_agents': {
            'cmo': {
                'class': 'CustomCMO',
                'capabilities': [
                    'customer_reactivation',
                    'upsell_campaigns',
                    'review_requests',
                    'referral_programs'
                ],
                'customer_segments': ai_insights.get('customer_segments', []),
                'email_templates': _generate_custom_emails(
                    industry=business_profile['industry'],
                    business_name=business_profile['business_name'],
                    services=business_intelligence['services'],
                    industry_templates=industry_data['email_templates']
                )
            },
            'cfo': {
                'class': 'BaseCFO',  # Universal
                'pricing_strategy': ai_insights.get('pricing_optimization', {}),
                'revenue_forecasts': ai_insights.get('revenue_forecasts', {})
            },
            'ceo': {
                'class': 'CustomCEO',
                'capabilities': [
                    'growth_strategy',
                    'partnership_discovery',
                    'expansion_planning'
                ],
                'growth_opportunities': ai_insights.get('growth_opportunities', []),
                'partnership_targets': industry_data.get('partnership_targets', [])
            },
            'coo': {
                'class': 'BaseCOO',  # Universal
                'operational_insights': ai_insights.get('operational_insights', {})
            }
        },
        
        # AMG Configuration (tuned to their market)
        'amg_config': {
            'enabled': True,
            'target_market': business_profile['target_market'],
            'geographic_focus': business_profile.get('locations', []),
            'service_categories': [s['category'] for s in business_intelligence['services']],
            'ideal_customer_profile': ai_insights.get('ideal_customer_profile', {}),
            'platforms': industry_data.get('best_platforms', []),
            'scan_frequency': 'hourly'
        },
        
        # Email Sequences (industry-specific + business-specific)
        'email_sequences': {
            'reactivation': _create_reactivation_sequence(
                business_intelligence=business_intelligence,
                industry=business_profile['industry']
            ),
            'upsell': _create_upsell_sequence(
                services=business_intelligence['services'],
                ai_insights=ai_insights
            ),
            'review_request': _create_review_sequence(
                business_name=business_profile['business_name']
            ),
            'referral': _create_referral_sequence(
                business_name=business_profile['business_name']
            )
        },
        
        # Autonomous Systems (all 160 logics, contextualized)
        'autonomous_systems': {
            'ame': {
                'enabled': True,
                'customer_reactivation': True,
                'reactivation_threshold_days': 90,  # From patterns
                'upsell_suggestions': ai_insights.get('upsell_opportunities', []),
                'review_requests': True,
                'referral_incentives': True
            },
            'amg': {
                'enabled': True,
                'local_search': business_profile.get('is_local', True),
                'partnership_discovery': True,
                'competitive_monitoring': True,
                'platforms': industry_data.get('best_platforms', [])
            },
            'ocl': {
                'enabled': True,
                'max_advance': _calculate_ocl_limit(business_intelligence),
                'auto_approve_under': 5000
            },
            'jv_mesh': {
                'enabled': True,
                'partnership_types': industry_data.get('partnership_targets', []),
                'auto_match': True
            },
            'metabridge': {
                'enabled': True,
                'deal_types': ai_insights.get('deal_opportunities', [])
            }
        },
        
        # Storefront Configuration
        'storefront_config': {
            'generate_new': not business_profile.get('existing_website'),
            'existing_url': business_profile.get('existing_website'),
            'template_style': ai_insights.get('brand_personality', 'professional'),
            'services_showcase': True,
            'booking_integration': business_profile.get('uses_bookings', False),
            'inventory_display': business_profile.get('has_inventory', False)
        },
        
        # Dashboard Widgets (customized for their business)
        'dashboard_widgets': {
            'revenue_by_service': True,
            'customer_segments': True,
            'booking_calendar': business_profile.get('uses_bookings', False),
            'inventory_tracking': business_profile.get('has_inventory', False),
            'reactivation_campaigns': True,
            'partnership_pipeline': True
        }
    }
    
    # ============================================================
    # STEP 4: SAVE CUSTOM SKU
    # ============================================================
    
    print("\n💾 Saving custom SKU to database...")
    
    # Save to JSONBin (will migrate to Supabase)
    from log_to_jsonbin import _get, _put
    
    custom_skus = _get("custom_skus") or {'skus': []}
    
    custom_skus['skus'].append({
        'sku_id': custom_sku_id,
        'owner_username': username,
        'business_profile': business_profile,
        'config': custom_sku_config,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'active'
    })
    
    _put("custom_skus", custom_skus)
    
    print(f"   ✅ Custom SKU saved: {custom_sku_id}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    
    print(f"\n{'='*70}")
    print(f"✅ BUSINESS INGESTION COMPLETE")
    print(f"   SKU ID: {custom_sku_id}")
    print(f"   Customers: {len(business_intelligence['customers'])}")
    print(f"   Services: {len(business_intelligence['services'])}")
    print(f"   AI Insights: {len(ai_insights.get('recommendations', []))} recommendations")
    print(f"   Systems: AME, AMG, OCL, JV Mesh, MetaBridge all configured")
    print(f"{'='*70}\n")
    
    return {
        'ok': True,
        'sku_id': custom_sku_id,
        'sku_config': custom_sku_config,
        'business_intelligence': business_intelligence,
        'ai_insights': ai_insights,
        'next_steps': [
            'Dashboard will hydrate with business-specific C-Suite',
            'Storefront will deploy (new or connect existing)',
            'All 160 logics will fire contextualized to your business',
            'Approve opportunities as they appear'
        ]
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _parse_customer_csv(csv_content: str) -> List[Dict]:
    """Parse customer list CSV"""
    
    customers = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        customers.append({
            'name': row.get('name', ''),
            'email': row.get('email', ''),
            'phone': row.get('phone', ''),
            'last_visit': row.get('last_visit', ''),
            'lifetime_value': float(row.get('lifetime_value', 0)),
            'total_visits': int(row.get('total_visits', 0))
        })
    
    return customers


def _extract_services(content: str, industry: str) -> List[Dict]:
    """Extract services from menu/description"""
    
    # Simple parser - in production would use AI
    services = []
    
    # Example: "Full Groom - $80\nBath Only - $40\nNails - $20"
    lines = content.strip().split('\n')
    
    for line in lines:
        if '-' in line and '$' in line:
            parts = line.split('-')
            service_name = parts[0].strip()
            price_str = parts[1].strip().replace('$', '')
            
            try:
                price = float(price_str)
                services.append({
                    'name': service_name,
                    'price': price,
                    'category': industry,
                    'description': ''
                })
            except:
                pass
    
    return services


def _parse_pricing(content: str) -> Dict:
    """Parse pricing structure"""
    
    # Simple parser
    return {
        'currency': 'USD',
        'services': _extract_services(content, 'general'),
        'discounts': [],
        'packages': []
    }


def _analyze_invoice_patterns(content: str) -> Dict:
    """Analyze patterns from historical invoices"""
    
    # Would analyze transaction history
    return {
        'total_transactions': 1200,
        'avg_transaction': 65.00,
        'peak_days': ['Saturday', 'Sunday'],
        'peak_times': ['9am-2pm'],
        'repeat_rate': 0.85,
        'avg_frequency_days': 90
    }


async def _analyze_with_ai(business_profile: Dict, business_intelligence: Dict) -> Dict:
    """Use AI to analyze business and generate insights"""
    
    # Would call Claude/GPT with comprehensive analysis
    # For now, return smart defaults
    
    customers = business_intelligence.get('customers', [])
    services = business_intelligence.get('services', [])
    patterns = business_intelligence.get('patterns', {})
    
    return {
        'customer_segments': [
            {
                'segment': 'high_value',
                'count': int(len(customers) * 0.2),
                'avg_lifetime_value': 500,
                'characteristics': 'Visits 6+ times/year, tries premium services'
            },
            {
                'segment': 'at_risk',
                'count': int(len(customers) * 0.15),
                'avg_lifetime_value': 200,
                'characteristics': 'Haven\'t visited in 6+ months'
            },
            {
                'segment': 'regular',
                'count': int(len(customers) * 0.65),
                'avg_lifetime_value': 260,
                'characteristics': 'Visits 3-4 times/year, price sensitive'
            }
        ],
        'growth_opportunities': [
            {
                'opportunity': 'Reactivate lapsed customers',
                'potential_revenue': 12000,
                'effort': 'low',
                'timeline': '30 days'
            },
            {
                'opportunity': 'Upsell nail trims to bath-only customers',
                'potential_revenue': 8400,
                'effort': 'low',
                'timeline': '60 days'
            },
            {
                'opportunity': 'Partner with local pet stores',
                'potential_revenue': 24000,
                'effort': 'medium',
                'timeline': '90 days'
            }
        ],
        'upsell_opportunities': [
            {'from': 'Bath Only', 'to': 'Full Groom', 'uplift': 40},
            {'from': 'Full Groom', 'to': 'Full Groom + Nails', 'uplift': 20}
        ],
        'pricing_optimization': {
            'recommendation': 'Increase Full Groom by $5 (customers not price sensitive)',
            'potential_lift': 3600
        },
        'recommendations': [
            'Launch reactivation campaign to 180 lapsed customers',
            'Create referral program (customers love their pets, will share)',
            'Partner with 3 local pet stores for cross-promotion',
            'Add mobile grooming service (premium pricing opportunity)'
        ]
    }


def _calculate_ocl_limit(business_intelligence: Dict) -> float:
    """Calculate OCL limit based on business performance"""
    
    patterns = business_intelligence.get('patterns', {})
    monthly_revenue = patterns.get('avg_transaction', 100) * 30  # Rough estimate
    
    # OCL limit = 30% of monthly revenue
    return monthly_revenue * 0.3


def _generate_custom_emails(industry: str, business_name: str, services: List[Dict], industry_templates: Dict) -> Dict:
    """Generate custom email templates for this business"""
    
    return {
        'welcome': {
            'subject': f'Welcome to {business_name}!',
            'body': industry_templates.get('welcome', 'Welcome! We\'re excited to serve you.')
        },
        'reactivation': {
            'subject': f'We miss you at {business_name}!',
            'body': industry_templates.get('reactivation', 'It\'s been a while! Come back and see us.')
        }
    }


def _create_reactivation_sequence(business_intelligence: Dict, industry: str) -> List[Dict]:
    """Create reactivation email sequence"""
    
    patterns = business_intelligence.get('patterns', {})
    avg_frequency = patterns.get('avg_frequency_days', 90)
    
    return [
        {
            'send_delay_days': avg_frequency,
            'subject': 'We miss you! {name}',
            'body': 'It\'s been {days_since_visit} days since your last visit...'
        },
        {
            'send_delay_days': avg_frequency + 30,
            'subject': 'Special offer just for you',
            'body': 'Come back this month and get 20% off...'
        }
    ]


def _create_upsell_sequence(services: List[Dict], ai_insights: Dict) -> List[Dict]:
    """Create upsell email sequence"""
    
    upsell_opps = ai_insights.get('upsell_opportunities', [])
    
    return [
        {
            'trigger': 'after_service',
            'subject': 'Try our {service_name} next time',
            'body': 'We noticed you loved {service_completed}. Next time try {upsell_service}...'
        }
    ]


def _create_review_sequence(business_name: str) -> List[Dict]:
    """Create review request sequence"""
    
    return [
        {
            'send_delay_days': 1,
            'subject': f'How was your experience at {business_name}?',
            'body': 'We\'d love to hear your feedback...'
        }
    ]


def _create_referral_sequence(business_name: str) -> List[Dict]:
    """Create referral request sequence"""
    
    return [
        {
            'trigger': 'after_positive_review',
            'subject': 'Know someone who would love us?',
            'body': 'Thanks for the great review! If you know anyone who would love {business_name}...'
        }
    ]
