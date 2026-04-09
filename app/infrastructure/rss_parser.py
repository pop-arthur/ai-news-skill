from __future__ import annotations

import email.utils
import hashlib
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable

from app.domain.entities import Article


def parse_rss_articles(payload: bytes, source_name: str) -> list[Article]:
    """Parse RSS or Atom XML into normalized domain articles."""
    root = ET.fromstring(payload)
    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    articles: list[Article] = []
    for entry in entries:
        title = _find_text(entry, ["title", "{http://www.w3.org/2005/Atom}title"]).strip()
        description = _find_text(
            entry,
            [
                "description",
                "summary",
                "{http://www.w3.org/2005/Atom}summary",
                "{http://www.w3.org/2005/Atom}content",
            ],
        ).strip()
        url = _extract_link(entry).strip()
        published_raw = _find_text(
            entry,
            [
                "pubDate",
                "published",
                "updated",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
            ],
        )

        if not title or not url:
            continue

        articles.append(
            Article(
                id=_build_article_id(source_name, url, title),
                title=" ".join(title.split()),
                description=_clean_text(description),
                url=url,
                source=source_name,
                published_at=_parse_date(published_raw),
            )
        )

    return articles


def _build_article_id(source_name: str, url: str, title: str) -> str:
    fingerprint = f"{source_name}|{url}|{title}".encode("utf-8", errors="ignore")
    return hashlib.sha256(fingerprint).hexdigest()[:16]


def _find_text(element: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        node = element.find(name)
        if node is not None:
            if node.text:
                return node.text
            if node.attrib.get("href"):
                return node.attrib["href"]
    return ""


def _extract_link(element: ET.Element) -> str:
    """Handle both RSS text links and Atom link href attributes."""
    direct = _find_text(element, ["link", "{http://www.w3.org/2005/Atom}id"])
    if direct and direct.startswith("http"):
        return direct

    atom_link = element.find("{http://www.w3.org/2005/Atom}link")
    if atom_link is not None and atom_link.attrib.get("href"):
        return atom_link.attrib["href"]

    if direct:
        parsed = urllib.parse.urlparse(direct)
        if parsed.scheme and parsed.netloc:
            return direct
    return ""


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return datetime.min.replace(tzinfo=timezone.utc)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_text(value: str) -> str:
    """Strip feed markup so normalized descriptions stay API-friendly."""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    unescaped = html.unescape(without_tags)
    return " ".join(unescaped.split())
