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
    - "requirements.txt:3: git+https://github.com/google-agentic-commerce/AP2.git@main"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:79-154: IntentMandate built with ap2.types.mandate, written to state['intent_mandate'], expiry 1h"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175: reads intent from state, validates expiry, writes CartMandate (15 min) to state['cart_mandate']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157: reads cart from state, validates expiry, writes payment_mandate and payment_result"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:69-74: 'THE COMPLETE AP2 CREDENTIAL CHAIN'"
  guesses:
    - "1 hour (intent) and 15 minutes (cart) are demo defaults, not product decisions (see Q-06)"
    - "The AP2 Pydantic models ignore extra keys (intent_id, amount, timestamp) on model_validate; otherwise the merchant step would fail (see Q-07)"
---

# ADR 0002: AP2 three-mandate credential chain, handed off through ADK session state

Status: accepted (reconstructed from code)

## Context

Donors need assurance that money goes "exactly where it was intended" (`credentials_provider/agent.py:74`). The payment step needs proof that the donor meant to fund this organisation, that the organisation agreed to the terms, and that the donor authorised execution. These facts are produced by three different agents in different turns, so they have to cross agent boundaries without being re-typed by an LLM.

## Options considered

1. **Pass details in natural language between agents**, so each LLM restates the organisation and amount. Simple, but amounts and names can be hallucinated or tampered with, and nothing is auditable.
2. **A custom JSON contract** between tools. Structured, but non-standard.
3. **AP2 mandates (IntentMandate, CartMandate, PaymentMandate) using the AP2 Pydantic types, with W3C PaymentRequest inside the cart, stored in ADK session state** under well-known keys.

## Decision

Use **AP2** types from the AP2 GitHub repository. Each tool:

1. reads the previous mandate from `tool_context.state` (`intent_mandate`, then `cart_mandate`),
2. re-validates its schema (`model_validate`) and its **expiry** (intent 1 h, cart 15 min) in Python, so the check does not depend on the LLM,
3. writes the next mandate back to state (`cart_mandate`, `payment_mandate`, `payment_result`).

The LLM agents never pass amounts or IDs to the downstream tools: `create_cart_mandate` and `create_payment_mandate` take only `tool_context`.

## Consequences

- ✅ Amount and recipient flow from tool to tool through structured data. Once the intent exists, the LLM cannot change the amount.
- ✅ Expiry checks are deterministic and fail closed with `{status: "error"}`.
- ✅ The vocabulary follows a public standard (AP2, W3C PaymentRequest), which eases a later move to real payment rails.
- ⚠️ State keys are a single slot each. A second intent or cart overwrites the first, so there is no history and no idempotency key.
- ⚠️ No step checks that the cart is derived from the *current* intent. The cart does not carry `intent_id`.
- ⚠️ `amount` and `intent_id` are custom extras outside the AP2 IntentMandate. The merchant tool reads `amount` from the raw dict and defaults to `0.0` if it is missing.
- ⚠️ AP2 is pinned to `@main`, so upstream schema changes can break the build without warning.
- ⚠️ Session state is in memory. The "auditable chain" disappears when the process restarts.
