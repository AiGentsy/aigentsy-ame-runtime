"""
CONTRACT & DEPOSIT ENGINE
=========================
Automatically generates service agreements and collects deposits via Stripe.

FLOW:
1. Conversation reaches CLOSING stage
2. Generate service agreement from template
3. Create Stripe Payment Link for deposit (typically 50%)
4. Send contract + payment link to prospect
5. Track payment status via webhook
6. Mark deal as CLOSED_WON when paid

FEATURES:
- Dynamic contract generation
- Stripe Payment Links (no checkout code needed)
- Webhook handling for payment confirmation
- Deposit tracking
- Revenue recording

INTEGRATES WITH:
- conversation_engine.py (triggers contract send)
- direct_outreach_engine.py (sends emails)
- Stripe (payments)
"""

import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import httpx


# =============================================================================
# CONFIGURATION
# =============================================================================

class ContractStatus(Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"  # Future: e-signature integration
    DEPOSIT_PENDING = "deposit_pending"
    DEPOSIT_PAID = "deposit_paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class ServiceContract:
    """A service agreement with payment tracking"""
    contract_id: str
    conversation_id: str
    opportunity_id: str
    
    # Client info
    client_name: str
    client_email: str
    client_company: Optional[str] = None
    
    # Service details
    service_description: str = ""
    deliverables: List[str] = field(default_factory=list)
    timeline: str = "To be determined"
    
    # Pricing
    total_amount: float = 0.0
    deposit_amount: float = 0.0
    deposit_percentage: float = 0.5  # 50% default
    
    # Payment
    stripe_payment_link_id: Optional[str] = None
    stripe_payment_link_url: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    
    # Status
    status: ContractStatus = ContractStatus.DRAFT
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sent_at: Optional[str] = None
    paid_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Content
    contract_html: Optional[str] = None
    contract_text: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'contract_id': self.contract_id,
            'conversation_id': self.conversation_id,
            'opportunity_id': self.opportunity_id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_company': self.client_company,
            'service_description': self.service_description,
            'deliverables': self.deliverables,
            'timeline': self.timeline,
            'total_amount': self.total_amount,
            'deposit_amount': self.deposit_amount,
            'deposit_percentage': self.deposit_percentage,
            'stripe_payment_link_url': self.stripe_payment_link_url,
            'status': self.status.value,
            'payment_status': self.payment_status.value,
            'created_at': self.created_at,
            'sent_at': self.sent_at,
            'paid_at': self.paid_at
        }


# =============================================================================
# CONTRACT TEMPLATES
# =============================================================================

