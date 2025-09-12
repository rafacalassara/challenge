from typing import List


def scrape_page(url: str, selectors: List[str]) -> dict:
    """Scrape content from a page (stub)."""
    return {"url": url, "data": {sel: f"content for {sel}" for sel in selectors}}
