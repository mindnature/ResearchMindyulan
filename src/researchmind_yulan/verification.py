from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher

from .models import EvidenceItem


def normalize_doi(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def normalize_title(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def title_similarity(left: str, right: str) -> float:
    a = normalize_title(left)
    b = normalize_title(right)
    if not a or not b:
        return 0.0
    return round(SequenceMatcher(None, a, b).ratio(), 3)


@dataclass
class CrossrefClient:
    mailto: str | None = None
    timeout: int = 20
    base_url: str = "https://api.crossref.org"

    @classmethod
    def from_env(cls) -> "CrossrefClient":
        return cls(
            mailto=os.getenv("CROSSREF_MAILTO", "").strip() or None,
            timeout=int(os.getenv("CROSSREF_TIMEOUT", "20")),
        )

    def fetch_doi(self, doi: str) -> dict | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None
        encoded = urllib.parse.quote(normalized, safe="")
        url = f"{self.base_url}/works/{encoded}"
        if self.mailto:
            url = f"{url}?{urllib.parse.urlencode({'mailto': self.mailto})}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ResearchMindYulan/0.2 evidence-verifier"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"Crossref verification failed with HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Crossref verification failed: {exc}") from exc
        return payload.get("message") or None

    def verify(self, items: list[EvidenceItem], limit: int = 12) -> list[EvidenceItem]:
        checked = 0
        for item in items:
            doi = str(item.metadata.get("doi") or item.url or "")
            normalized = normalize_doi(doi)
            if not normalized or not normalized.startswith("10."):
                item.metadata["crossref_checked"] = False
                continue
            if checked >= limit:
                item.metadata["crossref_checked"] = False
                item.metadata["crossref_skip_reason"] = "verification_limit"
                continue

            record = self.fetch_doi(normalized)
            checked += 1
            item.metadata["crossref_checked"] = True
            item.metadata["crossref_record_verified"] = record is not None
            if record is None:
                item.metadata["crossref_title_similarity"] = 0.0
                continue

            crossref_titles = record.get("title") or []
            crossref_title = str(crossref_titles[0]) if crossref_titles else ""
            similarity = title_similarity(item.title, crossref_title)
            item.metadata["crossref_title"] = crossref_title
            item.metadata["crossref_title_similarity"] = similarity
            item.metadata["crossref_title_match"] = similarity >= 0.85
            item.metadata["doi_normalized"] = normalized
        return items
