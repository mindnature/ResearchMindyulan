# ResearchMind Yulan Architecture

## 1. Architecture Goal

ResearchMind Yulan is a research-decision-oriented Deep Research Agent.

Its output should not be only a report. The system must preserve the decision path that produced the report.

```text
USER RESEARCH QUESTION
        │
        ▼
[1] Question Mapper
        │
        ▼
[2] Search Planner ───────────────┐
        │                         │
        ▼                         │
[3] Evidence Scout               │
        │                         │
        ▼                         │
[4] Evidence Registry            │
        │                         │
        ├──────────────┐          │
        ▼              ▼          │
[5] Literature     [6] Conflict   │
    Matrix             Scanner    │
        │              │          │
        └──────┬───────┘          │
               ▼                  │
        [7] Gap Detector          │
               │                  │
               ▼                  │
        [8] Skeptic Agent ────────┘
               │   iterative search
               ▼
        [9] Method Auditor
               │
               ▼
       [10] Research Advisor
        ├─ DOMAIN_BASELINE
        ├─ SCHOLAR_LENS
        └─ TRANSFER_INFERENCE
               │
               ▼
       [11] Decision Synthesizer
               │
               ▼
       [12] Evidence Audit Trail
               │
               ▼
       RESEARCH DECISION REPORT
```

## 2. Design Principles

### Evidence before advice
No major research recommendation should be emitted without an evidence object or an explicit uncertainty label.

### Separate observation from inference
The system must distinguish:

- source fact;
- model extraction;
- cross-source synthesis;
- methodological inference;
- recommendation.

### Counter-search before conclusion
A candidate gap or conclusion must trigger at least one targeted attempt to disconfirm it.

### Domain baseline before scholar lens
Scholar-derived heuristics cannot override established domain methodology.

### Graceful degradation
If evidence is insufficient, the system should reduce confidence rather than fabricate completeness.

## 3. Core Data Objects

### ResearchQuestion

```json
{
  "topic": "",
  "research_question": "",
  "population_or_context": "",
  "candidate_mechanisms": [],
  "candidate_outcomes": [],
  "constraints": [],
  "scope": "",
  "discipline": "",
  "uncertainties": []
}
```

### EvidenceItem

```json
{
  "evidence_id": "E001",
  "title": "",
  "source_url": "",
  "source_type": "paper|official|dataset|report|archive|other",
  "publication_date": "",
  "authors": [],
  "claim": "",
  "quote_or_locator": "",
  "retrieved_at": "",
  "credibility_grade": "A|B|C|D",
  "verification_status": "verified|partial|unverified",
  "supports": [],
  "contradicts": []
}
```

### LiteratureMatrixRow

```json
{
  "paper_id": "P001",
  "question": "",
  "theory": "",
  "data": "",
  "sample": "",
  "method": "",
  "identification": "",
  "main_findings": [],
  "limitations": [],
  "conflicts_with": [],
  "evidence_ids": []
}
```

### GapCandidate

```json
{
  "gap_id": "G001",
  "gap_type": "theory|data|method|context|time",
  "claim": "",
  "supporting_evidence": [],
  "counter_evidence": [],
  "searches_used_to_falsify": [],
  "status": "supported|weak|rejected|needs_more_evidence",
  "confidence": 0.0,
  "researchability": 0.0,
  "novelty": 0.0
}
```

### MethodAudit

```json
{
  "proposed_method": "",
  "question_method_fit": "",
  "critical_assumptions": [],
  "identification_risks": [],
  "data_risks": [],
  "validity_risks": [],
  "leakage_or_contamination_risks": [],
  "recommended_tests": [],
  "blocking_issues": []
}
```

### AdvisorRecommendation

```json
{
  "recommendation_id": "R001",
  "layer": "DOMAIN_BASELINE|SCHOLAR_LENS|TRANSFER_INFERENCE",
  "recommendation": "",
  "rationale": "",
  "evidence_ids": [],
  "assumptions": [],
  "failure_conditions": [],
  "next_test": "",
  "confidence": 0.0
}
```

## 4. Agent Responsibilities

### Question Mapper

Input: natural-language topic/question.

Output:

- structured question;
- ambiguity list;
- scope;
- candidate mechanism map;
- search dimensions.

