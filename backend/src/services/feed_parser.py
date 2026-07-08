import feedparser
from src.config.db import get_db

RSS_FEEDS = [
    "http://feeds.reuters.com/Reuters/worldNews",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.upstreamonline.com/rss",
]

CORRIDOR_KEYWORDS = {
    "hormuz": ["hormuz", "strait of hormuz"],
    "bab_el_mandeb": ["bab-el-mandeb", "bab el mandeb", "yemen strait"],
    "red_sea_suez": ["red sea", "suez", "suez canal"],
}
GENERAL_KEYWORDS = ["opec", "opec+", "crude oil", "oil tanker", "sanctions oil"]


def fetch_candidate_entries() -> list[dict]:
    """Fetch all configured RSS feeds, return raw entries (title, url, source, published)."""
    entries = []
    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                entries.append({
                    "url": entry.get("link", ""),
                    "title": entry.get("title", ""),
                    "source": feed_url,
                    "published_at": entry.get("published", None),
                })
        except Exception:
            # A single feed failing shouldn't kill the whole poll cycle
            continue
    return entries


def match_corridor(title: str) -> str | None:
    """Return the corridor id this headline is relevant to, or None if no match."""
    lower = title.lower()
    for corridor_id, keywords in CORRIDOR_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return corridor_id
    # General energy/geopolitical keywords without a specific corridor match
    # still count as relevant but need Gemini to assign the corridor.
    if any(kw in lower for kw in GENERAL_KEYWORDS):
        return "unassigned"
    return None


def filter_relevant(entries: list[dict]) -> list[dict]:
    relevant = []
    for e in entries:
        if not e["url"] or not e["title"]:
            continue
        corridor_guess = match_corridor(e["title"])
        if corridor_guess:
            e["corridor_guess"] = corridor_guess
            relevant.append(e)
    return relevant


def dedup_against_db(entries: list[dict]) -> list[dict]:
    """Only return entries whose URL isn't already in the headlines table."""
    db = get_db()
    if not entries:
        return []
    urls = [e["url"] for e in entries]
    existing = db.table("headlines").select("url").in_("url", urls).execute()
    existing_urls = {row["url"] for row in existing.data}
    new_entries = [e for e in entries if e["url"] not in existing_urls]
    return new_entries


def insert_headlines(entries: list[dict]) -> list[dict]:
    """Insert new headline rows, return them with their DB ids."""
    db = get_db()
    inserted = []
    for e in entries:
        row = {
            "url": e["url"],
            "title": e["title"],
            "source": e["source"],
            "processed": False,
        }
        result = db.table("headlines").insert(row).execute()
        if result.data:
            inserted.append(result.data[0])
    return inserted
