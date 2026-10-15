---
blueprint:
  type: adr
  id: art_0004-simulated-settlement-and-signatures
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:54-74: _generate_merchant_signature = 'SIG_' + sha256(canonical JSON)[:16], described as simulated"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:62-67: PaymentResponse token 'simulated_funding_token_AFRICA_TECH'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:128: consent_granted = True  # Assume consent for this demo flow"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:133-143: payment_result with simulation: True"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39,76-78: consent requested via prompt; FunctionTool without require_confirmation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent_mock.py:15: require_confirmation=False marked '← Only difference'"
  guesses:
    - "Simulation is a deliberate demo-scope decision, not an unfinished integration (see Q-01)"
    - "The author intended the real CredentialsProvider to use tool-level confirmation (as implied by the mock's comment) but did not set it (see Q-02)"
---

# ADR 0004: Simulated settlement, hash-based "signatures" and prompt-level consent

Status: accepted (reconstructed from code)

## Context

The project shows how an agent can carry a donor from "wanting to help" to "money sent". Doing this for real needs a payment service provider, merchant onboarding, signing keys held by each organisation, donor KYC and regulatory work in several African markets. None of that exists in the repo. The demo still needs to produce believable AP2 artefacts: signatures, transaction IDs and consent.

## Options considered

1. **Integrate a real PSP** (card or mobile money) and real merchant signing keys (JWS or VC signatures).
2. **Simulate settlement and signatures locally**, keeping AP2-shaped artefacts so a real integration can replace them later.
3. **Stop at the CartMandate** and do no payment step.

For consent:

- a. Tool-level human-in-the-loop confirmation (ADK `FunctionTool(require_confirmation=True)`).
- b. A prompt instruction telling the LLM to ask and wait.

## Decision

Option **2** with consent **b**:

- The merchant "signature" is `SIG_` followed by the first 16 hex characters of a SHA-256 hash over the canonical JSON of the cart contents. No key is used and nothing verifies it.
- Payment builds a spec-shaped PaymentMandate with a fixed simulated token and writes a `payment_result` with `status: completed, simulation: true`. Transaction and mandate IDs are truncated SHA-256 hashes of cart ID and timestamp.
- Consent is asked for by the Credentials Provider's instruction ("Two-Turn Conversational Confirmation Pattern"). The tool sets `consent_granted = True` unconditionally, and its `FunctionTool` keeps ADK's default (no confirmation). The mock agent, meant to *skip* confirmation, sets `require_confirmation=False` explicitly, which is the same value as the default.

## Consequences

- ✅ The demo runs end to end with only a Gemini key, and the artefact shapes match AP2 and W3C.
- ✅ Simulation is marked clearly (`simulation: True`, "simulated" in the messages).
- ⚠️ The "signature" offers **no authenticity**. Anyone who can write state can recompute it, and the payment step never checks it.
- ⚠️ **Consent is not enforced.** An LLM that misreads the turn, or a prompt injection, can call `create_payment_mandate` without a "yes", and the record will still say `user_consent: true`. Moving to real money requires option (a) or an equivalent check in code (Q-02).
- ⚠️ The mock and real Credentials Providers behave the same at the tool level. The mock also cannot be imported (`charity_advisor.tools.payment_tools`).
- ⚠️ A real integration will need a new trust boundary: secrets management, webhooks, idempotency and reconciliation. None of these have a place in the current design.
