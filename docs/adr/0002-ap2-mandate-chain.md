---
blueprint:
  type: adr
  id: art_adr-0002-ap2-mandate-chain
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:79-113 — IntentMandate via ap2.types"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:13-21, 122-159 — W3C PaymentRequest construction inside CartMandate"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:12-13, 48-92 — PaymentMandate and PaymentResponse"
    - "requirements.txt:3 — git+https://github.com/google-agentic/AP2.git@main"
  guesses:
    - "AP2 was adopted both for standards alignment and hackathon/protocol-fit reasons; the repo does not state a rationale (see Q-08)"
---

# ADR-0002: Use the AP2 mandate protocol (IntentMandate → CartMandate → PaymentMandate) as the payment vocabulary

Status: accepted (reconstructed from code)

## Context

An agentic donation flow needs a structured, verifiable representation of "the user wants to fund X", "the organization commits to receiving those funds", and "the user authorized execution". Ad-hoc JSON blobs would work for a demo but would not survive contact with a real payment processor, and would leave no standardized audit trail. The repo depends on Google's AP2 (Agentic Payments Protocol) library, pinned to `main`.

## Options considered

1. **Ad-hoc dictionaries** for intent/cart/payment — maximum freedom, zero interoperability or validation.
2. **W3C Payment Request only** — models the offer, but says nothing about user intent or execution authorization.
3. **AP2 three-credential chain over W3C PaymentRequest** (chosen) — `IntentMandate` (user desire), `CartMandate` (organization offer, wrapping a W3C `PaymentRequest`), `PaymentMandate` (execution authorization, wrapping a `PaymentResponse`).

## Decision

Represent every funding stage as an AP2 mandate built from the library's Pydantic models, serialized to dictionaries for session state. The Merchant Agent embeds a full W3C `PaymentRequest` (payment method data: card networks/types; details: display items and total; options: no shipping) inside the `CartMandate`, and the Credentials Provider mirrors it with a `PaymentResponse` carrying a simulated token. Domain-specific fields (`org_name`, `amount`, `currency`, custom timestamps, IDs) ride alongside as extra dictionary keys since the standard models don't carry them.

## Consequences

- **Positive**: standardized, validated structures — `model_validate` catches malformed mandates at each stage; a real AP2-compatible payment processor could replace the simulation without changing the agent contracts.
- **Positive**: each mandate gets protocol-native expiry fields (`intent_expiry`, `cart_expiry`), which the tools re-check at every stage.
- **Negative**: domain data (amount, currency, org name) lives *outside* the standard models as extra dict keys, so validation of the actual money fields is entirely hand-rolled and could drift from the protocol types.
- **Negative**: depending on `AP2@main` (a moving branch, not a release) makes builds non-reproducible.
