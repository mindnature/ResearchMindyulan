"""A bounded search planner: model-assisted when configured, deterministic otherwise."""
from __future__ import annotations

import json
from .models import ResearchQuestion, SearchQuery
from .providers import DeterministicProvider, LLMProvider
from .quality import focus_terms, tokens


def _fallback(question: ResearchQuestion) -> list[SearchQuery]:
    focus = focus_terms(question.raw)
    general = tokens(question.raw)
    context = "LLM" if "llm" in general or "llms" in general else ""
    base = " ".join([context, *focus[:5]]).strip() or question.raw.strip()
    return [
        SearchQuery(base, "core literature"),
        SearchQuery(f"{base} benchmark measurement", "empirical evidence"),
        SearchQuery(f"{base} limitations counterexample", "critical evidence"),
        SearchQuery(f"{base} systematic review", "coverage validation"),
    ]


def plan_queries(question: ResearchQuestion, provider: LLMProvider | None = None) -> list[SearchQuery]:
    fallback = _fallback(question)
    if provider is None or isinstance(provider, DeterministicProvider):
        return fallback
    system = (
        "You plan scientific literature searches. Return ONLY a JSON object with "
        "queries: [{query: a concise 2-8 term scholarly keyword search, purpose: text}]. "
        "Avoid search operators, URLs, boolean wildcards and invented paper titles. "
        "Use exact technical terminology; include one adverse/contrasting search."
    )
    prompt = f"Discipline: {question.discipline}\nResearch question: {question.raw}\nReturn 3 or 4 keyword queries."
    try:
        raw = provider.complete(system, prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(raw)
        rows = data.get("queries") if isinstance(data, dict) else None
        queries = []
        if isinstance(rows, list):
            for row in rows[:4]:
                if not isinstance(row, dict):
                    continue
                value = " ".join(str(row.get("query") or "").replace("?", " ").replace("*", " ").split())
                if 8 <= len(value) <= 140 and len(value.split()) <= 12:
                    queries.append(SearchQuery(value, str(row.get("purpose") or "scholarly retrieval")[:80]))
        if len(queries) >= 3 and len({q.query.lower() for q in queries}) == len(queries):
            return queries
    except (ValueError, TypeError, AttributeError):
        pass
    except Exception:
        pass
    return fallback
