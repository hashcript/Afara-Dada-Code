---
blueprint:
  type: adr
  id: art_0003-curated-vetted-registry-instead-of-open-web-search
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
      - { id: art_requirements, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py:1-12: 'Before' state, open web via google_search, 'lacks the Trust Layer'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py:1-76: 'Mock database of vetted ... Organizations. This represents the Trusted Data Layer'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py:20-23: 'Do NOT search the open web. Only use the trusted tool.'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:17-50,157-182: find_tech_initiatives and trust-focused formatting"
  guesses:
    - "The in-code dictionary stands in for a future database or registry service; there is no plan in the repo for what replaces it (see Q-02)"
---

# ADR 0003: Discover organisations only from a curated, vetted registry (the "Trust Layer"), not from open-web search

Status: accepted (reconstructed from code)

## Context

The core problem the product addresses is that donors find it hard to identify **credible** organisations (README.md:13-15). An LLM with web search answers quickly, but it "returns unverified results (mixing credible NGOs with potentially unverified entities)" and "places the burden of due diligence on the user" (`Naive_Agent/agent.py:4-8`).

## Options considered

1. **Open-web search** (`google_search` tool). Kept as the `Naive_Agent` baseline to show the problem.
2. **Web search with verification after the fact** by the LLM. Still unreliable and hard to audit.
3. **Curated registry behind a deterministic tool** *(chosen)*. A fixed set of vetted organisations with explicit trust metadata (verification source, efficiency, rating, impact), queried by region.

## Decision

- `data/femtech_programs.py` holds a read-only dictionary of 5 organisations under `pan-africa`, `east-africa` and `global-diaspora`. `africa` returns all of them.
- `find_tech_initiatives(region)` is the only discovery tool the finding agent has. The instructions forbid open-web search.
- Results are formatted to put trust first ("✅ Verified By", "💰 Efficiency % to programs"). Raw records are passed along so the LLM can answer follow-up questions without other sources.

## Consequences

- ✅ Discovery answers are limited to vetted data, and the agent shows where each organisation's credibility comes from.
- ✅ Discovery is deterministic, fast and costs nothing; only the presentation uses the LLM.
- ⚠️ The data is static Python. Updating it requires a code change and redeploy, and there is no record of who vetted what or when (Q-02).
- ⚠️ The trust boundary covers **discovery only**. `save_user_choice` does not check the chosen name against the registry, so the LLM or a prompt-injected donor message can create an intent for any organisation name (NFR B-04, Q-04).
- ⚠️ Region matching is exact on lowercase keys. Natural phrases such as "East Africa" or "west-africa" (named in the tool docstring) return `not_found` unless the LLM normalises them (NFR B-05, Q-05).
- ⚠️ Organisations are identified by display name, with no stable id. This leaks into the intent id and the "merchant" identity downstream.
