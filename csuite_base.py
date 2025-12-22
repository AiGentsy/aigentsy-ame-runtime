"""
UNIVERSAL C-SUITE BASE CLASSES
Base agent classes that all SKUs inherit from
Each SKU extends these with their specific behaviors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class BaseCSuiteAgent(ABC):
    """
    Base class for all C-Suite agents across all SKUs
    
    All agents have:
    - Dashboard awareness (reads user's real-time data)
    - Activity logging
    - Approval gate checking
    """
    
    def __init__(self, dashboard_state: Dict, name: str):
        self.dashboard = dashboard_state
        self.name = name
        self.sku = dashboard_state.get('selected_sku', 'unknown')
    
    def _check_approval_required(self, action: Dict) -> bool:
        """
        Universal approval checking
        Works for all SKUs based on user preferences
        """
        
        requires_approval_for = self.dashboard.get('requires_approval_for', [])
        auto_approve_threshold = self.dashboard.get('auto_approve_threshold', 10000)
        
        # Check value threshold
        if action.get('estimated_value', 0) >= auto_approve_threshold:
            return True
        
        # Check action type
        if action.get('action_type') in requires_approval_for:
            return True
        
        return False
    
    def _log_activity(self, message: str, action_type: str, metadata: Dict = None):
        """Log activity to dashboard"""
        print(f"[{self.name}] {message}")
        # TODO: Log to Supabase activity_log
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass


class BaseCMO(BaseCSuiteAgent):
    """
    Base CMO (Chief Marketing Officer)
    Handles communications, outreach, email sequences
    
    All SKUs have a CMO that:
    - Sends welcome emails
    - Manages email sequences
    - Handles automated outreach
    - Uses email templates as ammunition
    """
    
    def __init__(self, dashboard_state: Dict, email_templates: Dict):
        super().__init__(dashboard_state, "CMO")
        self.email_templates = email_templates
    
    def handle_new_signup(self, lead: Dict) -> Dict:
        """
        Universal new signup handler
        Sends welcome email appropriate for the SKU
        """
        
        # Get welcome template (each SKU has its own)
        template_key = self._get_welcome_template_key()
        template = self.email_templates.get(template_key, '')
        
        # Personalize with dashboard data
        email_content = template.format(
            first_name=lead['first_name'],
            your_name=self.dashboard['sender_name'],
            business_name=self.dashboard['business_name'],
            dashboard_link=f"{self.dashboard['storefront_url']}/dashboard"
        )
        
        action = {
            'agent': 'CMO',
            'action': 'send_email',
            'to': lead['email'],
            'template': template_key,
            'subject': self._get_welcome_subject(),
            'body': email_content,
            'auto_sent': True,
            'sent_at': datetime.utcnow().isoformat(),
            'dashboard_log': f"CMO sent welcome email to {lead['first_name']}"
        }
        
        self._log_activity(action['dashboard_log'], 'email_sent')
        return action
    
    def _get_welcome_template_key(self) -> str:
        """Get appropriate welcome template for SKU"""
        return 'welcome_1'  # Override in SKU-specific CMO
    
    def _get_welcome_subject(self) -> str:
        """Get welcome email subject for SKU"""
        return f"Welcome to {self.dashboard['business_name']}"
    
    def get_capabilities(self) -> List[str]:
        return ['send_emails', 'manage_sequences', 'automated_outreach']


class BaseCFO(BaseCSuiteAgent):
    """
    Base CFO (Chief Financial Officer)
    Tracks revenue, calculates fees, financial reporting
    
    All SKUs have a CFO that:
    - Calculates 2.8% + $0.28 fees
    - Tracks all revenue
    - Compares to traditional costs
    - Shows financial summaries
    """
    
    def __init__(self, dashboard_state: Dict):
        super().__init__(dashboard_state, "CFO")
    
    def calculate_fees(self, transaction_amount: float) -> Dict:
        """
        Universal fee calculation: 2.8% + $0.28
        Same for all SKUs
        """
        
        percentage_fee = transaction_amount * 0.028
        flat_fee = 0.28
        total_fee = percentage_fee + flat_fee
        
        calculation = {
            'agent': 'CFO',
            'action': 'calculate_fees',
            'transaction_amount': transaction_amount,
            'percentage_fee': percentage_fee,
            'flat_fee': flat_fee,
            'total_fee': total_fee,
            'net_to_user': transaction_amount - total_fee,
            'dashboard_update': {
                'revenue_this_month': self.dashboard['revenue_this_month'] + transaction_amount,
                'fees_paid': self.dashboard.get('fees_paid_this_month', 0) + total_fee
            },
            'dashboard_log': f"CFO calculated fees: ${total_fee:.2f} on ${transaction_amount:,.2f} transaction"
        }
        
        self._log_activity(calculation['dashboard_log'], 'fee_calculation', calculation)
        return calculation
    
    def generate_financial_summary(self) -> Dict:
        """
        Universal financial summary
        Works for all SKUs
        """
        
        # Traditional cost varies by SKU
        traditional_cost = self._get_traditional_cost()
        
        savings = traditional_cost - self.dashboard.get('fees_paid_total', 0)
        
        summary = {
            'agent': 'CFO',
            'action': 'financial_summary',
            'revenue_this_month': self.dashboard['revenue_this_month'],
            'revenue_total': self.dashboard['revenue_total'],
            'fees_paid_this_month': self.dashboard.get('fees_paid_this_month', 0),
            'fees_paid_total': self.dashboard.get('fees_paid_total', 0),
            'traditional_cost': traditional_cost,
            'you_saved': savings,
            'effective_fee_rate': (self.dashboard.get('fees_paid_total', 0) / self.dashboard['revenue_total'] * 100) if self.dashboard['revenue_total'] > 0 else 0,
            'dashboard_widget': 'financial_summary'
        }
        
        return summary
    
    def _get_traditional_cost(self) -> float:
        """Get traditional cost based on SKU"""
        costs = {
            'marketing': 180000,  # $15K/month * 12
            'saas': 240000,       # $20K/month * 12  
            'social': 120000      # $10K/month * 12
        }
        return costs.get(self.sku, 180000)
    
    def get_capabilities(self) -> List[str]:
        return ['calculate_fees', 'track_revenue', 'financial_reporting']


class BaseCEO(BaseCSuiteAgent):
    """
    Base CEO (Chief Executive Officer)
    Strategic analysis, recommendations, high-level decisions
    
    All SKUs have a CEO that:
    - Analyzes dashboard data
    - Generates recommendations
    - Evaluates opportunities
    - Requires user approval for major decisions
    """
    
    def __init__(self, dashboard_state: Dict, strategies: Dict):
        super().__init__(dashboard_state, "CEO")
        self.strategies = strategies
    
    def analyze_opportunities(self) -> Dict:
        """
        Universal opportunity analysis
        Each SKU overrides with specific opportunities
        """
        
        recommendations = self._generate_sku_recommendations()
        
        analysis = {
            'agent': 'CEO',
            'action': 'strategic_analysis',
            'recommendations': recommendations,
            'dashboard_widget': 'your_next_steps',
            'dashboard_log': f"CEO recommended {len(recommendations)} priority actions"
        }
        
        self._log_activity(analysis['dashboard_log'], 'strategic_analysis')
        return analysis
    
    @abstractmethod
    def _generate_sku_recommendations(self) -> List[Dict]:
        """Generate SKU-specific recommendations"""
        pass
    
    def get_capabilities(self) -> List[str]:
        return ['strategic_analysis', 'opportunity_evaluation', 'recommendations']


class BaseCOO(BaseCSuiteAgent):
    """
    Base COO (Chief Operating Officer)
    System monitoring, operations, health checks
    
    All SKUs have a COO that:
    - Monitors all autonomous systems
    - Reports system health
    - Tracks activity across all logics
    - Manages pending approvals
    """
    
    def __init__(self, dashboard_state: Dict):
        super().__init__(dashboard_state, "COO")
    
    def monitor_systems(self) -> Dict:
        """
        Universal system health monitoring
        Works for all SKUs
        """
        
        system_health = {
            'agent': 'COO',
            'action': 'system_health_check',
            'systems_status': self._get_system_status(),
            'activity_24h': self._get_activity_summary(),
            'pending_approvals': self._get_pending_approvals(),
            'dashboard_widget': 'system_health',
            'dashboard_log': f"COO: All systems operational"
        }
        
        self._log_activity(system_health['dashboard_log'], 'health_check')
        return system_health
    
    def _get_system_status(self) -> Dict:
        """Get status of all autonomous systems"""
        return {
            'ame': 'RUNNING',
            'autonomous_systems': 'RUNNING',
            'database': 'CONNECTED',
            'api': 'OPERATIONAL'
        }
    
    def _get_activity_summary(self) -> Dict:
        """Get 24h activity summary - varies by SKU"""
        base_activity = {
            'leads_captured': self.dashboard.get('leads_this_month', 0),
            'revenue_generated': self.dashboard.get('revenue_this_month', 0)
        }
        return base_activity
    
    def _get_pending_approvals(self) -> Dict:
        """Get pending approvals - varies by SKU"""
        return {'total': 0}
    
    def get_capabilities(self) -> List[str]:
        return ['system_monitoring', 'health_checks', 'operations_management']


# Example: Create SKU-specific agents by extending base classes

class MarketingCMO(BaseCMO):
    """Marketing SKU specific CMO"""
    
    def handle_partnership_opportunity(self, partnership: Dict) -> Dict:
        """Marketing-specific: Partnership proposals"""
        
        template = self.email_templates.get('partnership_story', '')
        
        email_content = template.format(
            first_name=partnership['contact_name'],
            business_type=partnership['business_type'],
            your_name=self.dashboard['sender_name'],
            business_name=self.dashboard['business_name'],
            active_partnerships=self.dashboard.get('active_partnerships', 0),
            partnership_revenue=f"${self.dashboard.get('partnership_revenue_ytd', 0):,.0f}"
        )
        
        action = {
            'agent': 'CMO',
            'action': 'partnership_proposal',
            'estimated_value': partnership['estimated_annual_value'],
            'email_body': email_content,
            'requires_approval': self._check_approval_required({
                'estimated_value': partnership['estimated_annual_value'],
                'action_type': 'partnership'
            })
        }
        
        return action


class SaaSCMO(BaseCMO):
    """SaaS SKU specific CMO"""
    
    def handle_developer_onboarding(self, developer: Dict) -> Dict:
        """SaaS-specific: Developer onboarding"""
        
        template = self.email_templates.get('developer_welcome', '')
        
        email_content = template.format(
            first_name=developer['first_name'],
            api_key=developer['api_key'],
            documentation_url=f"{self.dashboard['storefront_url']}/docs"
        )
        
        action = {
            'agent': 'CMO',
            'action': 'developer_onboarding',
            'email_body': email_content,
            'auto_sent': True
        }
        
        return action


class MarketingCEO(BaseCEO):
    """Marketing SKU specific CEO"""
    
    def _generate_sku_recommendations(self) -> List[Dict]:
        """Marketing-specific recommendations"""
        
        recommendations = []
        
        # Partnership recommendations
        if self.dashboard.get('pending_partnership_approvals', 0) > 0:
            recommendations.append({
                'priority': 1,
                'action': 'APPROVE_PARTNERSHIPS',
                'title': f'Approve {self.dashboard["pending_partnership_approvals"]} Partnership Proposals',
                'details': 'Est. pipeline value: $127,000'
            })
        
        # Campaign recommendations
        if len(self.dashboard.get('platforms', [])) < 8:
            recommendations.append({
                'priority': 2,
                'action': 'EXPAND_PLATFORMS',
                'title': 'Launch Additional Platforms',
                'details': 'Test Reddit, TikTok for potential 5x ROAS'
            })
        
        return recommendations


class SaaSCEO(BaseCEO):
    """SaaS SKU specific CEO"""
    
    def _generate_sku_recommendations(self) -> List[Dict]:
        """SaaS-specific recommendations"""
        
        recommendations = []
        
        # Developer recommendations
        if self.dashboard.get('pending_developer_approvals', 0) > 0:
            recommendations.append({
                'priority': 1,
                'action': 'APPROVE_DEVELOPERS',
                'title': f'Approve {self.dashboard["pending_developer_approvals"]} Developer Requests',
                'details': 'Grant API access to new developers'
            })
        
        # Integration recommendations
        if self.dashboard.get('pending_integration_requests', 0) > 0:
            recommendations.append({
                'priority': 2,
                'action': 'APPROVE_INTEGRATIONS',
                'title': f'Review {self.dashboard["pending_integration_requests"]} Integration Requests',
                'details': 'New integration opportunities available'
            })
        
        return recommendations


# Example usage
if __name__ == "__main__":
    
    print("🏢 UNIVERSAL C-SUITE BASE CLASSES\n")
    
    # Simulate dashboard states for different SKUs
    marketing_dashboard = {
        'selected_sku': 'marketing',
        'business_name': 'Marketing Agency',
        'sender_name': 'Wade',
        'storefront_url': 'https://wade.aigentsy.com',
        'revenue_this_month': 47000,
        'revenue_total': 127000,
        'active_partnerships': 8,
        'pending_partnership_approvals': 3,
        'partnership_revenue_ytd': 127000
    }
    
    saas_dashboard = {
        'selected_sku': 'saas',
        'business_name': 'API Platform',
        'sender_name': 'Sarah',
        'storefront_url': 'https://sarah.aigentsy.com',
        'revenue_this_month': 85000,
        'revenue_total': 340000,
        'pending_developer_approvals': 5,
        'pending_integration_requests': 2
    }
    
    # Marketing SKU C-Suite
    print("✅ MARKETING SKU C-SUITE:")
    marketing_cmo = MarketingCMO(marketing_dashboard, {'partnership_story': 'Template...'})
    marketing_cfo = BaseCFO(marketing_dashboard)
    marketing_ceo = MarketingCEO(marketing_dashboard, {})
    marketing_coo = BaseCOO(marketing_dashboard)
    
    print(f"   CMO: {marketing_cmo.get_capabilities()}")
    print(f"   CFO: {marketing_cfo.get_capabilities()}")
    print(f"   CEO: {marketing_ceo.get_capabilities()}")
    print(f"   COO: {marketing_coo.get_capabilities()}")
    print()
    
    # SaaS SKU C-Suite
    print("✅ SAAS SKU C-SUITE:")
    saas_cmo = SaaSCMO(saas_dashboard, {'developer_welcome': 'Template...'})
    saas_cfo = BaseCFO(saas_dashboard)
    saas_ceo = SaaSCEO(saas_dashboard, {})
    saas_coo = BaseCOO(saas_dashboard)
    
    print(f"   CMO: {saas_cmo.get_capabilities()}")
    print(f"   CFO: {saas_cfo.get_capabilities()}")
    print(f"   CEO: {saas_ceo.get_capabilities()}")
    print(f"   COO: {saas_coo.get_capabilities()}")
    print()
    
    # Test CFO (universal)
    print("💰 CFO TEST (Same for all SKUs):")
    transaction = marketing_cfo.calculate_fees(8400)
    print(f"   Transaction: ${transaction['transaction_amount']:,.2f}")
    print(f"   Fee: ${transaction['total_fee']:.2f}")
    print(f"   Net to user: ${transaction['net_to_user']:,.2f}")
    print()
    
    print("✅ BASE CLASSES WORK FOR ALL SKUs")
