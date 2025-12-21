"""
MARKETING AME INTEGRATION
Autonomous Marketing Engine that uses email templates for auto-pitching
Fires automatically based on opportunities discovered by AMG
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MarketingAME:
    """
    Autonomous Marketing Engine for Marketing SKU
    
    Uses the 13 email templates as ammunition for:
    - Welcome sequences (immediate on signup)
    - Partnership proposals (when AMG finds matches)
    - Competitive intelligence (when moves detected)
    - Nurture campaigns (scheduled based on user journey)
    - Re-engagement (when inactivity detected)
    """
    
    def __init__(self, user_id: str, dashboard_state: Dict, email_templates: Dict):
        self.user_id = user_id
        self.dashboard = dashboard_state
        self.email_templates = email_templates
        self.pitch_history = []
    
    def auto_pitch_partnership(self, partnership_opp: Dict) -> Dict:
        """
        AMG found partnership → AME automatically drafts + sends proposal
        Uses Email Template #4 (Partnership Story)
        
        Flow:
        1. AMG discovers partnership opportunity
        2. Scores match quality (94% for example)
        3. AME loads Template #4
        4. Personalizes with user's dashboard data
        5. Checks approval requirements
        6. Either auto-sends OR queues for user approval
        """
        
        # Load partnership template
        template = self.email_templates['partnership_story']
        
        # Get user's actual data from dashboard
        user_data = {
            'sender_name': self.dashboard['sender_name'],
            'business_name': self.dashboard['business_name'],
            'active_partnerships': self.dashboard['active_partnerships'],
            'partnership_revenue': self.dashboard['partnership_revenue_ytd'],
            'storefront_url': self.dashboard['storefront_url']
        }
        
        # Personalize template with BOTH user data AND opportunity data
        personalized_email = template.format(
            first_name=partnership_opp['contact_name'],
            business_type=partnership_opp['business_type'],
            match_score=partnership_opp['match_score'],
            audience_overlap=partnership_opp['audience_overlap'],
            estimated_value=f"${partnership_opp['estimated_annual_value']:,.0f}",
            **user_data
        )
        
        # Create pitch record
        pitch = {
            'ame_id': f"ame_pitch_{datetime.utcnow().timestamp()}",
            'template_used': 'partnership_story',
            'opportunity_type': 'partnership',
            'target': {
                'business_name': partnership_opp['business_name'],
                'contact_name': partnership_opp['contact_name'],
                'contact_email': partnership_opp['contact_email']
            },
            'email_subject': f"Partnership Opportunity: {user_data['business_name']} + {partnership_opp['business_name']}",
            'email_body': personalized_email,
            'estimated_value': partnership_opp['estimated_annual_value'],
            'match_score': partnership_opp['match_score'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Check if requires approval
        requires_approval = self._check_approval_required(pitch)
        
        if requires_approval:
            pitch['status'] = 'PENDING_APPROVAL'
            pitch['approval_widget'] = 'pending_approvals'
            pitch['approval_message'] = f"Partnership proposal ready: {partnership_opp['business_name']} (${partnership_opp['estimated_annual_value']:,.0f}/year est.)"
            
            # Queue for user approval in dashboard
            self._queue_for_approval(pitch)
        else:
            pitch['status'] = 'AUTO_SENT'
            pitch['sent_at'] = datetime.utcnow().isoformat()
            pitch['auto_send_reason'] = f"Under auto-approve threshold ${self.dashboard['auto_approve_threshold']:,.0f}"
            
            # Auto-send immediately
            self._send_email(pitch)
        
        # Log to dashboard
        self._log_to_dashboard(
            f"AME: Partnership pitch {'queued for approval' if requires_approval else 'auto-sent'} - {partnership_opp['business_name']}"
        )
        
        # Track pitch history
        self.pitch_history.append(pitch)
        
        return pitch
    
    def auto_send_welcome_sequence(self, new_lead: Dict) -> List[Dict]:
        """
        New lead captured → AME automatically triggers welcome sequence
        Uses Email Templates #1, #2, #3
        
        Schedule:
        - Email 1: Immediate
        - Email 2: 24 hours later
        - Email 3: 7 days later
        """
        
        scheduled_emails = []
        
        # Email 1: Immediate welcome
        email_1 = self.email_templates['welcome_1'].format(
            first_name=new_lead['first_name'],
            your_name=self.dashboard['sender_name'],
            your_agency=self.dashboard['business_name'],
            dashboard_link=f"{self.dashboard['storefront_url']}/dashboard"
        )
        
        pitch_1 = {
            'ame_id': f"ame_welcome_1_{new_lead['email']}_{datetime.utcnow().timestamp()}",
            'template_used': 'welcome_1',
            'sequence': 'welcome',
            'email_number': 1,
            'target': new_lead,
            'subject': f"Welcome to {self.dashboard['business_name']} - Let's Make Magic Happen 🚀",
            'body': email_1,
            'send_at': datetime.utcnow(),
            'status': 'AUTO_SENT',
            'auto_send_reason': 'Welcome emails auto-send (no approval needed)'
        }
        
        # Send immediately
        self._send_email(pitch_1)
        scheduled_emails.append(pitch_1)
        
        # Email 2: 24 hours
        send_time_2 = datetime.utcnow() + timedelta(hours=24)
        email_2 = self.email_templates['welcome_2'].format(
            first_name=new_lead['first_name'],
            your_name=self.dashboard['sender_name'],
            platform_name='Reddit',  # Could be dynamic based on best platform
            other_platform='Google',
            competitor_name='[Top Competitor]',
            book_call_link=f"{self.dashboard['storefront_url']}/book"
        )
        
        pitch_2 = {
            'ame_id': f"ame_welcome_2_{new_lead['email']}_{datetime.utcnow().timestamp()}",
            'template_used': 'welcome_2',
            'sequence': 'welcome',
            'email_number': 2,
            'target': new_lead,
            'subject': 'Your First 24 Hours: Here\'s What We Found 📊',
            'body': email_2,
            'send_at': send_time_2.isoformat(),
            'status': 'SCHEDULED',
            'auto_send_reason': 'Part of welcome sequence'
        }
        
        self._schedule_email(pitch_2)
        scheduled_emails.append(pitch_2)
        
        # Email 3: 7 days
        send_time_3 = datetime.utcnow() + timedelta(days=7)
        email_3 = self.email_templates['welcome_3'].format(
            first_name=new_lead['first_name'],
            your_name=self.dashboard['sender_name'],
            competitor='[Competitor]',
            dashboard_link=f"{self.dashboard['storefront_url']}/dashboard"
        )
        
        pitch_3 = {
            'ame_id': f"ame_welcome_3_{new_lead['email']}_{datetime.utcnow().timestamp()}",
            'template_used': 'welcome_3',
            'sequence': 'welcome',
            'email_number': 3,
            'target': new_lead,
            'subject': 'Week 1 Results + What Makes Us Different 💡',
            'body': email_3,
            'send_at': send_time_3.isoformat(),
            'status': 'SCHEDULED',
            'auto_send_reason': 'Part of welcome sequence'
        }
        
        self._schedule_email(pitch_3)
        scheduled_emails.append(pitch_3)
        
        self._log_to_dashboard(
            f"AME: Welcome sequence triggered for {new_lead['first_name']} (3 emails scheduled)"
        )
        
        return scheduled_emails
    
    def auto_send_competitive_alert(self, competitor_intel: Dict) -> Dict:
        """
        Competitive intelligence detected move → AME sends alert
        Uses Email Template #5 (Competitor Campaign)
        
        Sent to: Existing clients/users
        Auto-send: Yes (informational, no approval needed)
        """
        
        template = self.email_templates['competitor_campaign']
        
        email_body = template.format(
            first_name='[Client]',  # Will be personalized per recipient
            competitor_name=competitor_intel['competitor_name'],
            campaign_description=competitor_intel['campaign_brief'],
            counter_strategies_count=len(competitor_intel['counter_strategies']),
            your_name=self.dashboard['sender_name'],
            view_intel_link=f"{self.dashboard['storefront_url']}/intel",
            dashboard_link=f"{self.dashboard['storefront_url']}/dashboard"
        )
        
        pitch = {
            'ame_id': f"ame_competitive_{competitor_intel['competitor_name']}_{datetime.utcnow().timestamp()}",
            'template_used': 'competitor_campaign',
            'opportunity_type': 'competitive_intel',
            'target': 'existing_clients',  # Broadcast
            'subject': f"Why {competitor_intel['competitor_name']}'s Campaign Is About To Stop Working ⚠️",
            'body': email_body,
            'competitor': competitor_intel['competitor_name'],
            'counter_strategies_available': len(competitor_intel['counter_strategies']),
            'status': 'AUTO_SENT',
            'auto_send_reason': 'Competitive alerts auto-send to existing clients',
            'sent_at': datetime.utcnow().isoformat()
        }
        
        # Auto-send to client list
        self._send_email_broadcast(pitch)
        
        self._log_to_dashboard(
            f"AME: Sent competitive intel alert about {competitor_intel['competitor_name']} to all clients"
        )
        
        return pitch
    
    def handle_inactivity_trigger(self, inactive_user: Dict, days_inactive: int) -> Dict:
        """
        User inactive → AME sends re-engagement email
        Uses Email Templates #12 (14 days) or #13 (21 days)
        """
        
        if days_inactive >= 21:
            template = self.email_templates['reengagement_2']
            subject = "Quick Check-In: Is Everything Working for You? 💬"
        else:
            template = self.email_templates['reengagement_1']
            subject = "Haven't Seen You in the Dashboard Lately 👀"
        
        email_body = template.format(
            first_name=inactive_user['first_name'],
            days_inactive=days_inactive,
            revenue_generated='[AMOUNT]',  # Pull from their dashboard
            your_name=self.dashboard['sender_name'],
            dashboard_link=f"{self.dashboard['storefront_url']}/dashboard"
        )
        
        pitch = {
            'ame_id': f"ame_reengagement_{inactive_user['email']}_{datetime.utcnow().timestamp()}",
            'template_used': 'reengagement_1' if days_inactive < 21 else 'reengagement_2',
            'sequence': 'reengagement',
            'target': inactive_user,
            'subject': subject,
            'body': email_body,
            'days_inactive': days_inactive,
            'status': 'AUTO_SENT',
            'auto_send_reason': 'Re-engagement emails auto-send',
            'sent_at': datetime.utcnow().isoformat()
        }
        
        self._send_email(pitch)
        
        self._log_to_dashboard(
            f"AME: Sent re-engagement email to {inactive_user['first_name']} ({days_inactive} days inactive)"
        )
        
        return pitch
    
    def _check_approval_required(self, pitch: Dict) -> bool:
        """Check if pitch requires user approval based on dashboard preferences"""
        
        # Check approval requirements from dashboard
        requires_approval_for = self.dashboard.get('requires_approval_for', [])
        
        # Partnership over threshold?
        if pitch['opportunity_type'] == 'partnership':
            threshold = self.dashboard.get('auto_approve_threshold', 10000)
            if pitch['estimated_value'] >= threshold:
                return True
        
        # Campaign over $5K?
        if 'campaign' in pitch.get('opportunity_type', '') and pitch.get('budget', 0) >= 5000:
            return True
        
        # User specifically requires approval for this type?
        if pitch['opportunity_type'] in requires_approval_for:
            return True
        
        return False
    
    def _send_email(self, pitch: Dict):
        """Actually send email via Resend/SMTP"""
        # TODO: Integrate with Resend
        # resend.Emails.send({
        #     'from': f"{self.dashboard['sender_name']} <{self.dashboard['sender_email']}>",
        #     'to': pitch['target']['contact_email'],
        #     'subject': pitch['subject'],
        #     'html': pitch['body']
        # })
        pass
    
    def _send_email_broadcast(self, pitch: Dict):
        """Send email to multiple recipients (existing clients)"""
        # TODO: Integrate with Resend for broadcast
        pass
    
    def _schedule_email(self, pitch: Dict):
        """Schedule email for future send"""
        # TODO: Add to email scheduler queue
        pass
    
    def _queue_for_approval(self, pitch: Dict):
        """Add to dashboard pending approvals widget"""
        # TODO: Integrate with dashboard API
        pass
    
    def _log_to_dashboard(self, message: str):
        """Log activity to dashboard"""
        # TODO: Integrate with dashboard activity log
        print(f"[DASHBOARD LOG] {message}")
    
    def get_pitch_stats(self) -> Dict:
        """
        Get AME performance stats for dashboard
        """
        
        total_pitches = len(self.pitch_history)
        auto_sent = len([p for p in self.pitch_history if p['status'] == 'AUTO_SENT'])
        pending_approval = len([p for p in self.pitch_history if p['status'] == 'PENDING_APPROVAL'])
        
        return {
            'total_pitches_24h': total_pitches,
            'auto_sent': auto_sent,
            'pending_approval': pending_approval,
            'templates_used': list(set([p['template_used'] for p in self.pitch_history])),
            'partnership_pitches': len([p for p in self.pitch_history if p.get('opportunity_type') == 'partnership']),
            'competitive_alerts': len([p for p in self.pitch_history if p.get('opportunity_type') == 'competitive_intel']),
            'welcome_sequences': len([p for p in self.pitch_history if p.get('sequence') == 'welcome'])
        }


# Integration with AMG (Autonomous Marketing Growth)
def integrate_ame_with_amg(user_id: str, dashboard_state: Dict):
    """
    Connect AME with AMG for full autonomous operation
    
    Flow:
    1. AMG scans 8 platforms hourly
    2. AMG finds opportunities (partnerships, competitors, leads)
    3. AMG triggers AME with opportunity data
    4. AME loads appropriate email template
    5. AME personalizes with user's dashboard data
    6. AME either auto-sends OR queues for approval
    7. Dashboard updates in real-time
    """
    
    # Load email templates
    with open('/home/claude/marketing-email-sequences.json', 'r') as f:
        email_data = json.load(f)
    
    # Extract just the email bodies as templates
    email_templates = {}
    for sequence_name, emails in email_data['email_sequences'].items():
        for email in emails:
            key = f"{sequence_name.split('_')[0]}_{email['email_number']}"
            email_templates[key] = '\n'.join(email['body'])
    
    # Initialize AME
    ame = MarketingAME(
        user_id=user_id,
        dashboard_state=dashboard_state,
        email_templates=email_templates
    )
    
    return ame


# Example: Full autonomous flow
if __name__ == "__main__":
    
    # Simulate user's dashboard state
    dashboard_state = {
        'sender_name': 'Wade',
        'sender_email': 'wade@aigentsy.com',
        'business_name': 'AiGentsy Marketing',
        'active_partnerships': 8,
        'partnership_revenue_ytd': 127000,
        'storefront_url': 'https://wade.aigentsy.com',
        'auto_approve_threshold': 10000,
        'requires_approval_for': ['campaigns_over_5k']
    }
    
    # Initialize AME
    ame = integrate_ame_with_amg('user_wade', dashboard_state)
    
    print("🤖 AME INITIALIZED - READY TO AUTO-PITCH\n")
    
    # Scenario 1: AMG found partnership
    print("📊 AMG: Found partnership opportunity...")
    partnership_opp = {
        'business_name': 'Yoga Studio Network',
        'business_type': 'yoga studios',
        'contact_name': 'Elena',
        'contact_email': 'elena@yogastudios.com',
        'estimated_annual_value': 43000,
        'match_score': 0.94,
        'audience_overlap': '87%'
    }
    
    pitch = ame.auto_pitch_partnership(partnership_opp)
    print(f"✅ AME: {pitch['status']} - {pitch.get('approval_message', 'Email sent')}\n")
    
    # Scenario 2: New lead captured
    print("🎯 New lead captured on storefront...")
    new_lead = {
        'first_name': 'Sarah',
        'email': 'sarah@example.com',
        'source': 'landing_page'
    }
    
    sequence = ame.auto_send_welcome_sequence(new_lead)
    print(f"✅ AME: Welcome sequence triggered ({len(sequence)} emails scheduled)\n")
    
    # Scenario 3: Competitor move detected
    print("⚠️ AMG: Competitor move detected...")
    competitor_intel = {
        'competitor_name': 'Traditional Agency Co',
        'campaign_brief': 'Increased ad spend 40% on Facebook',
        'counter_strategies': [
            'Strategy A: Shift to Reddit',
            'Strategy B: Increase Google Ads',
            'Strategy C: Launch partnership blitz'
        ]
    }
    
    alert = ame.auto_send_competitive_alert(competitor_intel)
    print(f"✅ AME: {alert['status']} - Competitive alert sent to clients\n")
    
    # Show stats
    stats = ame.get_pitch_stats()
    print("📈 AME PERFORMANCE STATS:")
    print(f"Total pitches: {stats['total_pitches_24h']}")
    print(f"Auto-sent: {stats['auto_sent']}")
    print(f"Pending approval: {stats['pending_approval']}")
    print(f"Templates used: {', '.join(stats['templates_used'])}")
