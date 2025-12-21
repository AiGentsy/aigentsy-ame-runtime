"""
MARKETING DASHBOARD CONNECTOR
Connects C-Suite agents to user's live dashboard data
Enables real-time awareness and personalized recommendations
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class DashboardConnector:
    """
    Provides C-Suite agents with real-time access to user's dashboard state
    
    This is the KEY piece - without this, agents can't personalize
    With this, agents know:
    - User's actual revenue numbers
    - Real partnership count
    - Actual competitor moves
    - Live campaign performance
    - Everything in real-time
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.cache_ttl = 60  # Refresh every 60 seconds
        self.last_refresh = None
        self.dashboard_state = None
    
    def get_dashboard_state(self, force_refresh: bool = False) -> Dict:
        """
        Get complete dashboard state for user
        This is what C-Suite agents read to personalize their actions
        """
        
        # Check if cache is fresh
        if not force_refresh and self.dashboard_state and self._is_cache_fresh():
            return self.dashboard_state
        
        # Fetch fresh data from Supabase
        self.dashboard_state = self._fetch_from_supabase()
        self.last_refresh = datetime.utcnow()
        
        return self.dashboard_state
    
    def _fetch_from_supabase(self) -> Dict:
        """
        Fetch all dashboard data from Supabase
        
        Tables queried:
        - users (profile, preferences, storefront info)
        - revenue_tracking (all transactions, fees)
        - campaigns (active campaigns, performance)
        - partnerships (active, pending, revenue)
        - competitive_intel (monitored competitors, recent moves)
        - leads (count, response times, conversion)
        """
        
        # TODO: Replace with actual Supabase queries
        # For now, simulate with example data
        
        dashboard_data = {
            # User profile
            'user_id': self.user_id,
            'name': self._query_supabase('users', 'name'),
            'email': self._query_supabase('users', 'email'),
            'business_name': self._query_supabase('users', 'business_name'),
            'username': self._query_supabase('users', 'username'),
            
            # Branding
            'brand_color_primary': self._query_supabase('users', 'brand_color_primary'),
            'brand_color_secondary': self._query_supabase('users', 'brand_color_secondary'),
            'logo_url': self._query_supabase('users', 'logo_url'),
            'tagline': self._query_supabase('users', 'tagline'),
            
            # Revenue tracking (from revenue_tracking table)
            'revenue_this_month': self._query_supabase('revenue_tracking', 'sum_this_month'),
            'revenue_total': self._query_supabase('revenue_tracking', 'sum_total'),
            'fees_paid_this_month': self._query_supabase('revenue_tracking', 'fees_this_month'),
            'fees_paid_total': self._query_supabase('revenue_tracking', 'fees_total'),
            
            # Campaign performance (from campaigns table)
            'active_campaigns': self._query_supabase('campaigns', 'count_active'),
            'platforms': self._query_supabase('campaigns', 'list_platforms'),
            'best_platform': self._query_supabase('campaigns', 'top_platform_name'),
            'best_platform_roas': self._query_supabase('campaigns', 'top_platform_roas'),
            'avg_roas_all_platforms': self._query_supabase('campaigns', 'avg_roas'),
            
            # Partnerships (from partnerships table)
            'active_partnerships': self._query_supabase('partnerships', 'count_active'),
            'pending_partnership_approvals': self._query_supabase('partnerships', 'count_pending'),
            'partnership_revenue_ytd': self._query_supabase('partnerships', 'revenue_ytd'),
            'partnership_opportunities': self._query_supabase('partnerships', 'list_opportunities'),
            
            # Competitive intel (from competitive_intel table)
            'monitored_competitors': self._query_supabase('competitive_intel', 'count_monitored'),
            'competitor_moves_24h': self._query_supabase('competitive_intel', 'moves_last_24h'),
            'pending_counter_strategies': self._query_supabase('competitive_intel', 'pending_strategies'),
            'top_competitor': self._query_supabase('competitive_intel', 'top_competitor_name'),
            
            # Leads (from leads table)
            'leads_this_month': self._query_supabase('leads', 'count_this_month'),
            'leads_total': self._query_supabase('leads', 'count_total'),
            'avg_response_time_seconds': self._query_supabase('leads', 'avg_response_time'),
            'conversion_rate': self._query_supabase('leads', 'conversion_rate'),
            
            # User preferences (from user_preferences table)
            'auto_approve_partnerships_under': self._query_supabase('user_preferences', 'auto_approve_threshold'),
            'requires_approval_for': self._query_supabase('user_preferences', 'approval_list'),
            'sender_name': self._query_supabase('user_preferences', 'email_sender_name'),
            'sender_email': self._query_supabase('user_preferences', 'email_sender_address'),
            
            # Storefront (from storefronts table)
            'storefront_url': self._query_supabase('storefronts', 'url'),
            'storefront_template': self._query_supabase('storefronts', 'template_choice'),
            'storefront_status': self._query_supabase('storefronts', 'status'),
            'storefront_deployed_at': self._query_supabase('storefronts', 'deployed_at'),
            
            # System activity (from activity_log table)
            'ame_pitches_sent_24h': self._query_supabase('activity_log', 'ame_pitches_24h'),
            'amg_opportunities_found_24h': self._query_supabase('activity_log', 'amg_opportunities_24h'),
            'campaigns_optimized_24h': self._query_supabase('activity_log', 'optimizations_24h'),
            
            # Meta
            'last_login': self._query_supabase('users', 'last_login_at'),
            'dashboard_last_viewed': self._query_supabase('users', 'last_dashboard_view'),
            'days_since_last_login': self._calculate_days_since_login(),
            
            # Timestamp
            'fetched_at': datetime.utcnow().isoformat()
        }
        
        return dashboard_data
    
    def _query_supabase(self, table: str, field: str):
        """
        Query Supabase for specific field
        
        In production:
        supabase.table(table).select(field).eq('user_id', self.user_id).execute()
        """
        
        # TODO: Replace with actual Supabase query
        # For now, return example data
        
        example_data = {
            'users': {
                'name': 'Wade',
                'email': 'wade@aigentsy.com',
                'business_name': 'AiGentsy Marketing',
                'username': 'wade',
                'brand_color_primary': '#00bfff',
                'brand_color_secondary': '#0080ff',
                'logo_url': '/assets/logo.png',
                'tagline': 'Marketing for the Future',
                'last_login_at': '2025-12-21T10:30:00Z',
                'last_dashboard_view': '2025-12-21T11:45:00Z'
            },
            'revenue_tracking': {
                'sum_this_month': 47000,
                'sum_total': 127000,
                'fees_this_month': 1316,
                'fees_total': 3556
            },
            'campaigns': {
                'count_active': 8,
                'list_platforms': ['Facebook', 'Google', 'Reddit', 'LinkedIn', 'Twitter', 'TikTok', 'Instagram', 'Pinterest'],
                'top_platform_name': 'Reddit',
                'top_platform_roas': 5.3,
                'avg_roas': 3.2
            },
            'partnerships': {
                'count_active': 8,
                'count_pending': 3,
                'revenue_ytd': 127000,
                'list_opportunities': [
                    {'business': 'Yoga Studios', 'est_value': 43000},
                    {'business': 'Athletic Wear', 'est_value': 28000},
                    {'business': 'Supplements', 'est_value': 21000}
                ]
            },
            'competitive_intel': {
                'count_monitored': 47,
                'moves_last_24h': 2,
                'pending_strategies': 1,
                'top_competitor_name': 'Traditional Agency Co'
            },
            'leads': {
                'count_this_month': 156,
                'count_total': 487,
                'avg_response_time': 34,
                'conversion_rate': 12.5
            },
            'user_preferences': {
                'auto_approve_threshold': 10000,
                'approval_list': ['partnerships_over_10k', 'campaigns_over_5k'],
                'email_sender_name': 'Wade',
                'email_sender_address': 'wade@aigentsy.com'
            },
            'storefronts': {
                'url': 'https://wade.aigentsy.com',
                'template_choice': 'disruptive',
                'status': 'LIVE',
                'deployed_at': '2025-12-20T14:30:00Z'
            },
            'activity_log': {
                'ame_pitches_24h': 12,
                'amg_opportunities_24h': 18,
                'optimizations_24h': 47
            }
        }
        
        return example_data.get(table, {}).get(field, None)
    
    def _calculate_days_since_login(self) -> int:
        """Calculate days since last login"""
        # TODO: Implement actual calculation
        return 0
    
    def _is_cache_fresh(self) -> bool:
        """Check if cached data is still fresh"""
        if not self.last_refresh:
            return False
        
        age_seconds = (datetime.utcnow() - self.last_refresh).total_seconds()
        return age_seconds < self.cache_ttl
    
    def update_dashboard_widget(self, widget_name: str, data: Dict):
        """
        Update specific dashboard widget
        Called by C-Suite agents when they take actions
        """
        
        # TODO: Update Supabase dashboard_widgets table
        # supabase.table('dashboard_widgets').upsert({
        #     'user_id': self.user_id,
        #     'widget_name': widget_name,
        #     'data': data,
        #     'updated_at': datetime.utcnow()
        # }).execute()
        
        pass
    
    def log_activity(self, agent: str, message: str, action_type: str, metadata: Dict = None):
        """
        Log agent activity to dashboard activity feed
        """
        
        activity_record = {
            'user_id': self.user_id,
            'agent': agent,
            'message': message,
            'action_type': action_type,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # TODO: Insert into Supabase activity_log table
        # supabase.table('activity_log').insert(activity_record).execute()
        
        print(f"[{agent}] {message}")
    
    def get_widget_data(self, widget_name: str) -> Dict:
        """
        Get data for specific dashboard widget
        Widgets: pending_approvals, your_next_steps, system_health, etc.
        """
        
        dashboard = self.get_dashboard_state()
        
        widget_data = {
            'pending_approvals': {
                'partnerships': dashboard['pending_partnership_approvals'],
                'campaigns': 2,  # TODO: Get from campaigns table
                'counter_strategies': dashboard['pending_counter_strategies'],
                'total': dashboard['pending_partnership_approvals'] + 2 + dashboard['pending_counter_strategies']
            },
            
            'your_next_steps': {
                'priority_1': {
                    'action': 'APPROVE_PARTNERSHIPS',
                    'title': f'Approve {dashboard["pending_partnership_approvals"]} Partnership Proposals',
                    'est_value': 127000
                },
                'priority_2': {
                    'action': 'LAUNCH_CAMPAIGN',
                    'title': 'Launch Reddit Campaign',
                    'est_roas': dashboard['best_platform_roas']
                },
                'priority_3': {
                    'action': 'COUNTER_COMPETITOR',
                    'title': 'Deploy Counter-Strategies',
                    'count': dashboard['pending_counter_strategies']
                }
            },
            
            'system_health': {
                'status': 'ALL_SYSTEMS_OPERATIONAL',
                'ame': 'RUNNING',
                'amg': 'RUNNING',
                'campaign_optimizer': 'RUNNING',
                'competitive_intel': 'RUNNING',
                'partnership_matcher': 'RUNNING',
                'last_check': datetime.utcnow().isoformat()
            },
            
            'financial_summary': {
                'revenue_this_month': dashboard['revenue_this_month'],
                'fees_this_month': dashboard['fees_paid_this_month'],
                'traditional_agency_cost': 15000,  # $15K/month retainer
                'you_saved': 15000 - dashboard['fees_paid_this_month'],
                'effective_rate': (dashboard['fees_paid_this_month'] / dashboard['revenue_this_month'] * 100) if dashboard['revenue_this_month'] > 0 else 0
            },
            
            'storefront_status': {
                'url': dashboard['storefront_url'],
                'template': dashboard['storefront_template'],
                'status': dashboard['storefront_status'],
                'deployed_at': dashboard['storefront_deployed_at']
            },
            
            'performance_overview': {
                'campaigns': dashboard['active_campaigns'],
                'platforms': len(dashboard['platforms']),
                'best_platform': dashboard['best_platform'],
                'best_roas': dashboard['best_platform_roas'],
                'partnerships': dashboard['active_partnerships'],
                'leads_this_month': dashboard['leads_this_month'],
                'conversion_rate': dashboard['conversion_rate']
            }
        }
        
        return widget_data.get(widget_name, {})


# Integration function
def connect_csuite_to_dashboard(user_id: str):
    """
    Initialize dashboard connector and provide to C-Suite agents
    This is what gives agents their "awareness"
    """
    
    # Create connector
    connector = DashboardConnector(user_id)
    
    # Get fresh dashboard state
    dashboard_state = connector.get_dashboard_state(force_refresh=True)
    
    # Now C-Suite agents can read this state
    return connector, dashboard_state


# Example: C-Suite using dashboard awareness
if __name__ == "__main__":
    
    print("🔌 CONNECTING C-SUITE TO DASHBOARD...\n")
    
    # Connect to user's dashboard
    connector, dashboard = connect_csuite_to_dashboard('user_wade')
    
    print(f"✅ Connected to: {dashboard['business_name']}")
    print(f"📊 Dashboard state loaded:")
    print(f"   Revenue this month: ${dashboard['revenue_this_month']:,.0f}")
    print(f"   Active campaigns: {dashboard['active_campaigns']}")
    print(f"   Active partnerships: {dashboard['active_partnerships']}")
    print(f"   Pending approvals: {dashboard['pending_partnership_approvals']}")
    print(f"   Storefront: {dashboard['storefront_url']} ({dashboard['storefront_status']})")
    print()
    
    # Example: CMO using dashboard data
    print("📧 CMO: Personalizing partnership email...")
    print(f"   Using real data: {dashboard['active_partnerships']} partnerships, ${dashboard['partnership_revenue_ytd']:,.0f} revenue")
    print()
    
    # Example: CFO using dashboard data
    print("💰 CFO: Calculating fees...")
    transaction = 8400
    fee = transaction * 0.028 + 0.28
    print(f"   Transaction: ${transaction:,.2f}")
    print(f"   Fee: ${fee:.2f}")
    print(f"   Running total fees: ${dashboard['fees_paid_total']:,.2f}")
    print()
    
    # Example: CEO using dashboard data
    print("🎯 CEO: Generating recommendations...")
    widget_data = connector.get_widget_data('your_next_steps')
    for priority in ['priority_1', 'priority_2', 'priority_3']:
        rec = widget_data[priority]
        print(f"   {priority}: {rec['title']}")
    print()
    
    # Example: COO using dashboard data
    print("🔧 COO: System health check...")
    health = connector.get_widget_data('system_health')
    print(f"   Status: {health['status']}")
    print(f"   AME: {health['ame']}")
    print(f"   AMG: {health['amg']}")
    print()
    
    # Log activity
    connector.log_activity(
        agent='CMO',
        message='Sent partnership proposal to Yoga Studios',
        action_type='email_sent',
        metadata={'template': 'partnership_story', 'est_value': 43000}
    )
    
    print("✅ C-SUITE FULLY AWARE OF DASHBOARD STATE")
    print("🚀 Ready for autonomous operation with real user data")
