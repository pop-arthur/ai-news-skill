from __future__ import annotations

import email.utils
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable


USER_AGENT = "ai-news-skill/1.0 (+https://github.com/openai/codex)"
MAX_ITEMS = 10
REQUEST_TIMEOUT_SECONDS = 10

def google_news_rss_url(query: str) -> str:
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )


RSS_SOURCES = [
    {
        "name": "Google News",
        "url": google_news_rss_url(
            '("artificial intelligence" OR AI) '
            "(launch OR model OR research OR startup OR regulation OR chip OR agent) "
            "-stock -stocks -investing -investor -motley -fool when:7d"
        ),
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    },
    {
        "name": "VentureBeat via Google News",
        "url": google_news_rss_url(
            "site:venturebeat.com (artificial intelligence OR AI) when:30d"
        ),
    },
    {
        "name": "The Verge via Google News",
        "url": google_news_rss_url(
            "site:theverge.com (artificial intelligence OR AI) when:30d"
        ),
    },
    {
        "name": "Ars Technica via Google News",
        "url": google_news_rss_url(
            "site:arstechnica.com (artificial intelligence OR AI) when:30d"
        ),
    },
]


def fetch_xml(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read()


def parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def find_text(element: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return " ".join(found.text.split())
    return ""


def parse_feed(xml_bytes: bytes, source_name: str) -> list[dict[str, object]]:
    root = ET.fromstring(xml_bytes)
    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    items: list[dict[str, object]] = []
    for entry in entries:
        title = find_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"])
        link = find_text(entry, ["link", "{http://www.w3.org/2005/Atom}id"])
        if not link:
            atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href", "")

        published_text = find_text(
            entry,
            [
                "pubDate",
                "published",
                "updated",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
            ],
        )

        normalized_title = title.strip(" -")
        lower_title = normalized_title.lower()
        if (
            not normalized_title
            or not link
            or lower_title in {"the verge", "venturebeat", "ars technica"}
        ):
            continue

        items.append(
            {
                "title": normalized_title,
                "link": link,
                "source": source_name,
                "published_at": parse_date(published_text),
            }
        )
    return items


def load_items() -> tuple[list[dict[str, object]], list[str]]:
    collected: list[dict[str, object]] = []
    errors: list[str] = []

    for source in RSS_SOURCES:
        try:
            xml_bytes = fetch_xml(source["url"])
            collected.extend(parse_feed(xml_bytes, source["name"]))
        except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
            errors.append(f'{source["name"]}: {exc}')

    deduped: dict[str, dict[str, object]] = {}
    for item in collected:
        dedupe_key = str(item["link"]).strip().lower()
        if dedupe_key and dedupe_key not in deduped:
            deduped[dedupe_key] = item

    sorted_items = sorted(
        deduped.values(),
        key=lambda item: item["published_at"],
        reverse=True,
    )
    return sorted_items[:MAX_ITEMS], errors


def main() -> int:
    items, errors = load_items()

    if not items:
        print("AI News\n")
        print("No recent AI news could be fetched from public RSS sources.")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"- {error}")
        return 1

    print("AI News\n")
    for index, item in enumerate(items, start=1):
        published_at = item["published_at"]
        published_label = (
            published_at.strftime("%Y-%m-%d %H:%M UTC")
            if isinstance(published_at, datetime)
            and published_at != datetime.min.replace(tzinfo=timezone.utc)
            else "unknown date"
        )
        print(f"{index}. {item['title']}")
        print(f"   Source: {item['source']}")
        print(f"   Published: {published_label}")
        print(f"   Link: {item['link']}\n")

    if errors:
        print("Warnings:")
        for error in errors:
            print(f"- {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
