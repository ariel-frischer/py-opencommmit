import json
import os
from pathlib import Path

# Global variable to store translations
_translations = {}
_current_language = "en"


def load_translations(language="en"):
    """
    Load translations for the specified language.
    """
    global _translations, _current_language
    
    if language in _translations:
        _current_language = language
        return _translations[language]
    
    try:
        # Get the directory where this file is located
        i18n_dir = Path(__file__).parent
        
        # Construct the path to the language file
        lang_file = i18n_dir / f"{language}.json"
        
        # If the language file doesn't exist, fall back to English
        if not lang_file.exists() and language != "en":
            print(f"Language file for '{language}' not found, falling back to English.")
            return load_translations("en")
        
        # Load the language file
        with open(lang_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translations[language] = translations
            _current_language = language
            return translations
    except Exception as e:
        print(f"Error loading translations: {str(e)}")
        # Return an empty dict as fallback
        return {}


def get_text(key, language=None):
    """
    Get the translated text for the specified key.
    If language is not specified, use the current language.
    """
    if language is None:
        # Use environment variable if set, otherwise use current language
        language = os.environ.get("PYOC_LANGUAGE", _current_language)
    
    # Load translations if not already loaded
    if language not in _translations:
        load_translations(language)
    
    # Get the translation
    translation = _translations.get(language, {})
    
    # Return the translated text or the key itself if not found
    return translation.get(key, key)


def get_language_from_alias(alias):
    """
    Get the language code from an alias.
    """
    alias_map = {
        "en": "en",
        "english": "en",
        "eng": "en",
        "es": "es",
        "spanish": "es",
        "español": "es",
        "espanol": "es",
        # Add more aliases as needed
    }
    
    return alias_map.get(alias.lower(), None)
