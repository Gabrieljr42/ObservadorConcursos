"""Explicit publication labels, independent of source and PDF content."""
import re
import unicodedata


def publication_label(title):
    text = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().casefold()
    label = re.sub(r'^\s*(?:\d+[.\s\-:]+)?(?:edital\s+de\s+)?', '', text)
    return re.sub(r'^(?:edital|comunicado)(?:\s+complementar)?\s+'
        r'(?:n[.o]*\s*)?\d+(?:[/.-]\d+)*(?:\s*[-:]+\s*|\s+)', '', label)


def individual_administrative_act(title):
    return bool(re.match(r'^(?:edital\s+de\s+)?(?:posse\b|nomeacao\b|'
                r'(?:inclusao|exclusao)\s+(?:de\s+)?candidat|'
                r'(?:deferimento|indeferimento)\b)', publication_label(title)))
