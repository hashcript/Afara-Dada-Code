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
    - "requirements.txt — google-adk==1.17.0, AP2 pinned to git @main, google-cloud-aiplatform[agent-engines]"
    - "tools/payment_tools.py:128 — consent_granted = True hardcoded"
    - "tools/merchant_tools.py:114 — amount = intent_mandate_dict.get('amount', 0.0)"
    - "credentials_provider/agent_mock.py:7 — stale 'charity_advisor' import"
    - "tools/merchant_tools.py:65-71 — unkeyed signature; tools/femtechorgs_tools.py:90 — 10-char org ID truncation"
    - "data/femtech_programs.py:70-75 — exact lowercase region matching"
    - "scripts/test_merchant.py — only test in the repo"
  guesses:
    - "Performance, scalability and availability cannot be assessed from code (no server, no load profile); characteristics below are limited to what the code implies (see Q-05)."
---

# NFRs and Threats — Afara Dada Code

## Non-functional characteristics

| Characteristic | Assessment from code |
|---|---|
| **Security (payment)** | Demo-grade. Money never moves (result flagged `simulation: True`); secrets are limited to `GOOGLE_API_KEY` in a git-ignored `.env`. See threats below for consent and signature gaps. |
| **Data integrity** | Good within tools: AP2 Pydantic models validate on both write and read, expiry is re-checked at each handoff, and amounts are validated at intent creation. Weak at seams: `amount` falls back to `0.0` if the dict field is missing. |
| **Auditability** | Structural: the three-mandate chain plus per-tool `logging.info/error` with IDs and expiry windows gives a readable trace. But consent and signatures are simulated, so the trail proves intent, not authorization. |
| **Reliability / availability** | Not assessable from code — there is no server or deployment artifact in the repo. Runtime depends entirely on the Gemini API and ADK. |
| **Performance** | Each conversation turn is a Gemini inference; a full funding flow costs at least ~4 model turns plus tool calls. No caching, no streaming configuration visible. |
| **Maintainability** | Clear separation (agents / tools / data) and consistent docstrings; but agent behavior is defined in long prompt instructions (changes there are untested by any CI), AP2 floats on `@main`, and a stale mock file suggests renames are not tracked. |
| **Testability** | Weak. One manual script (`scripts/test_merchant.py`) exercising only the Merchant Agent with seeded state; no unit tests for validation/signature logic, no CI, and the mock payment agent is broken by a stale import. |
| **Portability** | Python package installable via `pip install -e .`; tied to Google stack (ADK, Gemini, Agent Engine) by design. |
| **Internationalization** | USD-only amounts; English-only conversation; region taxonomy fixed to three keys. |

## Bugs and risks noticed in the code

1. **Consent is hardcoded** — `payment_tools.py:128` sets `consent_granted = True` unconditionally. The recorded `user_consent`/`consent_timestamp` in the PaymentMandate do not reflect the donor's actual answer; refusal depends entirely on the LLM choosing not to call the tool. (Blocking for any trust claim — Q-02.)
2. **`agent_mock.py` is unimportable** — `credentials_provider/agent_mock.py:7` imports `charity_advisor.tools.payment_tools`, a package that does not exist in this repo (stale pre-rename name). Any use raises `ModuleNotFoundError`. (Q-04.)
3. **Signature is not a signature** — `merchant_tools.py:54-74` computes `SIG_<sha256(cart JSON)[:16]>` with no key; it is forgeable by anyone and never verified anywhere. The "binding commitment" narrative overstates what the artifact proves. (Q-07.)
4. **Amount defaults to zero** — `merchant_tools.py:114` reads the AP2-external field `intent_mandate_dict.get("amount", 0.0)`; a structurally valid IntentMandate without that extension field produces a $0 CartMandate rather than an error.
5. **Region matching is brittle** — `femtech_programs.py:70-75` requires exact lowercase keys (`east-africa`); "East Africa", "Kenya" or "Nairobi" return an empty list unless the LLM happens to normalize. The Finding Agent's instruction gives examples but no enforcement.
6. **Org ID truncation collisions** — `femtechorgs_tools.py:90` builds `mock_reg_id` as the first 10 alphanumeric chars of the org name; distinct organizations sharing a prefix would produce colliding intent ID namespaces.
7. **Expiry window is not atomic** — validation and settlement are separate steps with no lock; a CartMandate validated at payment-start could settle arbitrarily later (paused process, long Gemini turn) with no re-check inside the transaction itself.
8. **Prompt-enforced state machine** — phase gating, consent and agent boundaries live in instructions, not code; a model deviation (or prompt injection through user messages) can attempt out-of-order tool use. Tool availability limits the blast radius (the Finding Agent has no payment tool) but the pipeline's internal ordering relies on prompt compliance.
9. **AP2 dependency floats** — `requirements.txt:3` pins AP2 to `@main` of a git repo; upstream model changes break installs non-deterministically.
10. **Secrets posture** — only `GOOGLE_API_KEY` in `.env` (git-ignored, good); README also enables Secret Manager but nothing reads it in code, so key handling in any hosted deployment is undefined.
11. **No test coverage for the money path** — validation, expiry and signature logic have no unit tests; the single script is manual and LLM-dependent (cannot run headlessly without an API key).

## STRIDE-lite threat analysis

| Threat | Vector | Current mitigation | Gap |
|---|---|---|---|
| **Spoofing** (organization) | Merchant signature is unkeyed, so a tampered CartMandate re-signs itself; an org's "commitment" cannot be authenticated. | None — signature is decorative (ADR 0004). | Real keyed signatures + verification before payment (Q-07). |
| **Spoofing** (user) | No authentication of the donor anywhere in the flow. | None in code; implied out of scope for demo. | Any production design needs donor identity before consent is meaningful. |
| **Tampering** | Session state (`intent_mandate`, `cart_mandate`) is the only bus; anything that can write state (a future tool, a compromised session store) can alter amount or recipient between stages. | Pydantic re-validation on read; expiry re-checks. | Amount read from unvalidated dict field (default `0.0`); no state checksum/signature chain. |
| **Repudiation** | Donor consent is recorded as `True` regardless of the actual answer; consent timestamp is written even when consent is simulated. | Consent fields exist in the PaymentMandate. | The audit trail cannot prove the donor agreed — the opposite of its stated purpose (Q-02). |
| **Information disclosure** | Tool logs include org names and amounts (`logger.info`); raw initiative data is returned to the model alongside the display format. | `.env` git-ignored. | No log redaction policy; no PII beyond amounts, but amounts are donor-sensitive. |
| **Denial of service** | No server code in the repo; Gemini API is the only remote dependency, so availability inherits the API's rate limits. | N/A at demo scale. | Unassessable until a deployment shape exists (Q-05). |
| **Elevation of privilege** | Prompt injection via user messages could try to make the root or Finding Agent skip to payment or fabricate an IntentMandate narrative. | Structural: Finding Agent has no payment tools; payment tool requires a real CartMandate in state, which requires a real IntentMandate. | The credential chain is the strongest control here — it works precisely because the state keys cannot be talked into existence by the LLM. Keep that property when adding tools. |

## Priority remediations (for the product owner)

1. Thread consent through the `create_payment_mandate` tool signature (blocking, Q-02).
2. Fix or delete `credentials_provider/agent_mock.py` (trivial, Q-04).
3. Decide the real-signature strategy before any "verifiable" claim is made externally (blocking, Q-07).
4. Add unit tests for `_validate_donation_data`, `_validate_intent_expiry`, `_validate_cart_expiry` and the mandate builders — none require the LLM.
5. Pin AP2 to a commit hash.