It must not invent a precise causal design when the user has not supplied enough evidence.

### Search Planner

Creates search tasks across:

- foundational literature;
- recent literature;
- contradictory findings;
- methods literature;
- datasets;
- relevant benchmarks;
- replication / criticism where available.

### Evidence Scout

Retrieves candidate sources and converts them into EvidenceItem records.

Retrieval is modular. The MVP should allow adapters for:

- web search;
- Crossref / OpenAlex / Semantic Scholar or equivalent;
- user-provided PDFs;
- local corpus.

### Literature Matrix

Converts selected literature into comparable structured rows.

The output is not prose-first. Prose synthesis is downstream.

### Conflict Scanner

Detects:

- direct result conflicts;
- methodological disagreements;
- incompatible definitions;
- sample/context differences;
- temporal shifts;
- theory-measure mismatch.

### Gap Detector

Generates five gap families, but it is prohibited from treating “few papers found” as sufficient evidence of a research gap.

Every candidate gap enters falsification.

### Skeptic Agent

For each important claim, asks:

```text
What evidence would make this false?
What alternative explanation fits the same evidence?
Is the apparent gap only a search failure?
Does a different terminology already cover this question?
Is the result context-specific?
```

Then launches targeted counter-search tasks.

### Method Auditor

The first MVP should implement discipline-aware checklists rather than pretend to support every methodology equally.

Priority domains for the competition demo:

1. AI / computer science research;
2. economics / management empirical research.

### Research Advisor

Reuses ResearchMind concepts:

- Domain Baseline;
- Scholar Lens;
- Transfer Inference;
- evidence grading;
- scholar specificity;
- adaptive routing.

The advisor is downstream of evidence synthesis. It cannot independently overwrite source-grounded results.

### Decision Synthesizer

Produces a concise decision package:

- what is established;
- what is disputed;
- strongest gap candidates;
- rejected gap candidates;
- key methodological risks;
- recommended next experiments/searches;
- stop/continue criteria;
- research roadmap.

## 5. Iterative Loop

The main loop should be explicit and bounded.

```text
initial search
→ evidence synthesis
→ candidate gaps/claims
→ skeptic detects weak point
→ targeted search
→ update evidence graph
→ recompute gap status
→ stop when budget / evidence criterion reached
```

Suggested stop conditions:

- maximum loop count;
- search budget exhausted;
- no new high-value evidence in N searches;
- major claims all have supporting and counter-evidence checks;
- user-specified time/token budget.

## 6. Evidence Audit Trail

Every final claim should be addressable by a stable ID.

Example:

```text
Claim C07: "Most current evaluations use static benchmarks."

Derived from:
E012, E018, E026

Counter-search:
S019, S020

Counter-evidence:
E031

Final status:
PARTIALLY_SUPPORTED

Confidence:
0.72

Reason:
Static benchmarks dominate the sampled literature, but two recent dynamic evaluation frameworks weaken the absolute claim.
```

This object is central to the competition story.

## 7. MVP Technical Layout

```text
src/
├─ agents/
│  ├─ question_mapper.py
│  ├─ evidence_scout.py
│  ├─ gap_detector.py
│  ├─ skeptic.py
│  ├─ method_auditor.py
│  └─ research_advisor.py
├─ pipeline/
│  ├─ orchestrator.py
│  ├─ state.py
│  └─ stopping.py
├─ retrieval/
│  ├─ base.py
│  ├─ web.py
│  └─ local.py
├─ models/
│  ├─ evidence.py
│  ├─ literature.py
│  ├─ gap.py
│  └─ recommendation.py
└─ evaluation/
   ├─ grounding.py
   ├─ gap_validity.py
   ├─ traceability.py
   └─ decision_usefulness.py
```

## 8. Minimal Interface

CLI first:

```bash
python -m researchmind_yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --mode competition-demo
```

Expected artifacts:

```text
runs/<run_id>/
├─ question.json
├─ search_plan.json
├─ evidence_registry.jsonl
├─ literature_matrix.csv
├─ gaps.json
├─ method_audit.json
├─ advisor.json
├─ audit_trail.json
└─ final_report.md
```

A lightweight Web UI can be added only after this pipeline is stable.
