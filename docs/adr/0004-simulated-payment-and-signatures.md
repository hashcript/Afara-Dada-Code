---
blueprint:
  type: adr
  id: adr_0004-simulated-payment-and-signatures
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "tools/payment_tools.py:66,128,134-143 — 'simulated_funding_token_AFRICA_TECH', consent_granted = True, payment_result 'simulation': True"
    - "tools/merchant_tools.py:54-74 — _generate_merchant_signature: SIG_ + sha256(canonical JSON)[:16], docstring says 'simulated merchant signature'"
    - "credentials_provider/agent.py:45 — 'Simulate the fund transfer'"
  guesses:
    - "No real payment integration was ever stubbed (no PSP SDK, webhook, or payment env vars), so simulation is assumed to be a deliberate stage decision, not an unfinished integration (see Q-01)."
---

# ADR 0004: Simulated payments and simulated signatures

Status: accepted (reconstructed from code)

## Context

The demo must demonstrate the full funding journey — offer, signature, consent, transfer — without moving real money or holding real payment credentials. Real payment rails would demand PSP contracts, PCI scope, organization bank details and regulatory handling, none of which exist in the repo.

## Options considered

1. **Integrate a real PSP now** — impossible in scope: no merchant accounts, no organization payout rails, and it would make the demo unsafe to run.
2. **Simulate the entire execution layer** — keep the mandate structure and consent UX real, but fabricate the signature and the transfer, and label results as simulated.
3. **Stop after the CartMandate** — no transfer step at all; loses the end-to-end narrative.

## Decision

Simulate the execution layer (option 2). The merchant signature is an unkeyed hash `SIG_<sha256(canonical cart JSON)[:16]>`. Consent is elicited conversationally by the Credentials Provider, but the tool records `consent_granted = True` unconditionally. The "payment" fabricates a `txn_` ID over a simulated card token (`simulated_funding_token_AFRICA_TECH`) and writes a result record marked `"simulation": True`.

## Consequences

- **Positive:** the demo shows the complete three-credential chain and conversational consent UX without payment infrastructure, cost or regulatory exposure.
- **Positive:** the simulation markers are explicit (token name, `"simulation": True`), so results are unlikely to be mistaken for real transfers.
- **Negative:** the signature proves nothing — anyone who can produce the cart contents can produce the same signature; it cannot detect tampering between signing and verification because there is no verifier at all.
- **Negative:** the consent record is unconditionally `true` once the tool runs, so the "user consent" credential does not actually capture the donor's answer; refusal happens only if the LLM never calls the tool (Q-02, blocking).
- **Negative:** expiry validation remains meaningful, but the expiry-to-settlement window has no atomicity: a cart can pass validation and "settle" 15 minutes later in a paused process with no guard.
- **Migration cost:** moving to real rails later means replacing the signature scheme with keyed signatures, threading consent into the tool signature, and inserting a PSP — the state-key contract (`intent_mandate` → `cart_mandate` → `payment_mandate`) is the part designed to survive that swap (ADR 0002).
