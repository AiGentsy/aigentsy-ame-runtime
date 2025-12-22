"""
UNIVERSAL SKU CONFIG LOADER
Loads ANY SKU - template (marketing, saas, social) OR custom (user-created)

Flow:
1. Check if custom SKU (user-uploaded business)
2. Check if template SKU (built-in marketing/saas/social)
3. Fallback to default

Integrates with YOUR existing systems:
- CSuiteOrchestrator uses sku_config
- AMGOrchestrator uses sku_config
- APEX ULTRA uses sku_config
"""

import importlib
from typing import Dict, Optional
from datetime import datetime


def load_sku_config(
    sku_id: str,
    username: Optional[str] = None
) -> Dict:
    """
    Universal SKU loader - works for ALL business types
    
    Args:
        sku_id: SKU identifier (e.g., 'marketing', 'custom_pet_services_wade')
        username: User's username (needed for custom SKUs)
    
    Returns:
        Complete SKU configuration with:
        - storefront_templates
        - csuite_agents
        - email_sequences
        - autonomous_systems
        - dashboard_widgets
    
    Examples:
        # Template SKU
        config = load_sku_config('marketing')
        
        # Custom SKU
        config = load_sku_config('custom_pet_services_wade', username='wade')
    """
    
    print(f"\n🔧 SKU CONFIG LOADER")
    print(f"   SKU: {sku_id}")
    print(f"   User: {username}")
    
    # ============================================================
    # TIER 1: CUSTOM SKUs (User-created businesses)
    # ============================================================
    
    if sku_id.startswith('custom_'):
        print(f"   → Loading custom SKU...")
        
        try:
            from log_to_jsonbin import _get
            
            # Load from JSONBin (will migrate to Supabase)
            custom_skus_data = _get("custom_skus")
            
            if custom_skus_data:
                for sku_entry in custom_skus_data.get('skus', []):
                    if sku_entry['sku_id'] == sku_id:
                        config = sku_entry['config']
                        print(f"   ✅ Loaded custom SKU: {config['sku_name']}")
                        return config
            
            print(f"   ⚠️  Custom SKU not found: {sku_id}")
        
        except Exception as e:
            print(f"   ⚠️  Error loading custom SKU: {e}")
    
    # ============================================================
    # TIER 2: TEMPLATE SKUs (Built-in: marketing, saas, social)
    # ============================================================
    
    template_skus = ['marketing', 'saas', 'social']
    
    if sku_id in template_skus:
        print(f"   → Loading template SKU...")
        
        try:
            # Import SKU config from /skus/{sku_id}/config.py
            config_module = importlib.import_module(f'skus.{sku_id}.config')
            config_name = f'{sku_id.upper()}_SKU_CONFIG'
            config = getattr(config_module, config_name)
            
            print(f"   ✅ Loaded template SKU: {config['sku_name']}")
            return config
        
        except ImportError as e:
            print(f"   ⚠️  Template SKU file not found: /skus/{sku_id}/config.py")
            print(f"   Error: {e}")
        
        except AttributeError as e:
            print(f"   ⚠️  Config variable not found: {config_name}")
            print(f"   Error: {e}")
    
    # ============================================================
    # TIER 3: FALLBACK (Default general business)
    # ============================================================
    
    print(f"   → Using default SKU config...")
    
    from industry_knowledge import DEFAULT_INDUSTRY
    
    default_config = {
        'sku_id': 'default',
        'sku_name': 'General Business',
        'sku_type': 'template',
        'industry': 'general',
        
        # Storefront templates (basic)
        'storefront_templates': {
            'professional': 'default-professional.html',
            'minimal': 'default-minimal.html',
            'modern': 'default-modern.html'
        },
        
        # C-Suite configuration (basic)
        'csuite_agents': {
            'cmo': {
                'class': 'BaseCMO',
                'capabilities': ['email_sequences', 'outreach'],
                'email_templates': DEFAULT_INDUSTRY['email_templates']
            },
            'cfo': {
                'class': 'BaseCFO',
                'capabilities': ['fee_calculation', 'revenue_tracking']
            },
            'ceo': {
                'class': 'BaseCEO',
                'capabilities': ['strategic_analysis', 'recommendations']
            },
            'coo': {
                'class': 'BaseCOO',
                'capabilities': ['system_monitoring', 'health_checks']
            }
        },
        
        # Email sequences (generic)
        'email_sequences': {
            'welcome': [
                {
                    'subject': 'Welcome to {business_name}!',
                    'body': DEFAULT_INDUSTRY['email_templates']['welcome'],
                    'send_delay_days': 0
                }
            ],
            'follow_up': [
                {
                    'subject': 'Following up',
                    'body': DEFAULT_INDUSTRY['email_templates']['follow_up'],
                    'send_delay_days': 3
                }
            ]
        },
        
        # Autonomous systems (basic)
        'autonomous_systems': {
            'ame': {'enabled': True},
            'amg': {'enabled': True, 'platforms': DEFAULT_INDUSTRY['best_platforms']},
            'ocl': {'enabled': True},
            'jv_mesh': {'enabled': True}
        },
        
        # Dashboard widgets
        'dashboard_widgets': {
            'revenue_tracking': True,
            'customer_management': True,
            'opportunity_pipeline': True
        }
    }
    
    print(f"   ✅ Using default config")
    
    return default_config


