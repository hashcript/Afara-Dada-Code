---
blueprint:
  type: adr
  id: art_0002-ap2-mandate-chain-via-session-state
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "requirements.txt:3: AP2 installed from git+https://github.com/google-agentic-commerce/AP2.git@main"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:79-113,145: IntentMandate built with ap2.types.mandate and written to state['intent_mandate']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:89-165: IntentMandate.model_validate, then CartMandate written to state['cart_mandate']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:104-147: CartMandate.model_validate, then PaymentMandate and payment_result written to state"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:69-74: 'THE COMPLETE AP2 CREDENTIAL CHAIN'"
  guesses:
    - "Extra fields (intent_id, org_name, amount, currency, timestamp, user_consent, agent_present) are added to the dumped dicts because the AP2 models have no slot for them. Downstream AP2 validation is assumed to ignore extra keys (see Q-02)"
---

# ADR 0002 – Use AP2 mandates (Intent → Cart → Payment) passed through ADK session state

Status: accepted (reconstructed from code)

## Context

The product's value is trust: money should go "exactly where it was intended". Each step of the funding flow
must therefore leave an auditable artefact that the next step can check. The agents are separate LLM agents that
need a reliable way to pass structured data, not free text.

## Options considered

1. **Pass details in the conversation text.** Fragile: the LLM can paraphrase or hallucinate amounts and names.
2. **Custom JSON schema in state.** Reliable handoff, but not interoperable and not linked to any standard.
3. **AP2 (Agent Payments Protocol) mandates with W3C PaymentRequest types, stored in ADK session state
   (chosen).** Tools write `model_dump()` dicts to well-known keys. The next tool re-validates them into Pydantic
   models with `model_validate`.
4. A database or message queue between agents. Too heavy for a single-process demo.

## Decision

Model the flow as the AP2 credential chain:

| Step | Producer | State key | Expiry |
|------|----------|-----------|--------|
| IntentMandate | `save_user_choice` (finding_agent) | `intent_mandate` | 1 hour |
| CartMandate (+ merchant_authorization) | `create_cart_mandate` (merchant_agent) | `cart_mandate` | 15 minutes |
| PaymentMandate + payment_result | `create_payment_mandate` (CredentialsProvider) | `payment_mandate`, `payment_result` | n/a |

Tools never trust the LLM for amounts or recipients. They read them from the previous mandate in state. Each
consumer re-validates the structure and checks expiry before it acts.

## Consequences

- ✅ Amounts and recipients flow deterministically from tool to tool. The LLM only triggers the tools.
- ✅ The shapes conform to standards (AP2, W3C PaymentRequest), which eases a later move to real AP2 participants.
- ✅ Expiry windows limit how long stale intents or carts stay usable.
- ⚠️ AP2 is installed from git `main` and is unpinned. Upstream schema changes can break validation (a
  supply-chain and stability risk).
- ⚠️ Custom fields are attached outside the AP2 schema, for example `amount` on the intent. The merchant reads
  `amount` from the raw dict with a 0.0 default (`merchant_tools.py:114`), so a missing amount silently produces
  a $0 cart.
- ⚠️ State is a single per-session slot. A second donation in the same session overwrites the earlier mandates.
  There is no history or idempotency key, so `create_payment_mandate` can run twice on the same cart.
- ⚠️ Mandates are not cryptographically bound (see ADR 0004). The "chain" links by ID, not by signature.
