"""
MULTI-LINGUAL OUTREACH: Localized Client Communication
======================================================

Features:
- Detect client language from opportunity/profile
- Translate outreach messages
- Format currency in local format
- Culture-aware communication patterns

Updated: Jan 2026
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class LocaleConfig:
    """Configuration for a locale"""
    code: str                # e.g., 'en-US', 'es-ES'
    language: str            # e.g., 'English', 'Spanish'
    currency_code: str       # e.g., 'USD', 'EUR'
    currency_symbol: str     # e.g., '$', '\u20ac'
    currency_position: str   # 'before' or 'after'
    decimal_separator: str   # '.' or ','
    thousands_separator: str # ',' or '.'
    greeting_style: str      # 'formal' or 'casual'
    name_order: str          # 'western' or 'eastern'


# Supported locales
LOCALES: Dict[str, LocaleConfig] = {
    'en-US': LocaleConfig(
        code='en-US', language='English', currency_code='USD',
        currency_symbol='$', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='casual', name_order='western'
    ),
    'en-GB': LocaleConfig(
        code='en-GB', language='English (UK)', currency_code='GBP',
        currency_symbol='\u00a3', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='western'
    ),
    'es-ES': LocaleConfig(
        code='es-ES', language='Spanish', currency_code='EUR',
        currency_symbol='\u20ac', currency_position='after',
        decimal_separator=',', thousands_separator='.',
        greeting_style='formal', name_order='western'
    ),
    'es-MX': LocaleConfig(
        code='es-MX', language='Spanish (Mexico)', currency_code='MXN',
        currency_symbol='$', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='casual', name_order='western'
    ),
    'pt-BR': LocaleConfig(
        code='pt-BR', language='Portuguese (Brazil)', currency_code='BRL',
        currency_symbol='R$', currency_position='before',
        decimal_separator=',', thousands_separator='.',
        greeting_style='casual', name_order='western'
    ),
    'de-DE': LocaleConfig(
        code='de-DE', language='German', currency_code='EUR',
        currency_symbol='\u20ac', currency_position='after',
        decimal_separator=',', thousands_separator='.',
        greeting_style='formal', name_order='western'
    ),
    'fr-FR': LocaleConfig(
        code='fr-FR', language='French', currency_code='EUR',
        currency_symbol='\u20ac', currency_position='after',
        decimal_separator=',', thousands_separator=' ',
        greeting_style='formal', name_order='western'
    ),
    'ja-JP': LocaleConfig(
        code='ja-JP', language='Japanese', currency_code='JPY',
        currency_symbol='\u00a5', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='eastern'
    ),
    'zh-CN': LocaleConfig(
        code='zh-CN', language='Chinese (Simplified)', currency_code='CNY',
        currency_symbol='\u00a5', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='eastern'
    ),
    'ko-KR': LocaleConfig(
        code='ko-KR', language='Korean', currency_code='KRW',
        currency_symbol='\u20a9', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='eastern'
    ),
    'ar-SA': LocaleConfig(
        code='ar-SA', language='Arabic', currency_code='SAR',
        currency_symbol='\ufdfc', currency_position='after',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='western'
    ),
    'hi-IN': LocaleConfig(
        code='hi-IN', language='Hindi', currency_code='INR',
        currency_symbol='\u20b9', currency_position='before',
        decimal_separator='.', thousands_separator=',',
        greeting_style='formal', name_order='western'
    ),
}

# Message templates by language
MESSAGE_TEMPLATES: Dict[str, Dict[str, str]] = {
    'en': {
        'greeting_formal': 'Dear {name},',
        'greeting_casual': 'Hi {name},',
        'intro': "Thank you for your interest. I'd love to help with your {service_type} project.",
        'availability': "I'm available to start immediately and can deliver initial results within {timeframe}.",
        'price_mention': "Based on your requirements, I estimate this would be around {price}.",
        'cta': "Would you like to discuss the details?",
        'closing_formal': 'Best regards,',
        'closing_casual': 'Best,',
    },
    'es': {
        'greeting_formal': 'Estimado/a {name},',
        'greeting_casual': 'Hola {name},',
        'intro': 'Gracias por su inter\u00e9s. Me encantar\u00eda ayudarle con su proyecto de {service_type}.',
        'availability': 'Estoy disponible para comenzar de inmediato y puedo entregar resultados iniciales en {timeframe}.',
        'price_mention': 'Seg\u00fan sus requisitos, estimo que esto costar\u00eda aproximadamente {price}.',
        'cta': '\u00bfLe gustar\u00eda discutir los detalles?',
        'closing_formal': 'Atentamente,',
        'closing_casual': 'Saludos,',
    },
    'pt': {
        'greeting_formal': 'Prezado(a) {name},',
        'greeting_casual': 'Ol\u00e1 {name},',
        'intro': 'Obrigado pelo seu interesse. Adoraria ajudar com seu projeto de {service_type}.',
        'availability': 'Estou dispon\u00edvel para come\u00e7ar imediatamente e posso entregar resultados iniciais em {timeframe}.',
        'price_mention': 'Com base nos seus requisitos, estimo que isso custaria aproximadamente {price}.',
        'cta': 'Gostaria de discutir os detalhes?',
        'closing_formal': 'Atenciosamente,',
        'closing_casual': 'Abra\u00e7os,',
    },
    'de': {
        'greeting_formal': 'Sehr geehrte(r) {name},',
        'greeting_casual': 'Hallo {name},',
        'intro': 'Vielen Dank f\u00fcr Ihr Interesse. Ich w\u00fcrde Ihnen gerne bei Ihrem {service_type}-Projekt helfen.',
        'availability': 'Ich kann sofort beginnen und erste Ergebnisse innerhalb von {timeframe} liefern.',
        'price_mention': 'Basierend auf Ihren Anforderungen sch\u00e4tze ich die Kosten auf etwa {price}.',
        'cta': 'M\u00f6chten Sie die Details besprechen?',
        'closing_formal': 'Mit freundlichen Gr\u00fc\u00dfen,',
        'closing_casual': 'Viele Gr\u00fc\u00dfe,',
    },
    'fr': {
        'greeting_formal': 'Cher/Ch\u00e8re {name},',
        'greeting_casual': 'Bonjour {name},',
        'intro': "Merci pour votre int\u00e9r\u00eat. Je serais ravi(e) de vous aider avec votre projet de {service_type}.",
        'availability': "Je suis disponible pour commencer imm\u00e9diatement et peux livrer des r\u00e9sultats initiaux dans {timeframe}.",
        'price_mention': "En fonction de vos besoins, j'estime que cela co\u00fbterait environ {price}.",
        'cta': 'Souhaitez-vous en discuter les d\u00e9tails?',
        'closing_formal': 'Cordialement,',
        'closing_casual': 'Bien \u00e0 vous,',
    },
    'ja': {
        'greeting_formal': '{name}\u69d8',
        'greeting_casual': '{name}\u3055\u3093\u3001',
        'intro': '\u304a\u554f\u3044\u5408\u308f\u305b\u3044\u305f\u3060\u304d\u3042\u308a\u304c\u3068\u3046\u3054\u3056\u3044\u307e\u3059\u3002{service_type}\u306e\u30d7\u30ed\u30b8\u30a7\u30af\u30c8\u3092\u304a\u624b\u4f1d\u3044\u3055\u305b\u3066\u3044\u305f\u3060\u3051\u308c\u3070\u5e78\u3044\u3067\u3059\u3002',
        'availability': '\u3059\u3050\u306b\u958b\u59cb\u3067\u304d\u3001{timeframe}\u4ee5\u5185\u306b\u6700\u521d\u306e\u6210\u679c\u7269\u3092\u304a\u5c4a\u3051\u3067\u304d\u307e\u3059\u3002',
        'price_mention': '\u3054\u8981\u4ef6\u306b\u57fa\u3065\u304d\u3001\u304a\u898b\u7a4d\u308a\u306f\u7d04{price}\u3068\u306a\u308a\u307e\u3059\u3002',
        'cta': '\u8a73\u7d30\u306b\u3064\u3044\u3066\u3054\u76f8\u8ac7\u3044\u305f\u3060\u3051\u307e\u3059\u3067\u3057\u3087\u3046\u304b\uff1f',
        'closing_formal': '\u3088\u308d\u3057\u304f\u304a\u9858\u3044\u3044\u305f\u3057\u307e\u3059\u3002',
        'closing_casual': '\u3088\u308d\u3057\u304f\u304a\u9858\u3044\u3057\u307e\u3059\u3002',
    },
    'zh': {
        'greeting_formal': '\u5c0a\u656c\u7684{name}\uff0c',
        'greeting_casual': '{name}\u60a8\u597d\uff0c',
        'intro': '\u611f\u8c22\u60a8\u7684\u5173\u6ce8\u3002\u6211\u5f88\u4e50\u610f\u5e2e\u52a9\u60a8\u5b8c\u6210{service_type}\u9879\u76ee\u3002',
        'availability': '\u6211\u53ef\u4ee5\u7acb\u5373\u5f00\u59cb\uff0c\u5e76\u5728{timeframe}\u5185\u4ea4\u4ed8\u521d\u6b65\u6210\u679c\u3002',
        'price_mention': '\u6839\u636e\u60a8\u7684\u9700\u6c42\uff0c\u6211\u4f30\u8ba1\u8d39\u7528\u7ea6\u4e3a{price}\u3002',
        'cta': '\u60a8\u613f\u610f\u8ba8\u8bba\u8be6\u60c5\u5417\uff1f',
        'closing_formal': '\u6b64\u81f4\u656c\u793c\uff0c',
        'closing_casual': '\u7965\u597d\uff0c',
    },
}

# Service type translations
SERVICE_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'web_dev': {
        'en': 'web development',
        'es': 'desarrollo web',
        'pt': 'desenvolvimento web',
        'de': 'Webentwicklung',
        'fr': 'd\u00e9veloppement web',
        'ja': '\u30a6\u30a7\u30d6\u958b\u767a',
        'zh': '\u7f51\u7ad9\u5f00\u53d1',
    },
    'mobile_dev': {
        'en': 'mobile app development',
        'es': 'desarrollo de aplicaciones m\u00f3viles',
        'pt': 'desenvolvimento de aplicativos m\u00f3veis',
        'de': 'Mobile App-Entwicklung',
        'fr': 'd\u00e9veloppement d\'applications mobiles',
        'ja': '\u30e2\u30d0\u30a4\u30eb\u30a2\u30d7\u30ea\u958b\u767a',
        'zh': '\u79fb\u52a8\u5e94\u7528\u5f00\u53d1',
    },
    'design': {
        'en': 'design',
        'es': 'dise\u00f1o',
        'pt': 'design',
        'de': 'Design',
        'fr': 'design',
        'ja': '\u30c7\u30b6\u30a4\u30f3',
        'zh': '\u8bbe\u8ba1',
    },
    'content': {
        'en': 'content creation',
        'es': 'creaci\u00f3n de contenido',
        'pt': 'cria\u00e7\u00e3o de conte\u00fado',
        'de': 'Content-Erstellung',
        'fr': 'cr\u00e9ation de contenu',
        'ja': '\u30b3\u30f3\u30c6\u30f3\u30c4\u4f5c\u6210',
        'zh': '\u5185\u5bb9\u521b\u4f5c',
    },
    'devops': {
        'en': 'DevOps',
        'es': 'DevOps',
        'pt': 'DevOps',
        'de': 'DevOps',
        'fr': 'DevOps',
        'ja': 'DevOps',
        'zh': 'DevOps',
    },
}

# Exchange rates (would be fetched from API in production)
EXCHANGE_RATES: Dict[str, float] = {
    'USD': 1.0,
    'EUR': 0.92,
    'GBP': 0.79,
    'JPY': 149.50,
    'CNY': 7.24,
    'BRL': 4.97,
    'MXN': 17.15,
    'INR': 83.12,
    'KRW': 1320.0,
    'SAR': 3.75,
}


class MultilingualOutreach:
    """
    Handle multi-lingual client communication.

    Flow:
    1. Detect client locale from opportunity data
    2. Select appropriate templates
    3. Format currency in local format
    4. Generate localized message
    """

    def __init__(self):
        self.locales = LOCALES
        self.templates = MESSAGE_TEMPLATES
        self.service_translations = SERVICE_TRANSLATIONS
        self.exchange_rates = EXCHANGE_RATES
        self.stats = {
            'messages_generated': 0,
            'by_language': {},
            'currencies_converted': 0,
        }

    def detect_locale(
        self,
        opportunity: Dict[str, Any],
    ) -> LocaleConfig:
        """
        Detect client locale from opportunity data.

        Checks:
        1. Explicit locale field
        2. Platform region
        3. Language in description
        4. Currency mentioned
        5. Default to en-US
        """
        # Check explicit locale
        locale_code = opportunity.get('locale') or opportunity.get('language')
        if locale_code and locale_code in self.locales:
            return self.locales[locale_code]

        # Check platform region
        platform = opportunity.get('platform', '').lower()
        region_map = {
            'upwork_latam': 'es-MX',
            'upwork_europe': 'en-GB',
            'fiverr_de': 'de-DE',
            'freelancer_br': 'pt-BR',
        }
        if platform in region_map:
            return self.locales[region_map[platform]]

        # Check for language indicators in text
        text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()

        language_indicators = {
            'es-ES': ['espa\u00f1ol', 'castellano', 'hola', 'gracias', '\u20ac'],
            'pt-BR': ['portugu\u00eas', 'brasileiro', 'obrigado', 'r$'],
            'de-DE': ['deutsch', 'german', 'danke', 'bitte'],
            'fr-FR': ['fran\u00e7ais', 'french', 'merci', 'bonjour'],
            'ja-JP': ['\u65e5\u672c\u8a9e', '\u3042\u308a\u304c\u3068\u3046', '\u00a5'],
            'zh-CN': ['\u4e2d\u6587', '\u8c22\u8c22', '\u4eba\u6c11\u5e01'],
        }

        for locale_code, indicators in language_indicators.items():
            if any(ind in text for ind in indicators):
                return self.locales[locale_code]

        # Check currency mentions
        currency_locale_map = {
            '\u00a3': 'en-GB',
            '\u20ac': 'de-DE',
            'r$': 'pt-BR',
            '\u00a5': 'ja-JP',
            '\u20b9': 'hi-IN',
        }
        for currency, locale_code in currency_locale_map.items():
            if currency in text:
                return self.locales[locale_code]

        # Default to en-US
        return self.locales['en-US']

    def format_currency(
        self,
        amount_usd: float,
        locale: LocaleConfig,
        convert: bool = True,
    ) -> str:
        """
        Format currency for locale.

        Args:
            amount_usd: Amount in USD
            locale: Target locale
            convert: Whether to convert to local currency

        Returns:
            Formatted currency string
        """
        if convert:
            rate = self.exchange_rates.get(locale.currency_code, 1.0)
            amount = amount_usd * rate
            self.stats['currencies_converted'] += 1
        else:
            amount = amount_usd

        # Format number
        if locale.decimal_separator == ',':
            formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', locale.thousands_separator)
        else:
            formatted = f"{amount:,.2f}".replace(',', locale.thousands_separator)

        # Add currency symbol
        if locale.currency_position == 'before':
            return f"{locale.currency_symbol}{formatted}"
        else:
            return f"{formatted} {locale.currency_symbol}"

    def get_language_code(self, locale: LocaleConfig) -> str:
        """Get base language code from locale"""
        return locale.code.split('-')[0]

    def translate_service_type(
        self,
        service_type: str,
        locale: LocaleConfig,
    ) -> str:
        """Translate service type to locale language"""
        lang = self.get_language_code(locale)
        translations = self.service_translations.get(service_type, {})
        return translations.get(lang, translations.get('en', service_type))

    def generate_outreach_message(
        self,
        opportunity: Dict[str, Any],
        service_type: str,
        price_usd: float,
        timeframe: str = "24-48 hours",
        sender_name: str = "Aigentsy",
        locale: LocaleConfig = None,
    ) -> Dict[str, Any]:
        """
        Generate localized outreach message.

        Args:
            opportunity: Opportunity data
            service_type: Type of service
            price_usd: Price in USD
            timeframe: Delivery timeframe
            sender_name: Sender name
            locale: Override locale (auto-detect if None)

        Returns:
            Dict with message and metadata
        """
        # Detect locale if not provided
        if locale is None:
            locale = self.detect_locale(opportunity)

        lang = self.get_language_code(locale)
        templates = self.templates.get(lang, self.templates['en'])

        # Get client name
        client_name = opportunity.get('client_name') or opportunity.get('poster', 'there')
        if locale.name_order == 'eastern':
            # For Eastern names, might need to reverse if given in Western order
            pass

        # Select greeting style
        greeting_key = f"greeting_{locale.greeting_style}"
        greeting = templates.get(greeting_key, templates['greeting_casual'])

        closing_key = f"closing_{locale.greeting_style}"
        closing = templates.get(closing_key, templates['closing_casual'])

        # Format components
        formatted_price = self.format_currency(price_usd, locale)
        localized_service = self.translate_service_type(service_type, locale)

        # Build message
        message_parts = [
            greeting.format(name=client_name),
            '',
            templates['intro'].format(service_type=localized_service),
            '',
            templates['availability'].format(timeframe=timeframe),
            '',
            templates['price_mention'].format(price=formatted_price),
            '',
            templates['cta'],
            '',
            closing,
            sender_name,
        ]

        message = '\n'.join(message_parts)

        # Update stats
        self.stats['messages_generated'] += 1
        lang_stats = self.stats['by_language'].setdefault(lang, 0)
        self.stats['by_language'][lang] = lang_stats + 1

        logger.info(f"Generated outreach message in {locale.language}")

        return {
            'message': message,
            'locale': locale.code,
            'language': locale.language,
            'currency_code': locale.currency_code,
            'price_local': formatted_price,
            'price_usd': price_usd,
            'service_type_localized': localized_service,
        }

    def get_supported_locales(self) -> List[Dict[str, str]]:
        """Get list of supported locales"""
        return [
            {
                'code': locale.code,
                'language': locale.language,
                'currency': locale.currency_code,
            }
            for locale in self.locales.values()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get outreach stats"""
        return {
            **self.stats,
            'supported_locales': len(self.locales),
            'supported_languages': len(set(l.code.split('-')[0] for l in self.locales.values())),
        }


# Singleton
_multilingual_outreach: Optional[MultilingualOutreach] = None


def get_multilingual_outreach() -> MultilingualOutreach:
    """Get or create multilingual outreach instance"""
    global _multilingual_outreach
    if _multilingual_outreach is None:
        _multilingual_outreach = MultilingualOutreach()
    return _multilingual_outreach
