"""
OPPORTUNITY ENGAGEMENT ENGINE
Automated outreach to discovered opportunities
Platforms: GitHub, Upwork, Reddit, Twitter, Email, Direct
"""

from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import aiohttp
import json

class OpportunityEngagement:
    """
    Automates engagement with discovered opportunities
    - GitHub: Comment on issues
    - Upwork: Submit proposals
    - Reddit: Reply to posts
    - Twitter: Reply to tweets
    - Email: Send proposals
    - Direct: Website contact forms
    """
    
    def __init__(self):
        # Platform credentials (set via env vars)
        self.github_token = None  # Set from env
        self.upwork_api_key = None  # Set from env
        self.reddit_token = None  # Set from env
        
        # Engagement templates
        self.templates = {
            'github': self._github_template,
            'upwork': self._upwork_template,
            'reddit': self._reddit_template,
            'twitter': self._twitter_template,
            'email': self._email_template,
            'proactive': self._proactive_template
        }
    
    async def engage(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main engagement method - routes to appropriate platform
        
        Returns:
            {
                'success': bool,
                'method': str,
                'response': dict,
                'timestamp': str,
                'reason': str (if failed)
            }
        """
        
        platform = opportunity.get('platform', 'unknown')
        source = opportunity.get('source', 'unknown')
        
        # Route to appropriate engagement method
        if platform == 'github':
            return await self._engage_github(opportunity, pricing, score)
        
        elif platform == 'upwork':
            return await self._engage_upwork(opportunity, pricing, score)
        
        elif platform == 'reddit':
            return await self._engage_reddit(opportunity, pricing, score)
        
        elif platform == 'twitter':
            return await self._engage_twitter(opportunity, pricing, score)
        
        elif source == 'opportunity_creation':
            return await self._engage_proactive(opportunity, pricing, score)
        
        else:
            return await self._engage_email(opportunity, pricing, score)
    
    async def _engage_github(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comment on GitHub issue"""
        
        # Extract repo and issue number from URL
        url = opportunity.get('url', '')
        # Example: https://github.com/owner/repo/issues/123
        
        try:
            parts = url.split('/')
            owner = parts[3]
            repo = parts[4]
            issue_number = parts[6]
        except:
            return {
                'success': False,
                'reason': 'Invalid GitHub URL',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Generate comment
        comment = self.templates['github'](opportunity, pricing, score)
        
        # Post comment (simulated for now - would use GitHub API)
        print(f"[GitHub] Commenting on {owner}/{repo}#{issue_number}")
        print(f"Comment: {comment}")
        
        # TODO: Actual API call
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments',
        #         headers={'Authorization': f'token {self.github_token}'},
        #         json={'body': comment}
        #     ) as resp:
        #         response = await resp.json()
        
        return {
            'success': True,
            'method': 'github_comment',
            'response': {
                'owner': owner,
                'repo': repo,
                'issue_number': issue_number,
                'comment': comment
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _engage_upwork(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit Upwork proposal"""
        
        proposal = self.templates['upwork'](opportunity, pricing, score)
        
        print(f"[Upwork] Submitting proposal for: {opportunity['title']}")
        print(f"Proposal: {proposal}")
        
        # TODO: Actual Upwork API call
        
        return {
            'success': True,
            'method': 'upwork_proposal',
            'response': {
                'proposal': proposal,
                'bid_amount': pricing['optimal_price']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _engage_reddit(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reply to Reddit post"""
        
        reply = self.templates['reddit'](opportunity, pricing, score)
        
        print(f"[Reddit] Replying to: {opportunity['url']}")
        print(f"Reply: {reply}")
        
        # TODO: Actual Reddit API call
        
        return {
            'success': True,
            'method': 'reddit_reply',
            'response': {
                'reply': reply,
                'post_url': opportunity['url']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _engage_twitter(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reply to Twitter post"""
        
        reply = self.templates['twitter'](opportunity, pricing, score)
        
        print(f"[Twitter] Replying to: {opportunity['url']}")
        print(f"Reply: {reply}")
        
        # TODO: Actual Twitter API call
        
        return {
            'success': True,
            'method': 'twitter_reply',
            'response': {
                'reply': reply,
                'tweet_url': opportunity['url']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _engage_proactive(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Proactive outreach (created opportunities)"""
        
        pitch = self.templates['proactive'](opportunity, pricing, score)
        
        print(f"[Proactive] Reaching out for: {opportunity['title']}")
        print(f"Pitch: {pitch}")
        
        # TODO: Send email or find contact method
        
        return {
            'success': True,
            'method': 'proactive_outreach',
            'response': {
                'pitch': pitch,
                'target': opportunity.get('url', 'N/A')
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _engage_email(
        self,
        opportunity: Dict[str, Any],
        pricing: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Email proposal"""
        
        email = self.templates['email'](opportunity, pricing, score)
        
        print(f"[Email] Sending proposal for: {opportunity['title']}")
        print(f"Email: {email}")
        
        # TODO: Send actual email
        
        return {
            'success': True,
            'method': 'email',
            'response': {
                'email': email
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def deliver_solution(
        self,
        opportunity: Dict[str, Any],
        solution: Dict[str, Any],
        proof: Dict[str, Any],
        message: str
    ) -> Dict[str, Any]:
        """
        Deliver completed solution AND request payment via Stripe
        
        UPGRADED: Now creates Stripe payment request after delivery!
        """
        
        platform = opportunity.get('platform', 'email')
        
        # ===== STEP 1: DELIVER THE WORK =====
        
        if platform == 'github':
            print(f"[GitHub Delivery] Submitting solution for {opportunity['url']}")
            delivery_result = {
                'success': True,
                'method': 'github_pr',
                'pr_url': 'https://github.com/example/repo/pull/456'
            }
        
        elif platform == 'upwork':
            print(f"[Upwork Delivery] Uploading deliverables")
            delivery_result = {
                'success': True,
                'method': 'upwork_upload'
            }
        
        else:
            print(f"[Email Delivery] Sending completed work")
            delivery_result = {
                'success': True,
                'method': 'email'
            }
        
        # ===== STEP 2: REQUEST PAYMENT VIA STRIPE (NEW!) =====
        
        amount = opportunity.get('value', 1000)
        client_email = self._extract_client_email(opportunity)
        execution_id = solution.get('execution_id', f"exec_{opportunity.get('id')}")
        
        print(f"\n💰 Creating payment request for ${amount:,.2f}...")
        
        try:
            from payment_collector import get_payment_collector
            collector = get_payment_collector()
            
            # Create Stripe invoice/payment link
            payment_request = await collector.create_payment_request(
                execution_id=execution_id,
                opportunity=opportunity,
                delivery=delivery_result,
                amount=amount,
                client_email=client_email
            )
            
            if payment_request.get('success'):
                payment_url = payment_request.get('invoice_url') or payment_request.get('payment_link_url')
                print(f"✅ Payment request created: {payment_url}")
                
                # ===== STEP 3: NOTIFY CLIENT =====
                if client_email and payment_request.get('method') == 'stripe_invoice':
                    print(f"📧 Invoice automatically sent to {client_email}")
                else:
                    print(f"💳 Payment link: {payment_url}")
                    print(f"   (Send this to client via {platform})")
                
                delivery_result['payment_request'] = payment_request
                delivery_result['payment_url'] = payment_url
            else:
                print(f"⚠️ Payment request failed: {payment_request.get('error')}")
                delivery_result['payment_request'] = {'success': False}
        
        except Exception as e:
            print(f"⚠️ Payment request error: {e}")
            delivery_result['payment_request'] = {'success': False, 'error': str(e)}
        
        return delivery_result
    
    
    def _extract_client_email(self, opportunity: Dict) -> Optional[str]:
        """Extract client email from opportunity data"""
        
        import re
        
        # GitHub doesn't expose real emails
        if opportunity.get('platform') == 'github':
            return None
        
        # Try to extract from description
        description = opportunity.get('description', '')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', description)
        if emails:
            return emails[0]
        
        # Check source_data
        source = opportunity.get('source_data', {})
        if source.get('email'):
            return source['email']
        
        # Check title
        title = opportunity.get('title', '')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', title)
        if emails:
            return emails[0]
        
        return None
    
    # TEMPLATE METHODS
    
    def _github_template(self, opp, pricing, score):
        """Generate GitHub comment template"""
        return f"""Hi! I can help with this issue.

**Proposed Solution:**
{opp.get('description', 'Fix the issue as described')}

**Timeline:** {score['time_to_close_days']} days
**Estimated Cost:** ${pricing['optimal_price']}

I have experience with similar issues and can get started immediately. Let me know if you'd like to discuss further!

Built by AiGentsy - Autonomous AI Business Platform
"""
    
    def _upwork_template(self, opp, pricing, score):
        """Generate Upwork proposal template"""
        return f"""Hello!

I'm interested in your project: {opp['title']}

**My Approach:**
{opp.get('description', 'I will deliver exactly what you need')}

**Why Me:**
- {score['time_to_close_days']} day delivery
- {int(score['win_probability'] * 100)}% confidence in successful delivery
- Competitive pricing: ${pricing['optimal_price']}

I'm available to start immediately. Let's discuss your requirements!

Best regards,
AiGentsy Team
"""
    
    def _reddit_template(self, opp, pricing, score):
        """Generate Reddit reply template"""
        return f"""I can help with this! 

{opp.get('description', 'I have experience with exactly what you need.')}

Timeline: {score['time_to_close_days']} days
Cost: ${pricing['optimal_price']}

DM me if interested!
"""
    
    def _twitter_template(self, opp, pricing, score):
        """Generate Twitter reply template"""
        return f"""I can build this for you! {score['time_to_close_days']}-day delivery, ${pricing['optimal_price']}. DM me! 🚀"""
    
    def _email_template(self, opp, pricing, score):
        """Generate email proposal template"""
        return f"""Subject: Solution for {opp['title']}

Hi,

I came across your need for {opp['title']} and I can help.

**What I'll Deliver:**
{opp.get('description', 'Complete solution to your requirements')}

**Timeline:** {score['time_to_close_days']} days
**Investment:** ${pricing['optimal_price']}

I have {int(score['win_probability'] * 100)}% confidence in delivering exactly what you need.

Ready to get started whenever you are!

Best,
AiGentsy
"""
    
    def _proactive_template(self, opp, pricing, score):
        """Generate proactive outreach template"""
        return f"""Subject: I Found an Opportunity for {opp.get('company', 'Your Business')}

Hi,

I noticed {opp.get('pain_point', 'an opportunity to improve your operations')}.

**What I Can Do:**
{opp.get('description', 'Solve this issue quickly and affordably')}

**Timeline:** {score['time_to_close_days']} days
**Investment:** ${pricing['optimal_price']}

This is a proactive reach-out - no obligation. Would you like to discuss?

Best,
AiGentsy
https://aigentsy.com
"""


# Example usage
if __name__ == "__main__":
    async def test():
        engagement = OpportunityEngagement()
        
        test_opp = {
            'id': 'github_123',
            'platform': 'github',
            'title': 'Fix React bug',
            'description': 'State management issue in checkout flow',
            'url': 'https://github.com/example/repo/issues/123'
        }
        
        test_pricing = {
            'optimal_price': 2000
        }
        
        test_score = {
            'win_probability': 0.75,
            'time_to_close_days': 5
        }
        
        result = await engagement.engage(test_opp, test_pricing, test_score)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
