"""ResearchMind Yulan competition demo: streamlit run src/researchmind_yulan/webapp.py."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

from researchmind_yulan.cli import _resolve_evidence
from researchmind_yulan.pipeline import ResearchPipeline
from researchmind_yulan.providers import DeterministicProvider, resolve_provider

st.set_page_config(page_title="ResearchMind Yulan | Research Decision Intelligence", page_icon="🔬", layout="wide")

st.title("ResearchMind Yulan")
st.caption("Deep Research → Evidence Audit → Candidate Gaps → Skeptical Search → Research Decision")
st.info(
    "研究支持工具，而非自动发现新理论。DOI验证只核验文献元数据，"
    "候选研究空白和反证必须人工复核。"
)
with st.sidebar:
    st.header("Run configuration")
    question = st.text_area(
        "Research question",
        value="How should LLM refusal boundaries be evaluated?",
        height=120,
    )
    discipline = st.selectbox("Discipline", ["ai", "economics", "ecology", "general"])
    mode = st.radio("Source", ["offline fixture", "live OpenAlex"], index=0)
    use_llm = st.checkbox("Enable configured LLM API", value=False,
                          help="Requires environment variables; never enter API keys in this page.")
    verify = st.checkbox("Crossref metadata check", value=False)
    skeptic = st.checkbox("Second-pass skeptic search", value=True,
                          disabled=mode != "live OpenAlex")
    per_query = st.slider("Works per query", 2, 8, 4)
    top_k = st.slider("Main evidence cap", 5, 20, 10)
    run_button = st.button("Run research agent", type="primary", width="stretch")

if run_button:
    if not question.strip():
        st.error("Enter a research question.")
        st.stop()
    provider = resolve_provider(prefer_llm=use_llm)
    args = SimpleNamespace(
        question=question.strip(), discipline=discipline,
        source="openalex" if mode == "live OpenAlex" else "corpus",
        corpus="examples/demo_corpus.json",
        per_query=per_query, semantic_openalex=False,
        no_topic_gate=False, topic_threshold=0.24,
        verify_crossref=verify, crossref_limit=top_k,
    )
    try:
        with st.spinner("Searching literature and auditing claims…"):
            evidence, queries, rejected, client = _resolve_evidence(args, provider)
            pipeline = ResearchPipeline(
                provider=provider,
                counter_search_client=client if skeptic else None,
            )
            result = pipeline.run(
                question=question, discipline=discipline, corpus=evidence,
                top_k=top_k, queries=queries, rejected_evidence=rejected,
            )
        st.session_state["result"] = result
        st.session_state["run_dir"] = str(pipeline.runs_dir / result.run_id)
        st.session_state["mode"] = mode
        st.session_state["provider"] = type(provider).__name__
    except Exception as exc:
        st.error(f"Run failed: {type(exc).__name__}: {str(exc)[:600]}")

result = st.session_state.get("result")
if result is None:
    st.write("Select **offline fixture** for a reliable demo, or **live OpenAlex** for real scholarly metadata.")
    st.write("Use the form on the left to start a full reproducible run.")
    st.stop()

st.caption(f"Run: {result.run_id} | {st.session_state.get('mode')} | {st.session_state.get('provider')}")
if st.session_state.get("mode") == "offline fixture":
    st.warning("OFFLINE FIXTURE: synthetic papers. This demonstrates engineering, NOT scientific findings.")
elif st.session_state.get("provider") == "DeterministicProvider":
    st.warning("Real bibliography, heuristic semantic analysis: no configured LLM API was used.")

cols = st.columns(5)
for col, (label, value) in zip(cols, [
    ("Source records", len(result.evidence)),
    ("Claim nodes", len(result.claim_graph.claims)),
    ("Gap candidates", len(result.gaps)),
    ("Counter-search queries", len(result.skeptic_traces)),
    ("Excluded papers", len(result.rejected_evidence)),
]):
    col.metric(label, value)

overview, sources, graph, skepticism, audit = st.tabs(
    ["Overview", "Evidence board", "Claim graph", "Skeptic & Gaps", "Audit & exports"]
)

with overview:
    st.subheader("Research workflow")
    stages = list(result.stage_status.items())
    st.dataframe([{"Stage": name, "Status": status} for name, status in stages],
                 width="stretch", hide_index=True)
    st.subheader("Research decision memo")
    st.markdown(result.decision_summary)
    st.caption("An offline fallback returns a diagnostic statement rather than a scientific synthesis.")

with sources:
    st.subheader("Retrieved sources")
    rows = []
    for item in result.evidence:
        rows.append({
            "Evidence": item.evidence_id, "Title": item.title,
            "Year": item.metadata.get("publication_year", ""),
            "DOI": item.metadata.get("doi", ""),
            "Provenance": item.metadata.get("provenance_grade", ""),
            "Topical score": item.metadata.get("topic_relevance", {}).get("score", item.relevance),
            "Extraction": item.metadata.get("semantic_extraction_mode", ""),
        })
    st.dataframe(rows, width="stretch", hide_index=True)
    for item in result.evidence:
        with st.expander(f"{item.evidence_id} — {item.title[:95]}"):
            if item.url.startswith("http"):
                st.link_button("Open scholarly record", item.url)
            st.write(item.excerpt)
            st.json(item.metadata)

with graph:
    st.subheader("Claim–Evidence relations")
    st.caption("Each edge links a claim to its cited paper record. An edge is an extraction label, not independent verification.")
    links = {link.claim_id: link for link in result.claim_graph.links}
    limit = min(16, len(result.claim_graph.claims))
    dot = ["digraph claims {", 'rankdir=LR;', 'node [fontname="Arial", fontsize=10];']
    for node in result.claim_graph.claims[:limit]:
        link = links.get(node.claim_id)
        if not link:
            continue
        def clean(s):
            return str(s).replace("\\", "").replace('"', "'").replace("\n", " ")[:76]
        dot.append(f'"{clean(node.claim_id)}" [shape=box, label="{clean(node.claim_id)}: {clean(node.text)}"];')
        dot.append(f'"{clean(link.evidence_id)}" [shape=ellipse];')
        dot.append(f'"{clean(node.claim_id)}" -> "{clean(link.evidence_id)}" [label="{clean(link.relation)}"];')
    dot.append("}")
    if limit:
        st.graphviz_chart("\n".join(dot), width="stretch")
    st.dataframe([
        {"Claim": node.claim_id, "Text": node.text,
         "Evidence": links[node.claim_id].evidence_id if node.claim_id in links else "",
         "Relation": links[node.claim_id].relation if node.claim_id in links else ""}
        for node in result.claim_graph.claims
    ], width="stretch", hide_index=True)

with skepticism:
    st.subheader("Candidate research gaps (not validated novelty)")
    for gap in result.gaps:
        st.markdown(f"**{gap.gap_type}** — {gap.statement}")
        st.caption(f"Evidence IDs: {', '.join(gap.supporting_evidence_ids)} | Status: {gap.verification_status}")
    st.subheader("Second-pass prior-art search")
    if result.skeptic_traces:
        st.dataframe(result.skeptic_traces, width="stretch", hide_index=True)
    else:
        st.write("Not run. Offline tests do not call external search APIs.")
    st.subheader("Explicitly classified counter-evidence")
    if result.counter_evidence:
        st.write("; ".join(e.evidence_id for e in result.counter_evidence))
    else:
        st.write("None established from the available source records. This does not mean there are no counterexamples.")

with audit:
    st.subheader("Evidence provenance, methodological risks, and run exports")
    st.dataframe([asdict(risk) for risk in result.method_risks],
                 width="stretch", hide_index=True)
    st.subheader("Rejected sources")
    st.dataframe(result.rejected_evidence, width="stretch", hide_index=True)
    run_dir = Path(st.session_state["run_dir"])
    report_file = run_dir / "final_report.md"
    audit_file = run_dir / "audit_trail.json"
    if report_file.exists():
        st.download_button("Download Decision Report", report_file.read_text(encoding="utf-8"),
                           file_name="final_report.md", mime="text/markdown")
    if audit_file.exists():
        st.download_button("Download Audit Trail", audit_file.read_text(encoding="utf-8"),
                           file_name="audit_trail.json", mime="application/json")
    st.caption(f"Full structured stage artifacts saved to {run_dir}.")
