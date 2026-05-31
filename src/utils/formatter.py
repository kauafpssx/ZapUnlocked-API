import datetime
import re


def format_text(text: str) -> str:
    """
    Replaces date/time placeholders in the text.

    Supported placeholders: {{day}}, {{mon}}, {{yea}}, {{hou}}, {{min}}, {{sec}}
    """
    if not text or not isinstance(text, str):
        return text

    now = datetime.datetime.now()

    mapping = {
        "day": f"{now.day:02}",
        "mon": f"{now.month:02}",
        "yea": f"{now.year:04}",
        "hou": f"{now.hour:02}",
        "min": f"{now.minute:02}",
        "sec": f"{now.second:02}",
    }

    def replacer(match):
        content = match.group(1)
        result = content
        has_replacement = False

        for key, val in mapping.items():
            if key in result:
                result = result.replace(key, val)
                has_replacement = True

        return result if has_replacement else match.group(0)

    return re.sub(r"\{\{(.*?)\}\}", replacer, text)
