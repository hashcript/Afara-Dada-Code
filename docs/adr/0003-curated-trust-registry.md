---
blueprint:
  type: adr
  id: adr_0003-curated-trust-registry
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "data/femtech_programs.py — static curated registry of 5 organizations with verification_source fields"
    - "finding_agent/agent.py:20-26 — 'Do NOT search the open web. Only use the trusted tool.'"
    - "Naive_Agent/agent.py:1-12 — docstring: demonstrates 'the current friction donors face' with unverified open-web results"
  guesses:
    - "No refresh or external verification process exists in code; how the registry stays trustworthy is unknown (see Q-03)."
---

# ADR 0003: Curated in-code registry instead of open-web discovery

Status: accepted (reconstructed from code)

## Context

The project's core value proposition is donor trust: the README cites the <2% VC share going to female-led African teams and positions the agent as an "intelligent intermediary" that verifies credible organizations. An LLM with web search can find organizations, but cannot vouch for them — it would return a mix of credible NGOs and unverifiable entities, pushing due diligence back onto the donor.

## Options considered

1. **Open-web search (the Naive Agent)** — fastest to build, but unverified results and no trust metrics; the burden of diligence stays with the donor.
2. **Curated static registry in code** — a hardcoded, normalized list of vetted organizations with trust metadata (rating, efficiency, verification source), exposed via a deterministic tool.
3. **Live verified registry / API** — a real database with an ongoing vetting process; nothing in the repo implements this.

## Decision

Use a curated static registry (option 2): `data/femtech_programs.py` holds 5 organizations across 3 regions with trust metadata, served through the `find_tech_initiatives` tool. The Finding Agent is explicitly forbidden from web search ("Do NOT search the open web. Only use the trusted tool."). The open-web option is retained as a separate `Naive_Agent` demo to make the contrast measurable rather than asserted.

## Consequences

- **Positive:** every result the donor sees carries a stated verification source, rating and efficiency — the trust story is deterministic, not model-generated, so it cannot hallucinate an organization.
- **Positive:** discovery is fast, cheap and offline (no search API calls), and the curated set matches the README's named initiatives.
- **Positive:** keeping the Naive Agent in the repo gives a persuasive before/after demo artifact.
- **Negative:** the registry covers only 5 organizations in 3 fixed regions; region matching is exact-lowercase, so natural phrasing ("East Africa", "Kenya") silently returns nothing unless the LLM normalizes it (Q-08).
- **Negative:** trust data is a static snapshot with no refresh, review or revocation path — an organization could degrade after being curated (Q-03).
- **Negative:** discoverability of new organizations requires a code change.
