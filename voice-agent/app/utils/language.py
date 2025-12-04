"""Language detection utilities."""
import re


def detect_language(text: str) -> str:
    """Detect if text is primarily Arabic or English.

    Args:
        text: Input text to analyze

    Returns:
        'ar' if Arabic, 'en' otherwise
    """
    if not text:
        return "en"

    # Count Arabic characters (Unicode range)
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    arabic_chars = len(''.join(arabic_pattern.findall(text)))
    total_chars = len(re.sub(r'\s+', '', text))

    if total_chars == 0:
        return "en"

    # If more than 30% Arabic characters, consider it Arabic
    arabic_ratio = arabic_chars / total_chars
    return "ar" if arabic_ratio > 0.3 else "en"


def get_greeting(language: str) -> str:
    """Get a greeting in the specified language."""
    if language == "ar":
        return "مرحبا! أنا مساعدك الصوتي. كيف يمكنني مساعدتك اليوم؟"
    return "Hello! I'm your voice assistant. How can I help you today?"


def get_error_message(language: str, error_type: str = "general") -> str:
    """Get an error message in the specified language."""
    messages = {
        "en": {
            "general": "I'm sorry, something went wrong. Please try again.",
            "not_found": "I couldn't find that information.",
            "connection": "I'm having trouble connecting to the system.",
        },
        "ar": {
            "general": "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.",
            "not_found": "لم أتمكن من العثور على هذه المعلومات.",
            "connection": "أواجه مشكلة في الاتصال بالنظام.",
        }
    }
    return messages.get(language, messages["en"]).get(error_type, messages[language]["general"])
