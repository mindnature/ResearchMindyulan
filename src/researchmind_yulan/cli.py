"""Competition CLI: reproducible corpus and real-world scholarly retrieval."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .pipeline import ResearchPipeline, load_corpus
from .planning import plan_queries
from .providers import DeterministicProvider, resolve_provider
from .quality import filter_retrieval, llm_relevance_filter
from .retrieval import OpenAlexClient
from .stages import map_question
from .verification import CrossrefClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researchmind-yulan",
        description="Auditable research decision agent: real sources, structured claims and skeptical retrieval.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Generate a reproducible research decision run")
    run.add_argument("--question", required=True)
    run.add_argument("--discipline", default="general")
    run.add_argument("--source", choices=["corpus", "openalex"], default="corpus")
    run.add_argument("--corpus", default="examples/demo_corpus.json")
    run.add_argument("--per-query", type=int, default=5)
    run.add_argument("--semantic-openalex", action="store_true")
    run.add_argument("--verify-crossref", action="store_true")
    run.add_argument("--crossref-limit", type=int, default=10)
    run.add_argument("--top-k", type=int, default=12)
    run.add_argument("--offline", action="store_true", help="Force deterministic fixture-safe analysis")
    run.add_argument("--no-topic-gate", action="store_true", help="For debugging only")
    run.add_argument("--topic-threshold", type=float, default=0.24)
    run.add_argument("--skip-skeptic", action="store_true", help="Disable second-pass prior-art retrieval")
    bench = subparsers.add_parser("benchmark", help="Run labeled fixture relevance benchmark")
    bench.add_argument("--output", default="benchmark/results")
    return parser


def _resolve_evidence(args, provider):
    mapped = map_question(args.question, args.discipline)
    queries = plan_queries(mapped, provider)
    rejected = []
    client = None
    if args.source == "corpus":
        evidence = load_corpus(Path(args.corpus))
    else:
        client = OpenAlexClient.from_env()
        evidence = client.collect(
            queries,
            per_query=max(1, args.per_query),
            semantic=args.semantic_openalex,
        )
        if not args.no_topic_gate:
            evidence, rejected = filter_retrieval(
                args.question, evidence, threshold=args.topic_threshold
            )
        if evidence and not isinstance(provider, DeterministicProvider):
            evidence, llm_rejected = llm_relevance_filter(args.question, evidence, provider)
            rejected.extend(llm_rejected)
        if not evidence:
            raise RuntimeError(
                "No topical OpenAlex records survived the relevance gate; "
                "try a more specific question or --topic-threshold 0.15"
            )
    # Verify accepted records only, to avoid spending Crossref calls on noise.
    if args.verify_crossref:
        evidence = CrossrefClient.from_env().verify(
            evidence, limit=max(1, args.crossref_limit)
        )
    return evidence, queries, rejected, client


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "benchmark":
        from .benchmark import run_fixture_benchmark
        result = run_fixture_benchmark(Path(args.output))
        print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
        print(f"Benchmark artifacts: {args.output}")
        return 0

    provider = resolve_provider(prefer_llm=not args.offline)
    evidence, queries, rejected, client = _resolve_evidence(args, provider)
    pipeline = ResearchPipeline(
        provider=provider,
        counter_search_client=client if client and not args.skip_skeptic else None,
    )
    result = pipeline.run(
        question=args.question,
        discipline=args.discipline,
        corpus=evidence,
        top_k=args.top_k,
        queries=queries,
        rejected_evidence=rejected,
    )
    modes = Counter(item.extraction_mode for item in result.evidence_analysis)
    print(f"ResearchMind Yulan run completed: {result.run_id}")
    print(f"Provider mode: {'offline / heuristic' if isinstance(provider, DeterministicProvider) else type(provider).__name__}")
    print(f"Evidence source: {args.source}")
    print(f"Topic-gate rejections: {len(rejected)}")
    print(f"Evidence items: {len(result.evidence)}")
    print(f"Evidence extraction: {dict(modes)}")
    print(f"Claim nodes: {len(result.claim_graph.claims)}")
    print(f"Claim-evidence links: {len(result.claim_graph.links)}")
    print(f"Gap candidates (unverified): {len(result.gaps)}")
    print(f"Explicit counter-evidence: {len(result.counter_evidence)}")
    print(f"Skeptic retrieval queries: {len(result.skeptic_traces)}")
    print(f"Method risks: {len(result.method_risks)}")
    print(f"Crossref metadata verification: {'enabled' if args.verify_crossref else 'disabled'}")
    print(f"Outputs: runs/{result.run_id}/final_report.md")
    print(f"         runs/{result.run_id}/audit_trail.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
