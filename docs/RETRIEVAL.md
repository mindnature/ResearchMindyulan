# Scholarly Retrieval & Evidence Verification

ResearchMind Yulan separates three different questions:

1. **Was a source record actually retrieved?**
2. **Can its bibliographic identity be cross-checked?**
3. **Does the paper scientifically support the claim we want to make?**

These are deliberately not collapsed into one `trusted/untrusted` flag.

## OpenAlex discovery

The live retrieval path uses the OpenAlex Works API.

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --source openalex \
  --per-query 6 \
  --offline
```

Optional semantic retrieval:

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --source openalex \
  --semantic-openalex \
  --offline
```

OpenAlex returns an `abstract_inverted_index`; ResearchMind Yulan reconstructs readable abstract text locally before placing it into the Evidence Registry.

Official references:

- https://help.openalex.org/api/
- https://help.openalex.org/api/searching/
- https://help.openalex.org/data/works/attributes/

## Crossref DOI verification

A retrieved OpenAlex work can optionally be checked against the Crossref Works API:

```bash
researchmind-yulan run \
  --question "How should LLM refusal boundaries be evaluated?" \
  --discipline ai \
  --source openalex \
  --verify-crossref \
  --crossref-limit 12 \
  --offline
```

The verifier records:

- whether a DOI was available;
- whether Crossref returned a record for that DOI;
- the title returned by Crossref;
- normalized title similarity;
- whether the title match passes the current 0.85 threshold.

Crossref verification confirms bibliographic identity. It does **not** prove that a paper is correct or that a proposed research gap is valid.

Official references:

- https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/

## Provenance grades

The Evidence Registry currently assigns a provenance grade:

| Grade | Meaning |
|---|---|
| `A_crossref_confirmed` | Provider record exists, DOI exists, Crossref record exists, title matches |
| `B_provider_confirmed_with_doi` | Provider record exists and DOI exists, but Crossref has not confirmed it |
| `C_provider_confirmed` | Provider record exists without a usable DOI |
| `D_unverified_or_fixture` | Synthetic fixture or unverified input |

These grades describe **source-record traceability only**. They are not journal rankings, evidence-quality grades, causal-validity judgments, or truth scores.

## Competition rationale

This design creates an auditable separation between:

```text
retrieval
→ bibliographic verification
→ evidence extraction
→ claim support
→ research-gap validation
→ research decision
```

That separation is central to ResearchMind Yulan's competition claim: Deep Research should expose where its confidence comes from instead of hiding retrieval, interpretation, and judgment inside one generated report.
