"""
OUTREACH TRACKER: Prevents duplicate spam
=========================================

Tracks who we've contacted and prevents sending duplicate DMs/emails
to the same person unless they have a genuinely new opportunity.

Rules:
- Same person + same opportunity = NEVER resend
- Same person + different opportunity = Allow if >7 days since last contact
- Same person + any opportunity = Max 2 contacts per 30 days
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Persistence
DATA_DIR = Path(__file__).parent.parent / "data"
OUTREACH_FILE = DATA_DIR / "outreach_history.json"

# Limits
SAME_OPPORTUNITY_BLOCK = True  # Never resend for same opportunity
MIN_DAYS_BETWEEN_CONTACTS = 7  # Min days before contacting same person for different opp
MAX_CONTACTS_PER_30_DAYS = 2   # Max total contacts per person in 30 day window


@dataclass
class OutreachRecord:
    """Record of a single outreach attempt"""
    recipient_id: str  # normalized: email or @twitter_handle
    recipient_type: str  # email, twitter, linkedin, reddit, github
    opportunity_id: str
    opportunity_title: str
    sent_at: str
    contract_id: Optional[str] = None
    message_id: Optional[str] = None


class OutreachTracker:
    """
    Tracks outreach history to prevent spam.
    """

    def __init__(self):
        self.history: Dict[str, List[Dict]] = {}  # recipient_id -> list of outreach records
        self._load_history()
        logger.info(f"OutreachTracker initialized with {len(self.history)} tracked recipients")

    def _load_history(self):
        """Load outreach history from persistent storage"""
        try:
            if OUTREACH_FILE.exists():
                with open(OUTREACH_FILE, 'r') as f:
                    data = json.load(f)
                    self.history = data.get('history', {})
                    logger.info(f"Loaded outreach history: {len(self.history)} recipients")
        except Exception as e:
            logger.warning(f"Could not load outreach history: {e}")
            self.history = {}

    def _save_history(self):
        """Save outreach history to persistent storage"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                'history': self.history,
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            with open(OUTREACH_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save outreach history: {e}")

    def _normalize_recipient(self, recipient: str, recipient_type: str) -> str:
        """Normalize recipient ID for consistent tracking"""
        recipient = recipient.strip().lower()

        if recipient_type == 'twitter':
            # Remove @ prefix for consistency
            return recipient.lstrip('@')
        elif recipient_type == 'email':
            return recipient
        elif recipient_type == 'reddit':
            # Remove u/ prefix
            return recipient.replace('u/', '').lstrip('/')
        elif recipient_type == 'github':
            # Remove @ prefix
            return recipient.lstrip('@')
        else:
            return recipient

    def can_contact(
        self,
        recipient: str,
        recipient_type: str,
        opportunity_id: str,
        opportunity_title: str = ""
    ) -> tuple[bool, str]:
        """
        Check if we can contact this recipient.

        Returns:
            (can_contact: bool, reason: str)
        """
        recipient_id = self._normalize_recipient(recipient, recipient_type)
        key = f"{recipient_type}:{recipient_id}"

        # Get history for this recipient
        records = self.history.get(key, [])

        if not records:
            # Never contacted - go ahead
            return True, "new_recipient"

        now = datetime.now(timezone.utc)

        # Check 1: Same opportunity - BLOCK
        for record in records:
            if record.get('opportunity_id') == opportunity_id:
                return False, f"already_contacted_for_same_opportunity"

        # Check 2: Too recent (within MIN_DAYS_BETWEEN_CONTACTS)
        recent_records = []
        for record in records:
            try:
                sent_at = datetime.fromisoformat(record['sent_at'].replace('Z', '+00:00'))
                days_ago = (now - sent_at).days
                if days_ago < MIN_DAYS_BETWEEN_CONTACTS:
                    return False, f"contacted_{days_ago}_days_ago_min_{MIN_DAYS_BETWEEN_CONTACTS}"
                if days_ago < 30:
                    recent_records.append(record)
            except:
                pass

        # Check 3: Max contacts in 30 days
        if len(recent_records) >= MAX_CONTACTS_PER_30_DAYS:
            return False, f"max_{MAX_CONTACTS_PER_30_DAYS}_contacts_in_30_days_reached"

        # All checks passed
        return True, "allowed_new_opportunity"

    def record_outreach(
        self,
        recipient: str,
        recipient_type: str,
        opportunity_id: str,
        opportunity_title: str = "",
        contract_id: str = None,
        message_id: str = None
    ):
        """Record that we contacted this recipient"""
        recipient_id = self._normalize_recipient(recipient, recipient_type)
        key = f"{recipient_type}:{recipient_id}"

        record = {
            'recipient_id': recipient_id,
            'recipient_type': recipient_type,
            'opportunity_id': opportunity_id,
            'opportunity_title': opportunity_title,
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'contract_id': contract_id,
            'message_id': message_id
        }

        if key not in self.history:
            self.history[key] = []

        self.history[key].append(record)
        self._save_history()

        logger.info(f"📝 Recorded outreach to {key} for opportunity {opportunity_id}")

    def get_recipient_history(self, recipient: str, recipient_type: str) -> List[Dict]:
        """Get outreach history for a recipient"""
        recipient_id = self._normalize_recipient(recipient, recipient_type)
        key = f"{recipient_type}:{recipient_id}"
        return self.history.get(key, [])

    def get_stats(self) -> Dict:
        """Get outreach statistics"""
        total_recipients = len(self.history)
        total_outreach = sum(len(records) for records in self.history.values())

        by_type = {}
        for key, records in self.history.items():
            rtype = key.split(':')[0]
            by_type[rtype] = by_type.get(rtype, 0) + len(records)

        return {
            'total_recipients': total_recipients,
            'total_outreach': total_outreach,
            'by_type': by_type
        }


# Singleton instance
_outreach_tracker = None


def get_outreach_tracker() -> OutreachTracker:
    """Get singleton outreach tracker instance"""
    global _outreach_tracker
    if _outreach_tracker is None:
        _outreach_tracker = OutreachTracker()
    return _outreach_tracker
