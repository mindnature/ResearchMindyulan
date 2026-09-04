from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import ResearchPipeline, load_corpus
from .providers import resolve_provider


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
        "--corpus",
        default="examples/demo_corpus.json",
        help="Path to a JSON evidence corpus",
    )
    run_parser.add_argument("--top-k", type=int, default=12, help="Maximum evidence items to keep")
    run_parser.add_argument(
        "--offline",
        action="store_true",
        help="Force deterministic provider even when LLM environment variables are configured",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        corpus_path = Path(args.corpus)
        corpus = load_corpus(corpus_path)
        provider = resolve_provider(prefer_llm=not args.offline)
        pipeline = ResearchPipeline(provider=provider)
        result = pipeline.run(
            question=args.question,
            discipline=args.discipline,
            corpus=corpus,
            top_k=args.top_k,
        )
        print(f"ResearchMind Yulan run completed: {result.run_id}")
        print(f"Evidence items: {len(result.evidence)}")
        print(f"Gap candidates: {len(result.gaps)}")
        print(f"Counter-evidence items: {len(result.counter_evidence)}")
        print(f"Method risks: {len(result.method_risks)}")
        print(f"Outputs: runs/{result.run_id}/final_report.md")
        print(f"         runs/{result.run_id}/audit_trail.json")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
