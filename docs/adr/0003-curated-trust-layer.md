---
blueprint:
  type: adr
  id: art_adr-0003-curated-trust-layer
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_requirements, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py — hardcoded curated dataset with verification sources"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py:22-23 — 'Do NOT search the open web. Only use the trusted tool.'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py — the open-web 'before' baseline agent"
  guesses:
    - "The curated list is a demo fixture; long-term governance of the dataset is undecided (see Q-09)"
---

# ADR-0003: Curated verification dataset instead of open-web discovery

Status: accepted (reconstructed from code)

## Context

The product's differentiator is trust: donors need to know the organizations they fund are legitimate before money moves. Open-web search mixes credible NGOs with unverifiable entities and puts the burden of due diligence on the donor. At the same time, the team needed to demonstrate the *contrast* between the two approaches.

## Options considered

1. **LLM web search** (Google Search grounding) for discovery — always current, but unverified and manipulable.
2. **External verification API / charity registry** (e.g., charity watchdog) — authoritative, but no Africa-specific equivalent covering these community organizations, and out of demo scope.
3. **Curated in-repo dataset with trust metrics** (chosen) — a hardcoded, hand-vetted list of organizations, each with an explicit `verification_source`.

## Decision

The Finding Agent is instructed to *never* search the open web and only use `find_tech_initiatives`, which reads a hardcoded dataset of five vetted organizations across three regions (`pan-africa`, `east-africa`, `global-diaspora`). Each record carries trust metadata — verification source, efficiency (share of funds to programs), rating, impact metrics, HQ, mission, website — that the tool formats to foreground verification. A separate `Naive_Agent` using `google_search` is kept in the repo as a demonstrable "before" state.

## Consequences

- **Positive**: the trust claim is enforceable — the main-flow agent structurally cannot surface unverified organizations, and presented metrics are consistent.
- **Positive**: the Naive Agent makes the value proposition demoable side by side.
- **Negative**: coverage is fixed at five organizations; discovery adds no new information.
- **Negative**: trust metrics are static, unversioned and unaudited — data freshness and the vetting process for new organizations are unsolved (Q-09).
- **Negative**: region taxonomy (`west-africa` returns nothing although two orgs are HQ'd in West Africa) is a data-shape mismatch between `region` keys and `hq` fields (Q-04).
