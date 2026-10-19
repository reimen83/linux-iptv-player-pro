ADULT_KEYWORDS = [
    "adulto",
    "adults",
    "18+",
    "+18",
    "xxx",
    "erotico",
    "erotica",
    "for adult",
    "porn",
    "redlight",
]


def _normalize_text(value):
    text = str(value or "").lower()
    return " ".join(text.replace("-", " ").replace("_", " ").replace(".", " ").split())


def is_adult_category(category_name):
    """Verifica se a categoria se enquadra em conteúdo adulto."""
    text = _normalize_text(category_name)
    return any(keyword in text for keyword in ADULT_KEYWORDS)