def get_sku_info(sku_id: str, username: Optional[str] = None) -> Dict:
    """
    Get SKU metadata without loading full config
    
    Returns:
        {
            'sku_id': 'marketing',
            'sku_name': 'Marketing - Launch Assets Pack',
            'sku_type': 'template',  # or 'custom'
            'industry': 'marketing',
            'available': True
        }
    """
    
    # Try to load
    config = load_sku_config(sku_id, username)
    
    return {
        'sku_id': config.get('sku_id', sku_id),
        'sku_name': config.get('sku_name', 'Unknown'),
        'sku_type': config.get('sku_type', 'template'),
        'industry': config.get('industry', 'general'),
        'available': bool(config)
    }


def list_available_template_skus() -> list:
    """Return list of available template SKUs"""
    
    return [
        {
            'sku_id': 'marketing',
            'sku_name': 'Marketing - Launch Assets Pack',
            'description': 'Complete marketing agency with campaigns, partnerships, and competitive intelligence',
            'best_for': 'Marketing agencies, consultants, growth hackers'
        },
        {
            'sku_id': 'saas',
            'sku_name': 'SaaS - API Documentation System',
            'description': 'API platform with developer onboarding, documentation, and support automation',
            'best_for': 'SaaS companies, API providers, developer tools'
        },
        {
            'sku_id': 'social',
            'sku_name': 'Social - Creator Growth Pack',
            'description': 'Creator business with content automation, brand deals, and audience growth',
            'best_for': 'Content creators, influencers, social media managers'
        }
    ]


def list_user_custom_skus(username: str) -> list:
    """Return list of custom SKUs owned by user"""
    
    try:
        from log_to_jsonbin import _get
        
        custom_skus_data = _get("custom_skus")
        
        if not custom_skus_data:
            return []
        
        user_skus = []
        
        for sku_entry in custom_skus_data.get('skus', []):
            if sku_entry.get('owner_username') == username:
                user_skus.append({
                    'sku_id': sku_entry['sku_id'],
                    'sku_name': sku_entry['config']['sku_name'],
                    'industry': sku_entry['config']['industry'],
                    'created_at': sku_entry.get('created_at'),
                    'status': sku_entry.get('status', 'active')
                })
        
        return user_skus
    
    except Exception as e:
        print(f"Error loading user custom SKUs: {e}")
        return []


def validate_sku_config(config: Dict) -> Dict:
    """
    Validate SKU configuration has required fields
    
    Returns:
        {
            'valid': True/False,
            'missing_fields': [...],
            'errors': [...]
        }
    """
    
    required_fields = [
        'sku_id',
        'sku_name',
        'csuite_agents',
        'autonomous_systems'
    ]
    
    missing = []
    errors = []
    
    for field in required_fields:
        if field not in config:
            missing.append(field)
    
    # Validate C-Suite has all 4 agents
    if 'csuite_agents' in config:
        required_agents = ['cmo', 'cfo', 'ceo', 'coo']
        csuite = config['csuite_agents']
        
        for agent in required_agents:
            if agent not in csuite:
                errors.append(f"Missing C-Suite agent: {agent}")
    
    return {
        'valid': len(missing) == 0 and len(errors) == 0,
        'missing_fields': missing,
        'errors': errors
    }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    
    print("=" * 70)
    print("SKU CONFIG LOADER - EXAMPLES")
    print("=" * 70)
    
    # Example 1: Load template SKU
    print("\n1. Loading template SKU (marketing):")
    marketing_config = load_sku_config('marketing')
    print(f"\n   Config loaded: {marketing_config.get('sku_name')}")
    print(f"   Systems: {list(marketing_config.get('autonomous_systems', {}).keys())}")
    
    # Example 2: Load custom SKU
    print("\n2. Loading custom SKU (dog grooming):")
    custom_config = load_sku_config('custom_pet_services_wade', username='wade')
    print(f"\n   Config loaded: {custom_config.get('sku_name')}")
    
    # Example 3: List available SKUs
    print("\n3. Available template SKUs:")
    template_skus = list_available_template_skus()
    for sku in template_skus:
        print(f"\n   - {sku['sku_name']}")
        print(f"     {sku['description']}")
    
    # Example 4: Validate config
    print("\n4. Validating SKU config:")
    validation = validate_sku_config(marketing_config)
    print(f"\n   Valid: {validation['valid']}")
    if not validation['valid']:
        print(f"   Missing: {validation['missing_fields']}")
        print(f"   Errors: {validation['errors']}")
    
    print("\n" + "=" * 70)
    print("✅ SKU CONFIG LOADER READY")
    print("=" * 70)
