from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import ResearchPipeline, load_corpus
from .providers import resolve_provider
from .retrieval import OpenAlexClient
from .stages import map_question, plan_search
from .verification import CrossrefClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="researchmind-yulan",
        description="Run the ResearchMind Yulan competition pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run an end-to-end research decision pipeline")
    run_parser.add_argument("--question", required=True, help="Research question to analyze")
    run_parser.add_argument("--discipline", default="general", help="Discipline label")
    run_parser.add_argument(
        "--source",
        choices=["corpus", "openalex"],
        default="corpus",
        help="Evidence source: reproducible local corpus or live OpenAlex scholarly search",
    )
    run_parser.add_argument(
        "--corpus",
        default="examples/demo_corpus.json",
        help="Path to a JSON evidence corpus when --source=corpus",
    )
    run_parser.add_argument(
        "--per-query",
        type=int,
        default=6,
        help="OpenAlex results requested for each planned query",
    )
    run_parser.add_argument(
        "--semantic-openalex",
        action="store_true",
        help="Use OpenAlex semantic search instead of lexical search",
    )
    run_parser.add_argument(
        "--verify-crossref",
        action="store_true",
        help="Cross-check DOI records against Crossref before analysis",
    )
    run_parser.add_argument(
        "--crossref-limit",
        type=int,
        default=12,
        help="Maximum number of DOI records to verify with Crossref",
    )
    run_parser.add_argument("--top-k", type=int, default=12, help="Maximum evidence items to keep")
    run_parser.add_argument(
        "--offline",
        action="store_true",
        help="Force deterministic decision synthesis even when LLM environment variables are configured",
    )
    return parser


def _resolve_evidence(args) -> list:
    if args.source == "corpus":
        evidence = load_corpus(Path(args.corpus))
    else:
        mapped = map_question(args.question, args.discipline)
        queries = plan_search(mapped)
        client = OpenAlexClient.from_env()
        evidence = client.collect(
            queries,
            per_query=args.per_query,
            semantic=args.semantic_openalex,
        )
        if not evidence:
            raise RuntimeError("OpenAlex returned no evidence for the planned queries")

    if args.verify_crossref:
        evidence = CrossrefClient.from_env().verify(
            evidence,
            limit=max(1, args.crossref_limit),
        )
    return evidence


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        evidence = _resolve_evidence(args)
        provider = resolve_provider(prefer_llm=not args.offline)
        pipeline = ResearchPipeline(provider=provider)
        result = pipeline.run(
            question=args.question,
            discipline=args.discipline,
            corpus=evidence,
            top_k=args.top_k,
        )
        print(f"ResearchMind Yulan run completed: {result.run_id}")
        print(f"Evidence source: {args.source}")
        print(f"Evidence items: {len(result.evidence)}")
        print(f"Gap candidates: {len(result.gaps)}")
        print(f"Counter-evidence items: {len(result.counter_evidence)}")
        print(f"Method risks: {len(result.method_risks)}")
        print(f"Crossref verification: {'enabled' if args.verify_crossref else 'disabled'}")
        print(f"Outputs: runs/{result.run_id}/final_report.md")
        print(f"         runs/{result.run_id}/audit_trail.json")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
