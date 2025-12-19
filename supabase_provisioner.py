"""
Supabase Provisioner
Provisions databases for each user's business

Schemas:
- SaaS: API keys, usage logs, rate limits
- Marketing: Leads, campaigns, analytics
- Social: Content calendar, posts, engagement
"""

import os
import httpx
from typing import Dict, Any
from datetime import datetime, timezone


SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_ORG_ID = os.getenv("SUPABASE_ORG_ID")


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Database schemas for each template type
DATABASE_SCHEMAS = {
    "saas": """
-- SaaS API Business Schema
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    rate_limit_tier TEXT DEFAULT 'free'
);

CREATE TABLE api_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    date DATE NOT NULL,
    request_count INTEGER DEFAULT 0,
    UNIQUE(api_key_id, date)
);

CREATE INDEX idx_api_requests_key ON api_requests(api_key_id);
CREATE INDEX idx_api_requests_created ON api_requests(created_at);
""",
    
    "marketing": """
-- Marketing Campaign Business Schema
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    source TEXT,
    status TEXT DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- email, ad, landing_page
    status TEXT DEFAULT 'draft',
    launched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE campaign_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    UNIQUE(campaign_id, date)
);

CREATE TABLE email_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    campaign_id UUID REFERENCES campaigns(id),
    event_type TEXT NOT NULL, -- sent, opened, clicked, converted
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_campaign_stats_date ON campaign_stats(date);
""",
    
    "social": """
-- Social Media Business Schema
CREATE TABLE content_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL, -- twitter, linkedin, instagram, tiktok
    content TEXT NOT NULL,
    media_url TEXT,
    scheduled_for TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES content_posts(id),
    date DATE NOT NULL,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    UNIQUE(post_id, date)
);

CREATE TABLE growth_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    date DATE NOT NULL,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    UNIQUE(platform, date)
);

CREATE TABLE engagement_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    action_type TEXT NOT NULL, -- like, comment, follow
    target_user TEXT,
    target_post TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_scheduled ON content_posts(scheduled_for);
CREATE INDEX idx_engagement_platform ON engagement_metrics(post_id);
"""
}


async def provision_database(
    username: str,
    template_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Provision Supabase database for user's business
    
    Steps:
    1. Create Supabase project
    2. Run schema SQL
    3. Setup RLS policies
    4. Return connection credentials
    
    Args:
        username: User's username
        template_type: "saas" | "marketing" | "social"
        config: Template configuration
        
    Returns:
        {
            "ok": True,
            "database_url": "postgresql://...",
            "credentials": {...},
            "dashboard_url": "https://app.supabase.com/..."
        }
    """
    
    print(f"🗄️  Provisioning {template_type} database for {username}...")
    
    # Check if Supabase is configured
    if not SUPABASE_API_KEY:
        print("⚠️  Supabase API key not configured - using mock database")
        return await _mock_database(username, template_type, config)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {SUPABASE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Create project
            project_name = f"aigentsy-{username}-{template_type}"
            
            project_payload = {
                "organization_id": SUPABASE_ORG_ID,
                "name": project_name,
                "db_pass": _generate_secure_password(),
                "region": "us-east-1"
            }
            
            response = await client.post(
                "https://api.supabase.com/v1/projects",
                headers=headers,
                json=project_payload
            )
            
            if response.status_code not in [200, 201]:
                return {
                    "ok": False,
                    "error": f"Failed to create Supabase project: {response.status_code}",
                    "details": response.text
                }
            
            project_data = response.json()
            project_id = project_data.get("id")
            
            # Wait for project to be ready (can take 1-2 minutes)
            print("⏳ Waiting for database to initialize...")
            
            # Step 2: Run schema SQL
            # Note: This would be done via Supabase SQL editor or direct connection
            # For now, we'll return credentials and let user run schema
            
            database_url = f"postgresql://postgres:{project_payload['db_pass']}@{project_data['endpoint']}/postgres"
            
            return {
                "ok": True,
                "database_url": database_url,
                "credentials": {
                    "host": project_data.get("endpoint"),
                    "database": "postgres",
                    "user": "postgres",
                    "password": project_payload["db_pass"],
                    "port": 5432
                },
                "dashboard_url": f"https://app.supabase.com/project/{project_id}",
                "schema_sql": DATABASE_SCHEMAS[template_type],
                "project_id": project_id,
                "provisioned_at": now_iso()
            }
            
    except Exception as e:
        print(f"❌ Supabase provisioning error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


async def _mock_database(
    username: str,
    template_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock database for testing without Supabase API
    """
    
    mock_password = _generate_secure_password()
    
    print(f"✅ Mock database provisioned")
    
    return {
        "ok": True,
        "database_url": f"postgresql://postgres:{mock_password}@mock-db-{username}.supabase.co:5432/postgres",
        "credentials": {
            "host": f"mock-db-{username}.supabase.co",
            "database": "postgres",
            "user": "postgres",
            "password": mock_password,
            "port": 5432
        },
        "dashboard_url": f"https://app.supabase.com/project/mock-{username}",
        "schema_sql": DATABASE_SCHEMAS[template_type],
        "project_id": f"mock_{username}_{template_type}",
        "provisioned_at": now_iso(),
        "mock": True
    }


def _generate_secure_password() -> str:
    """Generate secure random password"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(24))


async def delete_database(project_id: str) -> Dict[str, Any]:
    """Delete Supabase project (rollback)"""
    
    if not SUPABASE_API_KEY:
        return {"ok": True, "mock": True, "message": "Mock deletion"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {SUPABASE_API_KEY}"}
            
            response = await client.delete(
                f"https://api.supabase.com/v1/projects/{project_id}",
                headers=headers
            )
            
            if response.status_code in [200, 204]:
                return {"ok": True, "deleted": True}
            else:
                return {
                    "ok": False,
                    "error": f"Deletion failed: {response.status_code}"
                }
                
    except Exception as e:
        return {"ok": False, "error": str(e)}
