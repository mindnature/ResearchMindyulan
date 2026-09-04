from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .models import EvidenceItem, SearchQuery


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct plaintext from OpenAlex's abstract_inverted_index."""
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions.append((int(index), word))
    positions.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positions)


def _author_names(work: dict) -> list[str]:
    names: list[str] = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(str(name))
    return names


def _source_name(work: dict) -> str:
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    return str(source.get("display_name") or "")


@dataclass
class OpenAlexClient:
    """Small OpenAlex Works API client for competition-grade scholarly discovery."""

    api_key: str | None = None
    timeout: int = 30
    base_url: str = "https://api.openalex.org"

    @classmethod
    def from_env(cls) -> "OpenAlexClient":
        return cls(
            api_key=os.getenv("OPENALEX_API_KEY", "").strip() or None,
            timeout=int(os.getenv("OPENALEX_TIMEOUT", "30")),
        )

    def search(self, query: str, per_page: int = 8, semantic: bool = False) -> list[EvidenceItem]:
        per_page = max(1, min(int(per_page), 50 if semantic else 100))
        params: dict[str, str | int] = {
            "per_page": per_page,
            "select": ",".join(
                [
                    "id",
                    "doi",
                    "title",
                    "type",
                    "publication_year",
                    "language",
                    "abstract_inverted_index",
                    "authorships",
                    "primary_location",
                    "cited_by_count",
                ]
            ),
        }
        params["search.semantic" if semantic else "search"] = query
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/works?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "ResearchMindYulan/0.2 scholarly-retrieval"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenAlex retrieval failed: {exc}") from exc

        results = payload.get("results") or []
        return [self._to_evidence(work) for work in results]

    def collect(
        self,
        queries: list[SearchQuery],
        per_query: int = 6,
        semantic: bool = False,
    ) -> list[EvidenceItem]:
        merged: list[EvidenceItem] = []
        seen: set[str] = set()
        for planned in queries:
            for item in self.search(planned.query, per_page=per_query, semantic=semantic):
                key = str(item.metadata.get("doi") or item.metadata.get("openalex_id") or item.title).lower()
                if key in seen:
                    continue
                seen.add(key)
                item.metadata["retrieval_query"] = planned.query
                item.metadata["retrieval_purpose"] = planned.purpose
                merged.append(item)
        return merged

    @staticmethod
    def _to_evidence(work: dict) -> EvidenceItem:
        openalex_id = str(work.get("id") or "")
        short_id = openalex_id.rsplit("/", 1)[-1] if openalex_id else "unknown"
        doi = str(work.get("doi") or "")
        title = str(work.get("title") or "Untitled work")
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        source_name = _source_name(work)
        excerpt = abstract or f"{title}. Source metadata retrieved from OpenAlex."
        return EvidenceItem(
            evidence_id=f"OA-{short_id}",
            title=title,
            source_type=str(work.get("type") or "scholarly_work"),
            url=doi or openalex_id,
            excerpt=excerpt,
            stance="neutral",
            verified=True,
            metadata={
                "provider": "openalex",
                "openalex_id": openalex_id,
                "doi": doi,
                "publication_year": work.get("publication_year"),
                "language": work.get("language"),
                "cited_by_count": work.get("cited_by_count", 0),
                "authors": _author_names(work),
                "source": source_name,
                "source_record_verified": True,
                "claim_independently_verified": False,
            },
        )
