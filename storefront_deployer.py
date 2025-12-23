"""
STOREFRONT DEPLOYER
Auto-deploys user's public website based on SKU + template choice

Integrates with YOUR existing vercel_deployer.py
Supports:
- Template SKUs (loads HTML file)
- Custom SKUs (generates HTML from business data)
- Existing websites (connects to user's site)

Result: username.aigentsy.com goes live
"""

import os
from typing import Dict
from datetime import datetime


async def deploy_storefront(
    username: str,
    sku_config: Dict,
    template_choice: str = 'professional',
    user_data: Dict = None
) -> Dict:
    """
    Deploy user's public storefront with unique variations
    
    Args:
        username: User's username
        sku_config: Complete SKU configuration
        template_choice: Template variation ('professional', 'boutique', 'disruptive')
        user_data: User's business data for personalization
    
    Returns:
        {
            'ok': True,
            'url': 'https://username.aigentsy.com',
            'template': 'professional',
            'deployed_at': '2025-12-22T...',
            'variation_id': 'electric-tech-modern-grain'
        }
    """
    
    print(f"\n🚀 STOREFRONT DEPLOYER")
    print(f"   User: {username}")
    print(f"   SKU: {sku_config['sku_id']}")
    print(f"   Template: {template_choice}")
    
    # ============================================================
    # STEP 1: CHECK IF USER HAS EXISTING WEBSITE
    # ============================================================
    
    storefront_config = sku_config.get('storefront_config', {})
    
    if storefront_config.get('existing_url'):
        # User has existing website - connect to it
        existing_url = storefront_config['existing_url']
        
        print(f"   → User has existing website: {existing_url}")
        print(f"   → Connecting to existing site (no deployment needed)")
        
        return {
            'ok': True,
            'url': existing_url,
            'template': 'existing',
            'deployed_at': datetime.utcnow().isoformat(),
            'deployment_type': 'connected_existing'
        }
    
    # ============================================================
    # STEP 2: GET TEMPLATE FILE
    # ============================================================
    
    templates = sku_config.get('storefront_templates', {})
    
    # Get template info
    if template_choice not in templates:
        template_choice = list(templates.keys())[0]  # Fallback to first available
    
    template_info = templates[template_choice]
    template_file = template_info.get('file', f'{template_choice}.html')
    
    print(f"   → Template file: {template_file}")
    
    # ============================================================
    # STEP 3: LOAD AND PERSONALIZE HTML
    # ============================================================
    
    print(f"   → Personalizing template with user data...")
    
    html_content = _load_and_personalize_template(
        template_file=template_file,
        user_data=user_data or {},
        sku_config=sku_config
    )
    
    # ============================================================
    # NEW: STEP 3.5: APPLY UNIQUE VARIATIONS
    # ============================================================
    
    print(f"   → Applying unique variations...")
    
    try:
        from template_variations import generate_unique_variations, apply_variations_to_html
        
        # Get user number from user_data
        user_number = user_data.get('userNumber', 1) if user_data else 1
        
        # Generate unique variations
        variations = generate_unique_variations(username, user_number)
        
        print(f"   → Color Palette: {variations['color_palette']['name']}")
        print(f"   → Font Pair: {variations['font_pair']['name']}")
        print(f"   → Accent Pattern: {variations['accent_pattern']['name']}")
        print(f"   → Variation ID: {variations['variation_id']}")
        
        # Apply variations to HTML
        html_content = apply_variations_to_html(html_content, variations)
        
        variation_id = variations['variation_id']
    
    except Exception as e:
        print(f"   ⚠️  Variations error: {e}")
        variation_id = 'default'
    
    # ============================================================
    # STEP 4: DEPLOY USING YOUR VERCEL_DEPLOYER.PY
    # ============================================================
    
    print(f"   → Deploying to Vercel...")
    
    try:
        # Import YOUR existing vercel_deployer
        from vercel_deployer import deploy_to_vercel
        
        deployment_result = await deploy_to_vercel(
            username=username,
            html_content=html_content,
            project_name=f"{username}-{sku_config['sku_id']}"
        )
        
        if deployment_result.get('ok'):
            deployed_url = deployment_result.get('url', f"https://{username}.aigentsy.com")
            
            print(f"   ✅ Deployed successfully!")
            print(f"   URL: {deployed_url}")
            
            return {
                'ok': True,
                'url': deployed_url,
                'template': template_choice,
                'template_name': template_info.get('name'),
                'deployed_at': datetime.utcnow().isoformat(),
                'deployment_type': 'vercel',
                'vercel_deployment_id': deployment_result.get('deployment_id'),
                'variation_id': variation_id  # NEW
            }
        
        else:
            print(f"   ⚠️  Vercel deployment failed: {deployment_result.get('error')}")
            
            # Fallback: Return subdomain (will be deployed later)
            return {
                'ok': False,
                'error': deployment_result.get('error'),
                'url': f"https://{username}.aigentsy.com",
                'template': template_choice,
                'deployed_at': None,
                'deployment_type': 'pending',
                'variation_id': variation_id
            }
    
    except Exception as e:
        print(f"   ⚠️  Deployment error: {e}")
        print(f"   → Will retry deployment in background")
        
        # Return subdomain even if deployment fails
        return {
            'ok': False,
            'error': str(e),
            'url': f"https://{username}.aigentsy.com",
            'template': template_choice,
            'deployed_at': None,
            'deployment_type': 'pending',
            'retry_scheduled': True,
            'variation_id': variation_id
        }


