"""Link filtering utilities."""

EXCLUDED_PREFIXES = frozenset([
    "Wikipedia:", "WP:", "File:", "Image:", "Category:",
    "Template:", "Help:", "Portal:", "Draft:", "Module:",
    "Talk:", "User:", "User talk:", "Special:", "Book:",
    "TimedText:", "MediaWiki:",
])


def is_valid_article(title: str) -> bool:
    if not title:
        return False
    return not any(title.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def filter_valid_links(raw_links: list[dict]) -> list[str]:
    return [
        link["title"]
        for link in raw_links
        if link.get("ns") == 0
        and link.get("title")
        and is_valid_article(link["title"])
    ]
