---
blueprint:
  type: adr
  id: art_0003-curated-in-code-trust-directory
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py:1-3: 'Mock database of vetted ... This represents the Trusted Data Layer'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py:22: 'Do NOT search the open web. Only use the trusted tool.'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py:1-12: open-web google_search agent described as the 'Before' state lacking a Trust Layer"
  guesses:
    - "The hard-coded dict is a stand-in for a future curated database or registry (see Q-06)"
---

# ADR 0003 – A curated, vetted initiative directory instead of open-web search

Status: accepted (reconstructed from code)

## Context

Donors struggle to tell credible female tech empowerment organisations from unverified ones. An LLM with web
search answers quickly but mixes legitimate NGOs with unverified entities and leaves due diligence to the donor.
The repo keeps this "before" situation as `Naive_Agent` to show the contrast.

## Options considered

1. **Open-web search (Google Search tool).** Coverage and freshness are high, but nothing is verified. Implemented
   only as the `Naive_Agent` demo.
2. **A curated, in-code directory behind a function tool (chosen).** Each entry carries trust metadata:
   verification source, rating, efficiency and impact.
3. An external registry or database (charity registers, a CMS, BigQuery). This needs integration and ownership.

## Decision

Discovery uses `find_tech_initiatives(region)` only. That tool reads `get_initiatives_by_region()`, a Python dict
holding five vetted organisations under `pan-africa`, `east-africa` and `global-diaspora`, with `africa` meaning
all of them. The finding agent is told not to search the web. Results are formatted to put the verification
source first.

## Consequences

- ✅ Recommendations are deterministic and reviewable. The LLM cannot invent organisations during discovery.
- ✅ No external calls or credentials are needed for discovery.
- ⚠️ Changing data means a code change and a redeploy. There is no admin process, audit trail or freshness date.
- ⚠️ "Verified" is a free-text claim in the code (`verification_source`). Nothing checks it, and the sources of
  rating and efficiency are not documented (see Q-06).
- ⚠️ **The trust boundary stops at discovery.** `save_user_choice` accepts any `org_name`, and later tools do not
  check it against the directory. A donor or the LLM could create mandates for an unlisted organisation (see
  Q-01).
- ⚠️ Region matching is an exact lower-cased key lookup. Free text such as "East Africa" or "West Africa"
  returns `not_found` unless the LLM normalises it (see Q-07).
