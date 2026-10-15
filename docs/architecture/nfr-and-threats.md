---
blueprint:
  type: nfr
  id: art_nfr-and-threats
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:128 — hardcoded consent"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:54-74 — hash-based signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent_mock.py:7 — broken import of non-existent charity_advisor package"
    - "afara-dada-code-agents/scripts/test_merchant.py:19 — imports root_agent from merchant_agent.agent which only defines merchant_agent"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:18-50 — no pagination/size limits; raw_data echoes full records"
    - "README.md:38-43 — Google Cloud services enablement and .env with GOOGLE_API_KEY"
    - "requirements.txt — AP2 pinned to @main branch"
  guesses:
    - "No performance/cost targets exist anywhere in the repo; the characteristics below are qualitative observations (see Q-01)"
---

# NFRs and threats — Afara Dada Code

## Non-functional characteristics (as observed in code)

| Characteristic | Current state | Notes |
|---|---|---|
| **Security of consent** | Weak — prompt-level only | `create_payment_mandate` hardcodes `consent_granted = True` (`payment_tools.py:128`); the two-turn confirmation exists only in the agent instruction. Any caller of the tool bypasses it. |
| **Authentication** | None | No user accounts, no auth on any boundary; the donor is an ADK `user_id` string. |
| **Integrity of mandates** | Tamper-evident at best | "Signatures" are unkeyed SHA-256 hashes over canonical JSON (`merchant_tools.py:54-74`) — anyone can recompute them; they authenticate no one. |
| **Authorization freshness** | Good pattern | Both intent (1h) and cart (15min) expiries are re-validated in code at each stage, with clear error messages. |
| **Auditability** | Good for a demo | Every mandate and the transaction result carry IDs and UTC timestamps in session state; the chain is reconstructable. |
| **Persistence** | None | In-memory ADK sessions only; state disappears with the process. No database anywhere. |
| **Availability / scalability** | Single process | One Python package on the ADK runtime; the only external dependency is the Gemini API, so availability is bounded by it. |
| **Performance** | Unmeasured | No caching, rate handling, or latency budget in code; each agent turn is an LLM round trip, so the full flow costs several Gemini calls plus tool executions. |
| **Data quality / trust** | Static | Five hand-vetted organizations, hardcoded, no refresh mechanism or versioning. |
| **Maintainability** | Reasonable | Clear module boundaries (agent / tools / data), typed tool signatures, docstrings; but cross-agent state keys are an implicit, undocumented contract. |
| **Reproducibility of builds** | Weak | `AP2` dependency is pinned to `@main` of a git repo (`requirements.txt:3`), not a release; model is a `-preview` Gemini version. |
| **Testability** | Partial | One end-to-end-style script (`scripts/test_merchant.py`) with simulated state; no unit tests, no CI; the script and the mock agent are currently broken (see Bugs). |
| **Privacy** | Minimal exposure | No PII collected by the code; the conversation content flows to the Gemini API, and `find_tech_initiatives` returns `raw_data` of the full records into model context. |
| **Localization** | English/USD only | All copy in English; amounts in USD with a $1,000,000 cap (`femtechorgs_tools.py:73-74`). |

## Bugs found in the code (recorded, not fixed)

