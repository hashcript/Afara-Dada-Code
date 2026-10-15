---
blueprint:
  type: adr
  id: art_0004-simulated-settlement-and-prompt-level-consent
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
      - { id: art_seq-donor-funding-flow, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:65-66,128,134-143: simulated card token, consent_granted = True, txn id from hash, simulation: True"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:54-74: simulated merchant signature (unkeyed SHA-256, truncated)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39,76-78: two-turn confirmation in prompt; FunctionTool without require_confirmation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent_mock.py:15: FunctionTool(..., require_confirmation=False) labelled '← Only difference'"
  guesses:
    - "The agent_mock comment suggests the production agent was once meant to use framework-level confirmation (require_confirmation=True), and this was dropped or forgotten (see Q-03)"
    - "Simulation is a deliberate demo-scope choice, not a placeholder awaiting an imminent provider integration (see Q-01)"
---

# ADR 0004: Simulate settlement and signatures, and enforce donor consent through the agent prompt

Status: accepted (reconstructed from code)

## Context

The repository is a demo or learning build (README Quick Start: "Placeholder version for learning", `git checkout my-demo`). Showing the full AP2 flow end to end needs a signature, a payment and a transaction id. Integrating real providers, key management and KYC is out of reach for this scope. The flow still has to show that the donor explicitly agrees before money "moves".

## Options considered

1. **Integrate a real PSP / payment rail** (card, mobile money) and real organisation keys. High effort, and needs compliance work.
2. **Simulate settlement in the tool** *(chosen)*. Make hash-based ids, a fixed token and a `simulation: true` flag.
3. **Consent through ADK tool confirmation** (`FunctionTool(require_confirmation=True)`), where the framework pauses the tool call until the user approves.
4. **Consent through the LLM prompt** *(chosen)*. The two-turn pattern "Do you want to proceed…?" then wait for "yes".

## Decision

- `create_payment_mandate` performs no external call. It makes `txn_<sha256[:16]>`, uses the token `simulated_funding_token_AFRICA_TECH` and returns `status: completed, simulation: true`.
- The merchant "signature" is `SIG_` plus the first 16 hex characters of an unkeyed SHA-256 over the canonical cart JSON.
- Consent is required only by the CredentialsProvider instruction. The tool is registered without `require_confirmation`, and the tool itself sets `consent_granted = True` (`payment_tools.py:128`).
- A mock agent that skips confirmation (`require_confirmation=False`) is intended for automated tests.

## Consequences

- ✅ The demo runs end to end with no external payment dependencies or secrets beyond the Gemini key.
- ✅ Results are clearly marked as simulated (`simulation: true`, the "(simulated)" wording in the prompt).
- ❌ **Consent is not enforced.** If the model calls `create_payment_mandate` early (because of model error or prompt injection), the payment goes through and is recorded with `user_consent: true` and a consent timestamp. This creates a false audit record (NFR T-R1, Q-03).
- ❌ The signature proves nothing. Anyone can compute it, it is truncated to 64 bits, and the payment step never checks it (NFR T-S1, Q-06).
- ⚠️ The mock cannot be imported (`from charity_advisor.tools...`), so there is no working automated path that skips confirmation (NFR B-01).
- ⚠️ A real integration later will need idempotency, mandates that are consumed once, real signing and verification, and error and retry handling. None of these exist today.