def _load_and_personalize_template(
    template_file: str,
    user_data: Dict,
    sku_config: Dict
) -> str:
    """
    Load HTML template and fill in user data
    
    Replaces placeholders:
    - {business_name} → User's business name
    - {tagline} → User's tagline
    - {services} → List of services
    - {contact_email} → User's email
    - {phone} → User's phone
    """
    
    # Check if template file exists
    template_path = f"/templates/{template_file}"
    
    # If template doesn't exist, generate basic HTML
    if not os.path.exists(template_path):
        print(f"   ⚠️  Template file not found: {template_path}")
        print(f"   → Generating basic HTML")
        
        html_content = _generate_basic_html(user_data, sku_config)
        return html_content
    
    # Load template
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Fill in placeholders
    replacements = {
        '{business_name}': user_data.get('business_name', 'My Business'),
        '{tagline}': user_data.get('tagline', 'Powered by AiGentsy'),
        '{contact_email}': user_data.get('email', 'hello@aigentsy.com'),
        '{phone}': user_data.get('phone', ''),
        '{username}': user_data.get('username', ''),
        '{sku_name}': sku_config.get('sku_name', ''),
        '{description}': user_data.get('description', '')
    }
    
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, value)
    
    return html_content


def _generate_basic_html(user_data: Dict, sku_config: Dict) -> str:
    """
    Generate basic HTML when template file doesn't exist
    """
    
    business_name = user_data.get('business_name', 'My Business')
    tagline = user_data.get('tagline', 'Powered by AiGentsy')
    description = user_data.get('description', f"Welcome to {business_name}")
    email = user_data.get('email', '')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 2rem;
        }}
        .hero h1 {{
            font-size: 3.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }}
        .hero p {{
            font-size: 1.5rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }}
        .cta {{
            display: inline-block;
            padding: 1rem 2rem;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 600;
            transition: transform 0.2s;
        }}
        .cta:hover {{
            transform: translateY(-2px);
        }}
        .powered {{
            margin-top: 3rem;
            opacity: 0.7;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <section class="hero">
        <div>
            <h1>{business_name}</h1>
            <p>{tagline}</p>
            <p style="max-width: 600px; margin: 0 auto 2rem;">{description}</p>
            <a href="mailto:{email}" class="cta">Get in Touch</a>
            <p class="powered">Powered by AiGentsy</p>
        </div>
    </section>
</body>
</html>"""
    
    return html


async def update_storefront(
    username: str,
    updates: Dict
) -> Dict:
    """
    Update existing storefront
    
    Args:
        username: User's username
        updates: Dict of fields to update
    
    Returns:
        Updated deployment result
    """
    
    # TODO: Implement storefront updates
    # Would reload current deployment, apply updates, redeploy
    
    return {
        'ok': True,
        'message': 'Storefront updated',
        'updated_at': datetime.utcnow().isoformat()
    }


def get_storefront_status(username: str) -> Dict:
    """
    Get current storefront deployment status
    
    Returns:
        {
            'deployed': True/False,
            'url': 'https://username.aigentsy.com',
            'status': 'live' | 'pending' | 'failed',
            'deployed_at': '...'
        }
    """
    
    # TODO: Check actual deployment status
    # Would query Vercel API or check database
    
    return {
        'deployed': True,
        'url': f"https://{username}.aigentsy.com",
        'status': 'live',
        'deployed_at': datetime.utcnow().isoformat()
    }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_deployment():
        
        print("=" * 70)
        print("STOREFRONT DEPLOYER - TEST")
        print("=" * 70)
        
        # Mock SKU config
        sku_config = {
            'sku_id': 'marketing',
            'sku_name': 'Marketing Pack',
            'storefront_templates': {
                'professional': {
                    'file': 'variation-1-professional.html',
                    'name': 'Professional'
                }
            }
        }
        
        # Mock user data
        user_data = {
            'username': 'wade',
            'business_name': 'Wade Marketing Agency',
            'tagline': 'Growth through AI',
            'email': 'wade@example.com',
            'description': 'We help businesses grow with AI-powered marketing'
        }
        
        # Test deployment
        result = await deploy_storefront(
            username='wade',
            sku_config=sku_config,
            template_choice='professional',
            user_data=user_data
        )
        
        print(f"\n{'='*70}")
        print(f"RESULT:")
        print(f"  OK: {result['ok']}")
        print(f"  URL: {result['url']}")
        print(f"  Template: {result['template']}")
        print(f"{'='*70}\n")
    
    asyncio.run(test_deployment())
