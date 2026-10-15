---
blueprint:
  type: adr
  id: art_0003-curated-registry-over-open-web-search
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py:1-12: 'Before' state, open web via google_search, unverified results, lacks the Trust Layer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py:1-4: 'Mock database of vetted ... This represents the Trusted Data Layer'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py:22: 'Do NOT search the open web. Only use the trusted tool.'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:17-50: find_tech_initiatives returns trust metrics"
  guesses:
    - "The in-code dict is a stand-in for a future database or vetted API, not the intended long-term store (see Q-04)"
    - "Registry contents (ratings, efficiency) were hand-curated by the team from public sources (see Q-04)"
---

# ADR 0003: A curated "Trusted Data Layer" instead of open-web search for discovery

Status: accepted (reconstructed from code)

## Context

The problem being solved is trust. Donors cannot easily tell credible organisations from unverified ones. The repo keeps a `Naive_Agent` that uses Google Search on purpose, to show the failure mode: results mix credible NGOs with unverified entities and leave due diligence to the donor (`Naive_Agent/agent.py:1-12`). An agent that is about to move money must not act on unverified web results.

## Options considered

1. **Open-web search (Google Search grounding)**: always current and covers many organisations, but unverified and open to SEO spam or impersonation. This is the Naive_Agent.
2. **A curated registry of vetted organisations with explicit trust metrics** (verification source, efficiency, rating, impact).
3. **A hybrid**: search the web, then verify against a registry.

## Decision

Discovery uses only the **curated registry** in `data/femtech_programs.py`, through the `find_tech_initiatives` tool. The Finding Agent is told never to search the open web and has no search tool. The registry holds 5 organisations under 3 region keys (`pan-africa`, `east-africa`, `global-diaspora`, plus `africa` meaning all), and each record carries `verification_source`, `efficiency`, `rating`, `impact_metrics`, `mission`, `hq` and `website`. The Naive_Agent stays only as a separate demo baseline.

## Consequences

- ✅ Discovery cannot return an unvetted organisation, and the trust metrics are shown every time.
- ✅ The tool is deterministic, fast and makes no network call.
- ⚠️ The **funding** path does not enforce the registry: `save_user_choice` accepts any org name, so a donor (or the LLM) can create an intent for an organisation that is not listed (Q-03, NFR T-01).
- ⚠️ The registry data is static and hard-coded. Any change needs a code deploy, there is no provenance or review date, and region lookup only matches exact keys (`"east africa"` and `"west-africa"` return nothing).
- ⚠️ The scope is small: the README mentions organisations that are not in the registry (Q-08).
- ⚠️ The tool returns formatted text and raw data together, which roughly doubles the tokens per discovery call.
