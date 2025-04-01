"""
Tests for the i18n module.
"""

import pytest
from py_opencommit.i18n import get_text, get_language_from_alias, load_translations

def test_get_text_default_language():
    """Test getting text with default language."""
    # This key should exist in the English translations
    assert get_text("localLanguage") == "english"
    
    # This key should fall back to the key itself if not found
    assert get_text("nonexistent_key") == "nonexistent_key"

def test_get_language_from_alias():
    """Test getting language code from aliases."""
    assert get_language_from_alias("en") == "en"
    assert get_language_from_alias("English") == "en"
    assert get_language_from_alias("english") == "en"
    assert get_language_from_alias("unknown_alias") is None

def test_load_translations():
    """Test loading translations."""
    # Load English translations
    en_translations = load_translations("en")
    assert "localLanguage" in en_translations
    assert en_translations["localLanguage"] == "english"
    
    # Loading unknown language should fall back to English
    unknown_translations = load_translations("unknown_language")
    assert "localLanguage" in unknown_translations
    assert unknown_translations["localLanguage"] == "english"