class ContractGenerator:
    """Generates service agreements from templates"""
    
    def __init__(self):
        self.company_name = "AiGentsy"
        self.company_email = os.getenv("AIGENTSY_FROM_EMAIL", "hello@aigentsy.com")
    
    def generate_contract(
        self,
        client_name: str,
        client_email: str,
        service_description: str,
        deliverables: List[str],
        total_amount: float,
        deposit_amount: float,
        timeline: str = "To be agreed upon",
        client_company: str = None
    ) -> tuple[str, str]:
        """
        Generate contract in both HTML and plain text formats.
        Returns: (html_content, text_content)
        """
        
        today = datetime.now().strftime("%B %d, %Y")
        deliverables_html = "\n".join([f"<li>{d}</li>" for d in deliverables])
        deliverables_text = "\n".join([f"  - {d}" for d in deliverables])
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #059669; }}
        .terms {{ font-size: 12px; color: #64748b; }}
        .signature {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; }}
        ul {{ margin: 10px 0; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Service Agreement</h1>
        <p><strong>{self.company_name}</strong></p>
        <p>Date: {today}</p>
    </div>
    
    <div class="section">
        <h2>Parties</h2>
        <p><strong>Service Provider:</strong> {self.company_name}<br>
        Email: {self.company_email}</p>
        <p><strong>Client:</strong> {client_name}<br>
        {f'Company: {client_company}<br>' if client_company else ''}
        Email: {client_email}</p>
    </div>
    
    <div class="section">
        <h2>Services</h2>
        <p>{service_description}</p>
        
        <h3>Deliverables</h3>
        <ul>
            {deliverables_html}
        </ul>
        
        <h3>Timeline</h3>
        <p>{timeline}</p>
    </div>
    
    <div class="section">
        <h2>Investment</h2>
        <p class="amount">Total: ${total_amount:,.2f}</p>
        <p><strong>Deposit Required:</strong> ${deposit_amount:,.2f} (to begin work)</p>
        <p><strong>Balance:</strong> ${total_amount - deposit_amount:,.2f} (due upon completion)</p>
    </div>
    
    <div class="section">
        <h2>Terms & Conditions</h2>
        <ol>
            <li><strong>Satisfaction Guarantee:</strong> Client may request revisions until satisfied with deliverables.</li>
            <li><strong>Deposit:</strong> Deposit is required to begin work and is applied to the total amount.</li>
            <li><strong>Timeline:</strong> Estimated delivery times are provided in good faith but may vary based on complexity.</li>
            <li><strong>Communication:</strong> Provider will maintain regular communication throughout the project.</li>
            <li><strong>Ownership:</strong> Upon full payment, all deliverables become the property of the Client.</li>
            <li><strong>Confidentiality:</strong> Both parties agree to keep project details confidential.</li>
        </ol>
    </div>
    
    <div class="signature">
        <p>By making the deposit payment, Client agrees to the terms outlined in this agreement.</p>
        <p class="terms">This agreement is effective as of {today}.</p>
    </div>
</body>
</html>
"""
        
        text_content = f"""
SERVICE AGREEMENT
=================
{self.company_name}
Date: {today}

PARTIES
-------
Service Provider: {self.company_name}
Email: {self.company_email}

Client: {client_name}
{f'Company: {client_company}' if client_company else ''}
Email: {client_email}

SERVICES
--------
{service_description}

Deliverables:
{deliverables_text}

Timeline: {timeline}

INVESTMENT
----------
Total: ${total_amount:,.2f}
Deposit Required: ${deposit_amount:,.2f} (to begin work)
Balance: ${total_amount - deposit_amount:,.2f} (due upon completion)

TERMS & CONDITIONS
------------------
1. Satisfaction Guarantee: Client may request revisions until satisfied.
2. Deposit: Required to begin work, applied to total amount.
3. Timeline: Estimates provided in good faith, may vary.
4. Communication: Regular updates throughout project.
5. Ownership: Deliverables become Client property upon full payment.
6. Confidentiality: Project details kept confidential.

By making the deposit payment, Client agrees to these terms.

Effective as of {today}.
"""
        
        return html_content.strip(), text_content.strip()


# =============================================================================
# STRIPE INTEGRATION
# =============================================================================

class StripePaymentManager:
    """Manages Stripe Payment Links and webhooks"""
    
    def __init__(self):
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self.base_url = "https://api.stripe.com/v1"
        
        # Product ID for deposits (create once in Stripe dashboard)
        self.deposit_product_id = os.getenv("STRIPE_DEPOSIT_PRODUCT_ID", "")
    
    async def create_payment_link(
        self,
        amount: float,
        client_email: str,
        client_name: str,
        contract_id: str,
        description: str = "Service Deposit"
    ) -> Optional[Dict]:
        """
        Create a Stripe Payment Link for the deposit.
        Returns: {payment_link_id, url} or None
        """
        if not self.stripe_secret_key:
            print("⚠️ Stripe secret key not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # First, create a Price for this specific amount
                price_response = await client.post(
                    f"{self.base_url}/prices",
                    headers={
                        "Authorization": f"Bearer {self.stripe_secret_key}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "currency": "usd",
                        "unit_amount": int(amount * 100),  # Stripe uses cents
                        "product_data[name]": f"Deposit - {description[:50]}",
                        "metadata[contract_id]": contract_id,
                        "metadata[client_email]": client_email
                    },
                    timeout=30
                )
                
                if price_response.status_code != 200:
                    print(f"⚠️ Stripe price creation failed: {price_response.text}")
                    return None
                
                price_data = price_response.json()
                price_id = price_data.get('id')
                
                # Now create the Payment Link
                link_response = await client.post(
                    f"{self.base_url}/payment_links",
                    headers={
                        "Authorization": f"Bearer {self.stripe_secret_key}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "line_items[0][price]": price_id,
                        "line_items[0][quantity]": 1,
                        "metadata[contract_id]": contract_id,
                        "metadata[client_email]": client_email,
                        "metadata[client_name]": client_name,
                        "after_completion[type]": "redirect",
                        "after_completion[redirect][url]": f"https://aigentsy.com/payment-success?contract={contract_id}"
                    },
                    timeout=30
                )
                
                if link_response.status_code == 200:
                    link_data = link_response.json()
                    return {
                        'payment_link_id': link_data.get('id'),
                        'url': link_data.get('url'),
                        'price_id': price_id
                    }
                else:
                    print(f"⚠️ Stripe payment link creation failed: {link_response.text}")
                    return None
                    
        except Exception as e:
            print(f"⚠️ Stripe error: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        if not self.stripe_webhook_secret:
            return True  # Skip verification if not configured
        
        import hmac
        import hashlib
        
        # Stripe uses a specific signature format
        try:
            elements = dict(item.split('=') for item in signature.split(','))
            timestamp = elements.get('t', '')
            expected_sig = elements.get('v1', '')
            
            signed_payload = f"{timestamp}.{payload.decode()}"
            computed = hmac.new(
                self.stripe_webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed, expected_sig)
        except:
            return False
    
    def parse_checkout_completed(self, event: Dict) -> Optional[Dict]:
        """Parse checkout.session.completed event"""
        if event.get('type') != 'checkout.session.completed':
            return None
        
        session = event.get('data', {}).get('object', {})
        
        return {
            'contract_id': session.get('metadata', {}).get('contract_id'),
            'client_email': session.get('metadata', {}).get('client_email') or session.get('customer_email'),
            'amount_paid': session.get('amount_total', 0) / 100,  # Convert from cents
            'payment_intent_id': session.get('payment_intent'),
            'payment_status': session.get('payment_status')
        }


# =============================================================================
# CONTRACT & PAYMENT ENGINE
# =============================================================================

class ContractPaymentEngine:
    """Main engine for contract generation and payment collection"""
    
    def __init__(self):
        self.contract_generator = ContractGenerator()
        self.stripe_manager = StripePaymentManager()
        
        # Storage
        self.contracts: Dict[str, ServiceContract] = {}
        self.email_to_contract: Dict[str, str] = {}  # Latest contract per email
        
        # Stats
        self.stats = {
            'contracts_created': 0,
            'contracts_sent': 0,
            'deposits_collected': 0,
            'total_deposit_amount': 0.0,
            'total_contract_value': 0.0
        }
    
    async def create_contract(
        self,
        conversation_id: str,
        opportunity_id: str,
        client_name: str,
        client_email: str,
        service_description: str,
        deliverables: List[str],
        total_amount: float,
        deposit_percentage: float = 0.5,
        timeline: str = "To be agreed upon",
        client_company: str = None
    ) -> ServiceContract:
        """Create a new service contract"""
        
        contract_id = f"contract_{hashlib.md5(f'{conversation_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        deposit_amount = total_amount * deposit_percentage
        
        # Generate contract content
        html_content, text_content = self.contract_generator.generate_contract(
            client_name=client_name,
            client_email=client_email,
            service_description=service_description,
            deliverables=deliverables,
            total_amount=total_amount,
            deposit_amount=deposit_amount,
            timeline=timeline,
            client_company=client_company
        )
        
        contract = ServiceContract(
            contract_id=contract_id,
            conversation_id=conversation_id,
            opportunity_id=opportunity_id,
            client_name=client_name,
            client_email=client_email,
            client_company=client_company,
            service_description=service_description,
            deliverables=deliverables,
            timeline=timeline,
            total_amount=total_amount,
            deposit_amount=deposit_amount,
            deposit_percentage=deposit_percentage,
            contract_html=html_content,
            contract_text=text_content
        )
        
        # Store
        self.contracts[contract_id] = contract
        self.email_to_contract[client_email.lower()] = contract_id
        
        self.stats['contracts_created'] += 1
        self.stats['total_contract_value'] += total_amount
        
        return contract
    
    async def create_payment_link(self, contract_id: str) -> Optional[str]:
        """Create Stripe payment link for contract deposit"""
        
        contract = self.contracts.get(contract_id)
        if not contract:
            return None
        
        result = await self.stripe_manager.create_payment_link(
            amount=contract.deposit_amount,
            client_email=contract.client_email,
            client_name=contract.client_name,
            contract_id=contract_id,
            description=contract.service_description[:50]
        )
        
        if result:
            contract.stripe_payment_link_id = result['payment_link_id']
            contract.stripe_payment_link_url = result['url']
            contract.status = ContractStatus.DEPOSIT_PENDING
            return result['url']
        
        return None
    
    async def prepare_and_send_contract(
        self,
        contract_id: str
    ) -> Dict[str, Any]:
        """
        Prepare contract with payment link and return send-ready package.
        Actual sending done by outreach engine.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return {"error": "Contract not found"}
        
        # Create payment link if not exists
        if not contract.stripe_payment_link_url:
            payment_url = await self.create_payment_link(contract_id)
            if not payment_url:
                # Continue without payment link (can add manually)
                payment_url = "[Payment link will be provided separately]"
        else:
            payment_url = contract.stripe_payment_link_url
        
        # Generate email content
        email_subject = f"Service Agreement - {contract.service_description[:30]}..."
        
        email_body = f"""Hi {contract.client_name},

Thank you for choosing to work with us! I'm excited to get started.

Please find your service agreement below. To begin work, simply make the deposit payment using the secure link.

📋 **Service Agreement**
{contract.contract_text}

💳 **Make Your Deposit**
Click here to pay securely: {payment_url}

Deposit Amount: ${contract.deposit_amount:,.2f}

Once the deposit is received, we'll begin work immediately. You'll receive regular updates throughout the project.

Questions? Just reply to this email.

Best,
The AiGentsy Team
"""
        
        # Update status
        contract.status = ContractStatus.SENT
        contract.sent_at = datetime.now(timezone.utc).isoformat()
        self.stats['contracts_sent'] += 1
        
        return {
            "ok": True,
            "contract_id": contract_id,
            "client_email": contract.client_email,
            "subject": email_subject,
            "body": email_body,
            "payment_link": payment_url,
            "deposit_amount": contract.deposit_amount,
            "total_amount": contract.total_amount
        }
    
    async def process_payment_webhook(self, event: Dict) -> Optional[str]:
        """Process Stripe webhook for payment confirmation"""
        
        payment_data = self.stripe_manager.parse_checkout_completed(event)
        
        if not payment_data or not payment_data.get('contract_id'):
            return None
        
        contract_id = payment_data['contract_id']
        contract = self.contracts.get(contract_id)
        
        if not contract:
            print(f"⚠️ Contract not found for payment: {contract_id}")
            return None
        
        # Update contract
        contract.payment_status = PaymentStatus.PAID
        contract.status = ContractStatus.DEPOSIT_PAID
        contract.paid_at = datetime.now(timezone.utc).isoformat()
        contract.stripe_payment_intent_id = payment_data.get('payment_intent_id')
        
        # Update stats
        self.stats['deposits_collected'] += 1
        self.stats['total_deposit_amount'] += payment_data.get('amount_paid', contract.deposit_amount)
        
        print(f"💰 Payment received for contract {contract_id}: ${payment_data.get('amount_paid', 0)}")
        
        return contract_id
    
    def get_contract_by_email(self, email: str) -> Optional[ServiceContract]:
        """Get latest contract for email"""
        contract_id = self.email_to_contract.get(email.lower())
        return self.contracts.get(contract_id) if contract_id else None
    
    def get_pending_payments(self) -> List[ServiceContract]:
        """Get contracts awaiting payment"""
        return [
            c for c in self.contracts.values()
            if c.status == ContractStatus.DEPOSIT_PENDING and c.payment_status == PaymentStatus.PENDING
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get contract/payment stats"""
        pending = len(self.get_pending_payments())
        paid = self.stats['deposits_collected']
        
        return {
            **self.stats,
            'pending_payments': pending,
            'payment_conversion_rate': paid / self.stats['contracts_sent'] if self.stats['contracts_sent'] > 0 else 0,
            'average_contract_value': self.stats['total_contract_value'] / self.stats['contracts_created'] if self.stats['contracts_created'] > 0 else 0
        }


# =============================================================================
# SINGLETON
# =============================================================================

_contract_engine = None

def get_contract_engine() -> ContractPaymentEngine:
    global _contract_engine
    if _contract_engine is None:
        _contract_engine = ContractPaymentEngine()
    return _contract_engine
