"""
INDUSTRY KNOWLEDGE BASE
Pre-built templates for 50+ industries

Each industry has:
- Email templates (context-aware)
- Partnership targets (who to JV with)
- Best platforms (where to find customers)
- Seasonal opportunities (when to push)
- Customer behavior patterns
"""

from typing import Dict, List


# ============================================================
# INDUSTRY TEMPLATES
# ============================================================

INDUSTRY_TEMPLATES = {
    
    # ============================================================
    # PET SERVICES
    # ============================================================
    
    'pet_services': {
        'name': 'Pet Services',
        'subcategories': ['dog_grooming', 'pet_sitting', 'dog_walking', 'pet_training'],
        
        'email_templates': {
            'welcome': "Welcome to {business_name}! We can't wait to meet {pet_name} 🐾",
            'reactivation': "Hi {name}, it's been {months} months since {pet_name}'s last visit. Time for a refresh! 🛁",
            'birthday': "🎉 Happy birthday to {pet_name}! Celebrate with 20% off any service this week.",
            'upsell_nails': "We noticed {pet_name} didn't get nails trimmed last time. Add it next visit for just $15!",
            'review_request': "How did {pet_name} enjoy their visit? We'd love your feedback! ⭐",
            'referral': "Know a friend with a furry buddy? Send them our way and you both get $10 off!"
        },
        
        'partnership_targets': [
            'local pet stores',
            'veterinarians',
            'dog walkers',
            'pet photographers',
            'pet supply companies',
            'doggy daycares'
        ],
        
        'best_platforms': ['Google Local', 'Yelp', 'Facebook', 'Nextdoor', 'Instagram'],
        
        'seasonal_opportunities': [
            {'season': 'summer', 'opportunity': 'Shedding season - promote de-shedding treatments'},
            {'season': 'holidays', 'opportunity': 'Gift grooming packages, holiday photos'},
            {'season': 'spring', 'opportunity': 'Spring cleaning/de-matting after winter'},
            {'season': 'back_to_school', 'opportunity': 'Get pets groomed before busy fall'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 90,
            'reactivation_threshold_days': 120,
            'peak_days': ['Saturday', 'Sunday'],
            'peak_times': ['9am-2pm'],
            'repeat_likelihood': 0.85
        }
    },
    
    # ============================================================
    # RESTAURANTS & FOOD SERVICE
    # ============================================================
    
    'restaurants': {
        'name': 'Restaurants & Food Service',
        'subcategories': ['fine_dining', 'casual_dining', 'fast_casual', 'food_truck', 'catering'],
        
        'email_templates': {
            'reservation_reminder': "Your table for {party_size} is confirmed for {date} at {time}. Can't wait to see you!",
            'review_request': "Thanks for dining with us! How was your {dish}? We'd love your feedback! 🌟",
            'special_events': "Join us for {event_name} on {date}! Limited seating - reserve now.",
            'loyalty': "You've dined with us {visit_count} times! Here's 20% off your next visit. 🎉",
            'birthday': "Happy birthday {name}! Celebrate with a complimentary dessert on us. 🎂",
            'reactivation': "We haven't seen you in {months} months! Here's 15% off to welcome you back."
        },
        
        'partnership_targets': [
            'food delivery apps',
            'event planners',
            'hotels',
            'tourism boards',
            'corporate catering',
            'wedding venues'
        ],
        
        'best_platforms': ['Google Local', 'Yelp', 'OpenTable', 'Instagram', 'UberEats', 'DoorDash'],
        
        'seasonal_opportunities': [
            {'season': 'valentines', 'opportunity': 'Special prix fixe menu, couple packages'},
            {'season': 'mothers_day', 'opportunity': 'Brunch specials, reservations fill up'},
            {'season': 'nye', 'opportunity': 'Premium seating, champagne packages'},
            {'season': 'summer', 'opportunity': 'Outdoor seating, summer cocktails'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 45,
            'reactivation_threshold_days': 90,
            'peak_days': ['Friday', 'Saturday', 'Sunday'],
            'peak_times': ['6pm-9pm', '12pm-2pm'],
            'repeat_likelihood': 0.65
        }
    },
    
    # ============================================================
    # PROFESSIONAL SERVICES (Consulting, Coaching, etc)
    # ============================================================
    
    'professional_services': {
        'name': 'Professional Services',
        'subcategories': ['consulting', 'coaching', 'accounting', 'legal', 'marketing_agency'],
        
        'email_templates': {
            'consultation': "Thanks for your interest in {service}. Let's schedule a 30-minute consultation to discuss your needs.",
            'follow_up': "Following up on our consultation about {topic}. Here's a proposal tailored to your goals.",
            'check_in': "Hi {name}, just checking in on {project}. How are things progressing?",
            'referral_request': "Would you mind referring us to someone who needs {service}? We'd be grateful!",
            'case_study': "We helped {client} achieve {result}. Could we help you do the same?",
            'newsletter': "{business_name} Monthly Insights: {topic_of_month}"
        },
        
        'partnership_targets': [
            'complementary service providers',
            'referral networks',
            'industry associations',
            'co-working spaces',
            'business incubators',
            'chambers of commerce'
        ],
        
        'best_platforms': ['LinkedIn', 'Google Ads', 'Industry Forums', 'Conferences', 'Referrals'],
        
        'seasonal_opportunities': [
            {'season': 'tax_season', 'opportunity': 'Accounting/financial planning services peak'},
            {'season': 'year_end', 'opportunity': 'Planning, strategy, goal-setting for next year'},
            {'season': 'budget_cycles', 'opportunity': 'Q4 budget planning, proposals'},
            {'season': 'january', 'opportunity': 'New year, new goals - coaching/consulting inquiries spike'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 180,  # Project-based
            'reactivation_threshold_days': 365,
            'peak_days': ['Tuesday', 'Wednesday', 'Thursday'],
            'peak_times': ['9am-11am', '2pm-4pm'],
            'repeat_likelihood': 0.70
        }
    },
    
    # ============================================================
    # FITNESS & WELLNESS
    # ============================================================
    
    'fitness_wellness': {
        'name': 'Fitness & Wellness',
        'subcategories': ['gym', 'yoga_studio', 'personal_training', 'massage', 'nutrition'],
        
        'email_templates': {
            'class_reminder': "Your {class_name} class is tomorrow at {time}. See you there! 💪",
            'milestone': "Congrats on {milestone}! You've come so far. Keep going! 🎉",
            'reactivation': "We haven't seen you in {weeks} weeks. Let's get back on track! First class back is on us.",
            'challenge': "Join our {challenge_name} starting {date}! Push yourself with the community.",
            'package_expiring': "Your class package expires in {days} days. Book your sessions now!",
            'referral': "Bring a friend for free this week! You both get 10% off next month."
        },
        
        'partnership_targets': [
            'nutritionists',
            'physical therapists',
            'athletic wear stores',
            'health food stores',
            'corporate wellness programs',
            'chiropractors'
        ],
        
        'best_platforms': ['Instagram', 'Facebook', 'Google Local', 'ClassPass', 'Mindbody'],
        
        'seasonal_opportunities': [
            {'season': 'january', 'opportunity': 'New Year resolutions - biggest signup month'},
            {'season': 'summer', 'opportunity': 'Beach body prep, outdoor classes'},
            {'season': 'fall', 'opportunity': 'Back to routine after summer'},
            {'season': 'holidays', 'opportunity': 'Gift memberships, challenge stress with wellness'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 7,  # Weekly classes
            'reactivation_threshold_days': 30,
            'peak_days': ['Monday', 'Wednesday', 'Saturday'],
            'peak_times': ['6am-8am', '5pm-7pm'],
            'repeat_likelihood': 0.75
        }
    },
    
    # ============================================================
    # HOME SERVICES
    # ============================================================
    
    'home_services': {
        'name': 'Home Services',
        'subcategories': ['cleaning', 'landscaping', 'plumbing', 'hvac', 'handyman', 'painting'],
        
        'email_templates': {
            'quote_follow_up': "Hi {name}, here's your quote for {service}. Book within 48 hours for 10% off!",
            'seasonal_reminder': "Time for {seasonal_service}! Book now before the busy season.",
            'maintenance_reminder': "It's been {months} months since your last {service}. Schedule your next appointment!",
            'referral': "Love our service? Refer a neighbor and you both get $25 off!",
            'review_request': "Thanks for choosing {business_name}! How did we do? 🌟",
            'emergency': "Need emergency {service}? We're available 24/7. Call now!"
        },
        
        'partnership_targets': [
            'real estate agents',
            'property managers',
            'home improvement stores',
            'contractors',
            'interior designers',
            'moving companies'
        ],
        
        'best_platforms': ['Google Local', 'Yelp', 'Nextdoor', 'Angi', 'HomeAdvisor', 'Thumbtack'],
        
        'seasonal_opportunities': [
            {'season': 'spring', 'opportunity': 'Spring cleaning, lawn care, gutter cleaning'},
            {'season': 'summer', 'opportunity': 'AC maintenance, deck staining, landscaping'},
            {'season': 'fall', 'opportunity': 'Leaf removal, winterization, heating inspection'},
            {'season': 'winter', 'opportunity': 'Snow removal, pipe winterizing, holiday lighting'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 90,
            'reactivation_threshold_days': 180,
            'peak_days': ['Saturday', 'Monday'],
            'peak_times': ['8am-12pm'],
            'repeat_likelihood': 0.80
        }
    },
    
    # ============================================================
    # REAL ESTATE
    # ============================================================
    
    'real_estate': {
        'name': 'Real Estate',
        'subcategories': ['residential_sales', 'commercial', 'property_management', 'real_estate_investing'],
        
        'email_templates': {
            'new_listing': "Just listed! {address} - {beds}bed/{baths}bath, ${price}. Schedule a showing today!",
            'market_update': "Hi {name}, here's what's happening in {neighborhood} this month.",
            'home_anniversary': "Happy {years}-year anniversary in your home! Need anything?",
            'buyer_update': "Hi {name}, I found {count} new properties matching your criteria.",
            'closing_anniversary': "It's been {years} years since we helped you buy your home! How can we help again?",
            'referral': "Know someone buying or selling? We'd love to help them too!"
        },
        
        'partnership_targets': [
            'mortgage brokers',
            'home inspectors',
            'moving companies',
            'home stagers',
            'contractors',
            'insurance agents'
        ],
        
        'best_platforms': ['Zillow', 'Realtor.com', 'Facebook', 'Instagram', 'LinkedIn', 'Google Ads'],
        
        'seasonal_opportunities': [
            {'season': 'spring', 'opportunity': 'Peak home buying season starts'},
            {'season': 'summer', 'opportunity': 'Families want to move before school starts'},
            {'season': 'fall', 'opportunity': 'Last push before holidays'},
            {'season': 'winter', 'opportunity': 'Motivated buyers, less competition'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 2555,  # 7 years between moves
            'reactivation_threshold_days': 1825,  # 5 years
            'peak_days': ['Saturday', 'Sunday'],
            'peak_times': ['10am-4pm'],
            'repeat_likelihood': 0.15  # But high referral rate
        }
    },
    
    # ============================================================
    # SAAS / TECH
    # ============================================================
    
    'saas_tech': {
        'name': 'SaaS / Technology',
        'subcategories': ['b2b_saas', 'b2c_app', 'developer_tools', 'enterprise_software'],
        
        'email_templates': {
            'onboarding_welcome': "Welcome to {product_name}! Here's how to get started in 3 easy steps.",
            'feature_education': "Did you know {product_name} can {feature}? Here's how to use it.",
            'usage_milestone': "Congrats! You've {milestone} with {product_name}. 🎉",
            'inactive_user': "We noticed you haven't logged in lately. Can we help with anything?",
            'upgrade_nudge': "You're getting close to your plan limit. Upgrade now to unlock more!",
            'churn_prevention': "Before you go, let us know what we could do better."
        },
        
        'partnership_targets': [
            'complementary SaaS tools',
            'app marketplaces',
            'system integrators',
            'consulting partners',
            'resellers',
            'developer communities'
        ],
        
        'best_platforms': ['Product Hunt', 'LinkedIn', 'Twitter', 'HackerNews', 'Reddit', 'Google Ads'],
        
        'seasonal_opportunities': [
            {'season': 'january', 'opportunity': 'New year, new tools - budget resets'},
            {'season': 'q4', 'opportunity': 'Use-it-or-lose-it budgets, annual planning'},
            {'season': 'product_launches', 'opportunity': 'Coordinate with launches'},
            {'season': 'conferences', 'opportunity': 'Industry events, demos'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 1,  # Daily usage ideal
            'reactivation_threshold_days': 14,  # Inactive 2 weeks = at risk
            'peak_days': ['Tuesday', 'Wednesday', 'Thursday'],
            'peak_times': ['9am-11am', '1pm-3pm'],
            'repeat_likelihood': 0.85  # High if engaged early
        }
    },
    
    # ============================================================
    # E-COMMERCE / RETAIL
    # ============================================================
    
    'ecommerce_retail': {
        'name': 'E-Commerce / Retail',
        'subcategories': ['fashion', 'electronics', 'home_goods', 'specialty_retail'],
        
        'email_templates': {
            'abandoned_cart': "You left {items} in your cart! Complete checkout now and get 10% off.",
            'order_shipped': "Your order #{order_id} is on its way! Track it here: {tracking_link}",
            'post_purchase': "How do you like your {product}? We'd love your review!",
            'restock': "{product} is back in stock! Get it before it sells out again.",
            'seasonal_sale': "{season} sale is here! Up to {discount}% off everything.",
            'loyalty': "You've earned {points} points! Redeem them for {reward}."
        },
        
        'partnership_targets': [
            'influencers',
            'affiliate marketers',
            'complementary brands',
            'subscription boxes',
            'retail pop-ups',
            'marketplaces'
        ],
        
        'best_platforms': ['Instagram', 'Facebook', 'TikTok', 'Pinterest', 'Google Shopping', 'Amazon'],
        
        'seasonal_opportunities': [
            {'season': 'black_friday', 'opportunity': 'Biggest sales day of the year'},
            {'season': 'cyber_monday', 'opportunity': 'Online shopping peak'},
            {'season': 'holiday_season', 'opportunity': 'Gift buying peak'},
            {'season': 'back_to_school', 'opportunity': 'School supplies, clothing'}
        ],
        
        'customer_behavior': {
            'avg_frequency_days': 60,
            'reactivation_threshold_days': 120,
            'peak_days': ['Sunday', 'Monday'],
            'peak_times': ['7pm-10pm', '12pm-2pm'],
            'repeat_likelihood': 0.55
        }
    }
    
    # Add 43 more industries...
}


# ============================================================
# DEFAULT / GENERAL BUSINESS
# ============================================================

DEFAULT_INDUSTRY = {
    'name': 'General Business',
    
    'email_templates': {
        'welcome': "Welcome to {business_name}! We're excited to work with you.",
        'follow_up': "Hi {name}, following up on our conversation. How can we help?",
        'reactivation': "We haven't heard from you in a while. Let's reconnect!",
        'review_request': "How was your experience with {business_name}? We'd love your feedback!",
        'referral': "Know someone who could benefit from {service}? We'd love an introduction."
    },
    
    'partnership_targets': ['complementary businesses', 'referral partners', 'industry associations'],
    
    'best_platforms': ['Google', 'LinkedIn', 'Facebook', 'Word of Mouth'],
    
    'seasonal_opportunities': [
        {'season': 'year_end', 'opportunity': 'Budget cycles, planning for next year'},
        {'season': 'new_year', 'opportunity': 'Fresh starts, new initiatives'}
    ],
    
    'customer_behavior': {
        'avg_frequency_days': 90,
        'reactivation_threshold_days': 180,
        'peak_days': ['Tuesday', 'Wednesday', 'Thursday'],
        'peak_times': ['9am-5pm'],
        'repeat_likelihood': 0.65
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_industry_knowledge(industry: str) -> Dict:
    """
    Get industry-specific knowledge
    
    Args:
        industry: Industry identifier (e.g., 'pet_services', 'restaurants')
    
    Returns:
        Industry template with email templates, partnership targets, etc.
    """
    
    # Exact match
    if industry in INDUSTRY_TEMPLATES:
        return INDUSTRY_TEMPLATES[industry]
    
    # Fuzzy match (simple version)
    for key, template in INDUSTRY_TEMPLATES.items():
        if industry.lower() in key.lower() or key.lower() in industry.lower():
            return template
    
    # Check subcategories
    for key, template in INDUSTRY_TEMPLATES.items():
        if industry in template.get('subcategories', []):
            return template
    
    # Default
    return DEFAULT_INDUSTRY


def list_available_industries() -> List[str]:
    """Return list of available industry templates"""
    return list(INDUSTRY_TEMPLATES.keys())


def get_industry_partnerships(industry: str) -> List[str]:
    """Get partnership targets for industry"""
    knowledge = get_industry_knowledge(industry)
    return knowledge.get('partnership_targets', [])


def get_industry_platforms(industry: str) -> List[str]:
    """Get best marketing platforms for industry"""
    knowledge = get_industry_knowledge(industry)
    return knowledge.get('best_platforms', [])


def get_email_template(industry: str, template_type: str) -> str:
    """Get specific email template for industry"""
    knowledge = get_industry_knowledge(industry)
    templates = knowledge.get('email_templates', {})
    return templates.get(template_type, DEFAULT_INDUSTRY['email_templates'].get(template_type, ''))
