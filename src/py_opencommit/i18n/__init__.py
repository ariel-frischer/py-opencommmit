"""
Internationalization (i18n) module for OpenCommit CLI.
"""

import json
import os
from typing import Any, Dict, List, Optional

# Default language
DEFAULT_LANGUAGE = "en"

# Path to the translations directory
TRANSLATIONS_DIR = os.path.dirname(os.path.abspath(__file__))

# Dictionary to store loaded translations
_translations: Dict[str, Dict[str, str]] = {}

# List of supported languages
supported_languages = [
    "en",       # English
    "cs",       # Czech
    "de",       # German
    "es_ES",    # Spanish
    "fr",       # French
    "id_ID",    # Bahasa Indonesia
    "it",       # Italian
    "ja",       # Japanese
    "ko",       # Korean
    "nl",       # Dutch
    "pl",       # Polish
    "pt_br",    # Portuguese (Brazil)
    "ru",       # Russian
    "sv",       # Swedish
    "th",       # Thai
    "tr",       # Turkish
    "vi_VN",    # Vietnamese
    "zh_CN",    # Chinese (Simplified)
    "zh_TW",    # Chinese (Traditional)
]

# Language aliases for easier selection
language_aliases = {
    "en": ["en", "English", "english"],
    "cs": ["cs", "Czech", "česky"],
    "de": ["de", "German", "Deutsch"],
    "es_ES": ["es_ES", "Spanish", "español"],
    "fr": ["fr", "French", "française"],
    "id_ID": ["id_ID", "Bahasa", "bahasa"],
    "it": ["it", "Italian", "italiano"],
    "ja": ["ja", "Japanese", "にほんご"],
    "ko": ["ko", "Korean", "한국어"],
    "nl": ["nl", "Dutch", "Nederlands"],
    "pl": ["pl", "Polish", "Polski"],
    "pt_br": ["pt_br", "Portuguese", "português"],
    "ru": ["ru", "Russian", "русский"],
    "sv": ["sv", "Swedish", "Svenska"],
    "th": ["th", "Thai", "ไทย"],
    "tr": ["tr", "Turkish", "Turkish"],
    "vi_VN": ["vi_VN", "Vietnamese", "tiếng Việt"],
    "zh_CN": ["zh_CN", "简体中文", "中文", "简体"],
    "zh_TW": ["zh_TW", "繁體中文", "繁體"],
}


def get_language_from_alias(alias: str) -> Optional[str]:
    """
    Get language code from an alias.
    
    Args:
        alias: The alias to look up
        
    Returns:
        The language code if found, None otherwise
    """
    for lang, aliases in language_aliases.items():
        if alias in aliases:
            return lang
    return None


def load_translations(language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """
    Load translations for a specific language.
    
    Args:
        language: Language code to load translations for
        
    Returns:
        Dictionary of translations
    """
    # Return cached translations if already loaded
    if language in _translations:
        return _translations[language]
    
    # First, ensure we have the default (English) translations loaded
    if DEFAULT_LANGUAGE not in _translations:
        try:
            default_path = os.path.join(TRANSLATIONS_DIR, f"{DEFAULT_LANGUAGE}.json")
            with open(default_path, 'r', encoding='utf-8') as f:
                _translations[DEFAULT_LANGUAGE] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If we can't load the default translations, use an empty dict
            _translations[DEFAULT_LANGUAGE] = {}
    
    # If requesting the default language, just return it
    if language == DEFAULT_LANGUAGE:
        return _translations[DEFAULT_LANGUAGE]
    
    # Try to load the requested language
    try:
        lang_path = os.path.join(TRANSLATIONS_DIR, f"{language}.json")
        with open(lang_path, 'r', encoding='utf-8') as f:
            _translations[language] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If language file doesn't exist or is invalid, use only the default translations
        _translations[language] = {}
    
    # Return a combination of language-specific translations with English fallbacks
    return {**_translations[DEFAULT_LANGUAGE], **_translations[language]}


def get_text(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Get a translated text by key.
    
    Args:
        key: Translation key
        language: Language code
        
    Returns:
        Translated text, falls back to key if not found
    """
    translations = load_translations(language)
    return translations.get(key, key)


# Initialize by loading the default translations
load_translations()