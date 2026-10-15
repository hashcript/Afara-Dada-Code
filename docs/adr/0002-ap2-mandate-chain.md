---
blueprint:
  type: adr
  id: adr_0002-ap2-mandate-chain
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "requirements.txt:3 — 'git+https://github.com/google-agentic-commerce/AP2.git@main' dependency"
    - "tools/femtechorgs_tools.py:92-99 — IntentMandate model construction; merchant_tools.py:122-159 — W3C PaymentRequest + CartMandate; payment_tools.py:63-92 — PaymentResponse + PaymentMandate"
    - "credentials_provider/agent.py:69-73 — 'THE COMPLETE AP2 CREDENTIAL CHAIN' described as an auditable chain of trust"
  guesses:
    - "The extra non-AP2 fields (intent_id, org_name, amount, user_consent) bolted onto the dicts suggest the AP2 models alone were insufficient for the demo's needs (see Q-01/Q-02)."
---

# ADR 0002: AP2 three-credential mandate chain as the trust backbone

Status: accepted (reconstructed from code)

## Context

The system needs an auditable, structured way to carry a donor's decision from "I want to fund X" through "X has committed to receiving the funds" to "the donor authorized the transfer". Hand-rolled JSON between agents would be unversioned and unauditable, and the project's positioning (agentic commerce for funding) calls for a recognized protocol.

## Options considered

1. **Ad-hoc JSON dictionaries** passed through session state — zero dependencies, but no schema validation and no standard payment semantics.
2. **AP2 (Agentic Commerce Protocol) mandate types** — use the library's Pydantic models: `IntentMandate` → `CartMandate` (embedding a W3C PaymentRequest) → `PaymentMandate`.
3. **W3C Payment Request only**, without AP2 wrappers — standard payment description but no intent or consent credentials.

## Decision

Adopt AP2's mandate chain (option 2). Each stage materializes one AP2 credential via Pydantic models, dumps it to a dict, augments it with domain fields (`intent_id`, `org_name`, `amount`, `user_consent`), and stores it in session state under a dedicated key. The chain is: Finding Agent creates the `IntentMandate` (1-hour expiry); the Merchant Agent converts it into a `CartMandate` whose `contents.payment_request` is a W3C PaymentRequest with card method data and a 15-minute expiry, plus a signature; the Credentials Provider links a `PaymentMandate` to the cart and records consent.

## Consequences

- **Positive:** credentials are schema-validated on both write and read (`IntentMandate.model_validate`, `CartMandate.model_validate`), so structural corruption between stages is caught early with an error status instead of a crash.
- **Positive:** expiry is a first-class protocol field, enabling the two time-based security checks (intent at cart creation, cart at payment).
- **Positive:** the chain gives the demo a legible "audit trail" narrative and aligns with an existing agentic-commerce standard rather than inventing vocabulary.
- **Negative:** the domain extensions live outside the AP2 schema — `amount` is read from the raw dict (`merchant_tools.py:114`) rather than from a validated field, so a mandate missing it silently defaults to `0.0`.
- **Negative:** AP2 is pinned to a floating git branch (`@main`), so upstream model changes can break this code at install time.
- **Negative:** the "verifiable credential" claim is currently decorative — signatures are unkeyed hashes and consent is a hardcoded boolean, so the chain is structured but not cryptographically verifiable (see ADR 0004, Q-07).
