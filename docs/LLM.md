# LLM integration

ResearchMind Yulan uses an LLM as a semantic reasoning component, not as the source of scholarly truth.

The deterministic parts of the system continue to own retrieval, DOI verification, provenance grading, evidence IDs, artifact persistence, audit trails, and benchmark bookkeeping. The LLM is currently used for evidence extraction and final decision synthesis.

## Supported providers

### Native Gemini

```bash
export RM_YULAN_LLM_PROVIDER=gemini
export RM_YULAN_GEMINI_API_KEY="..."
export RM_YULAN_GEMINI_MODEL="<a model available to your Gemini API account>"
```

`GEMINI_API_KEY` is also accepted as an alias for `RM_YULAN_GEMINI_API_KEY`.

The implementation calls Google's native `generateContent` REST API.

### OpenAI-compatible Chat Completions

```bash
export RM_YULAN_LLM_PROVIDER=openai_compatible
export RM_YULAN_LLM_ENDPOINT="https://api.openai.com/v1/chat/completions"
export RM_YULAN_LLM_API_KEY="..."
export RM_YULAN_LLM_MODEL="<model>"
```

The same adapter can be used with other services that implement the compatible request and response shape.

### Automatic selection

```bash
export RM_YULAN_LLM_PROVIDER=auto
```

In auto mode, ResearchMind Yulan first checks for complete Gemini configuration, then for complete OpenAI-compatible configuration, otherwise it falls back to deterministic mode.

## Semantic evidence extraction

For every retained evidence record, the Evidence Extractor requests a constrained JSON object containing:

- source research question;
- method;
- sample/population;
- data/dataset;
- main finding;
- explicit limitations;
- boundary conditions;
- up to three atomic claims;
- each claim's relation to the user's research question;
- extraction confidence.

Allowed claim relations are:

- `supporting`
- `contradicting`
- `boundary`
- `neutral`

The confidence field means confidence that the supplied source text supports the extraction. It does **not** mean that the scientific claim is true.

## Failure behavior

The system does not fail the whole research run when one model response is malformed or one LLM request fails. That evidence item is downgraded to heuristic extraction and records `extraction_mode=heuristic`.

This is deliberate competition-demo behavior: semantic quality can degrade, but provenance, source records, and auditable pipeline artifacts remain available.

## Offline mode

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --source corpus \
  --offline
```

Offline mode never requires an external LLM. It is intended for CI, reproducible benchmark fixtures, and competition-stage network failure fallback.

## Live research example

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --source openalex \
  --semantic-openalex \
  --verify-crossref
```

With an LLM configured, the output run directory now includes:

```text
stages/
├─ 01_question_mapper.json
├─ 02_search_planner.json
├─ 03_evidence_registry.json
├─ 04_evidence_analysis.json
├─ 05_claim_evidence_graph.json
├─ 06_literature_matrix.json
├─ 07_gap_detector.json
├─ 08_counter_evidence.json
├─ 09_method_audit.json
└─ 10_stage_status.json
```

The Claim–Evidence Graph is currently a provenance-preserving bipartite graph: atomic claim nodes are connected to the evidence record from which they were extracted. Cross-source semantic claim clustering is a later milestone and should not be implied by the current implementation.