1. **`credentials_provider/agent_mock.py:7`** imports `from charity_advisor.tools.payment_tools import create_payment_mandate`, but no `charity_advisor` package exists in the repo — a leftover from a rename to `femtech_empowerment_funding_advisor`. The mock agent cannot be imported at all.
2. **`scripts/test_merchant.py:19`** imports `root_agent` from `femtech_empowerment_funding_advisor.merchant_agent.agent`, but that module defines only `merchant_agent` (the `root_agent` alias lives in the package `__init__.py`). The test script raises `ImportError` on startup.
3. **`payment_tools.py:128`** — `consent_granted = True` contradicts the Credentials Provider's instruction that the tool must be called *after* explicit user confirmation. Also worth noting: a `FunctionTool(func=create_payment_mandate, require_confirmation=False)`-style guard exists in the mock agent, implying the real agent's confirmation is expected to be tool-level in ADK, which the current wiring does not implement.
4. **Region taxonomy mismatch** — `data/femtech_programs.py` has no `west-africa` key although two listed organizations are HQ'd in Nigeria/Ghana; a donor asking for "west-africa" gets an empty result.
5. **`merchant_tools.py:114`** reads `amount` from the raw intent dict with `dict.get("amount", 0.0)` — a structurally valid but amount-less IntentMandate would produce a $0.00 CartMandate rather than an error, since the AP2 `IntentMandate` model carries no amount to validate.
6. **README quick start** refers to `cd afara-dada-code-agents` and `git checkout my-demo`, a branch that does not exist in this repo, and names the clone directory inconsistently with the actual repo name (`Afara-Dada-Code`).

## STRIDE-lite threat analysis

| # | Threat | STRIDE | Where | Notes |
|---|---|---|---|---|
| T-1 | **Consent bypass** — a prompt injection or confused model calls `create_payment_mandate` without the donor's "yes"; the tool hardcodes consent, so nothing in code stops it. | Tampering / Elevation of privilege | `payment_tools.py:128` | Highest-severity gap in the demo. Mitigated only by the instruction text. |
| T-2 | **Spoofed merchant signature** — the `SIG_<sha256>` "signature" is unkeyed and recomputable by anyone, so a tampered CartMandate can be re-signed validly. | Spoofing / Tampering | `merchant_tools.py:54-74` | Acceptable for simulation; must not survive into real money movement. |
| T-3 | **Organization name confusion** — orgs are identified by free-text name; an LLM could pass a near-verbatim name ("She Code Africa Ltd") that still passes the non-empty check, creating an intent for an organization that is not the verified one. | Spoofing | `femtechorgs_tools.py:53-76` | No code-level match against the curated dataset in `save_user_choice`. |
| T-4 | **Prompt injection via dataset or conversation** — malicious text in `raw_data` (echoed into model context) or in the donor's message could steer an agent to skip phases or exfiltrate state. | Tampering / Information disclosure | `femtechorgs_tools.py:49` | Dataset is trusted-by-construction today; any future open data source raises this sharply. |
| T-5 | **Secrets handling** — `GOOGLE_API_KEY` loaded from a plain `.env` in the repo tree (gitignored, but no example file or vault wiring); README also enables Secret Manager without the code using it. | Information disclosure | `README.md:42-43`, `test_merchant.py:12-13` | Low impact for a demo key, poor pattern to inherit. |
| T-6 | **Stale authorization replay** — mitigated in the happy path by expiry checks, but state holds no idempotency record: the same cart could be re-processed to produce duplicate "transactions" within its 15-minute window. | Repudiation / Tampering | `payment_tools.py:104-121` | No uniqueness check on cart_id or transaction deduplication. |
| T-7 | **No sender authentication / repudiation** — nothing binds a donor to a transaction (no accounts, no signature of consent), so any completed "transfer" is deniable. | Repudiation | whole system | Fine for simulation; a production requirement. |
| T-8 | **Dependency supply chain** — AP2 is consumed from `@main` of a live git repo, so any upstream change becomes part of every fresh install, unreviewed and unpinned. | Tampering | `requirements.txt:3` | Pin a commit or release. |

## Recommended follow-ups (for the product owner)

- Enforce consent in code (tool-level `require_confirmation` or a consent token written to state by a separate confirmation step) — closes T-1.
- Validate `org_name` in `save_user_choice` against the curated dataset — closes T-3.
- Fix the two broken imports (Bugs 1–2) or delete the dead mock agent — restores the test path.
- Pin the AP2 dependency to a commit hash; add a minimal unit-test suite over the tool functions, which are pure-state and cheap to test.
