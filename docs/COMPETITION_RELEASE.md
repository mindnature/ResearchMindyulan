# ResearchMind Yulan | Competition Release Guide

Status (2026-10-18): functioning competition prototype, not independently validated scientific research.

## Install and run

From repository root (Python 3.10 or newer):

~~~powershell
python -m pip install -e ".[web]"
python -m unittest discover -s tests -v
researchmind-yulan benchmark --output benchmark/results
streamlit run src/researchmind_yulan/webapp.py
~~~

The web application provides research question input, stage status, evidence board,
Claim–Evidence provenance graph, candidate research gaps, second-pass skeptical search,
method risks, and report/audit downloads.

## Reproducible offline demo

~~~powershell
researchmind-yulan run --question "How should LLM refusal boundaries be evaluated?" --discipline ai --offline
~~~

The included sample papers are synthetic. This mode proves engineering functionality,
not scholarly accuracy, scientific novelty, or model performance.

## Real scholarly retrieval with offline semantic fallback

~~~powershell
researchmind-yulan run --question "How should LLM refusal boundaries be evaluated?" --discipline ai --source openalex --per-query 4 --top-k 10 --verify-crossref --offline
~~~

Offline only disables the LLM API, not scholarly API requests.
The live source path performs topic filtering, OpenAlex discovery, optional Crossref
metadata verification, and limited prior-art searches to test candidate gaps.
All queried and rejected records are recorded for audit. Crossref validation of
a DOI or title does not prove the publication's scientific claims.

## LLM configuration: local environment only

Set your own authorized credentials through process environment variables.
Never commit secrets or paste them into the web application.

~~~powershell
$env:RM_YULAN_LLM_PROVIDER = "gemini"
$env:RM_YULAN_GEMINI_API_KEY = "<your key from a secure source>"
$env:RM_YULAN_GEMINI_MODEL = "<available model>"
researchmind-yulan run --question "How should LLM refusal boundaries be evaluated?" --discipline ai --source openalex
~~~

An OpenAI-compatible endpoint is also supported; consult .env.example.
Without credentials, semantic analysis is labeled heuristic fallback.
A real LLM provider has not yet been tested in this release with a user credential.

## Evidence quality contract

- Topic gate: conservative keywords first, optional LLM semantic relevance check.
  Precision is prioritized over recall, so some relevant papers may be missed.
- Claim–Evidence graph: model claims require an exact supporting source span.
  Missing/nonexistent quotation causes per-record heuristic fallback. This checks
  literal traceability, not scientific truth or substantive entailment.
  Current links do not provide
  full-text independent verification or causal cross-document entailment.
- Contradictions: a negative-sounding word like 'however' or 'failure' does not
  constitute counter-evidence. Genuine contradictory claims need explicit labels
  and preferably domain-expert review.
- Candidate gaps: always unverified. Finding no paper is not proof of novelty.
  Second-pass skeptic search cannot conclusively validate research gaps.
- Source grade: measures metadata traceability, not scientific validity.
- Method auditor: partially heuristic and must not be marketed as expert review.

## Research-grade benchmark still required

Prepare at least ten independent real research cases spanning AI and social science.
For each case record source gold labels, true research gaps, method risk gold labels,
and at least two independent expert reviews.
Compare B0 single-shot LLM, B1 conventional Deep Research, B2 full ResearchMind Yulan
and A1 B2 without Skeptic under equal model budgets and equal retrieval constraints.
Measure grounding precision, off-topic rate, gap validity, counter-evidence coverage,
methodological-risk recall, unsupported claim rate, blinded usefulness, cost, and latency.
Report negative as well as positive findings.

The built-in benchmark currently measures only a hand-labeled synthetic fixture;
its scores are NOT evidence of real-world performance.

## 8-minute demo outline

00:00–00:45 The scientific decision problem
00:45–01:30 Research workflow and provenance guarantees
01:30–03:15 Real or offline run: evidence board
03:15–04:30 Claim to source trace
04:30–05:50 Gap candidate and prior-art second search
05:50–06:45 Method risks and known failure modes
06:45–07:30 Test status and benchmark limitations
07:30–08:00 Final report and audit exports

For any competition, verify the official submission rules and deadlines anew.
