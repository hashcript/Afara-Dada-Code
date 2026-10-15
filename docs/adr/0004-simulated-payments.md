---
blueprint:
  type: adr
  id: art_adr-0004-simulated-payments
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:128, 133-143 — consent hardcoded True, simulated transaction result"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:54-74 — SHA-256 hash as 'merchant signature'"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent_mock.py — mock agent that bypasses confirmation"
  guesses:
    - "The simulation boundary was chosen to keep the demo self-contained without payment-network accounts; the README hints at Secret Manager/production intent but no PSP is named (see Q-08)"
---

# ADR-0004: Simulate payment execution and signatures; enforce consent only at the prompt level

Status: accepted (reconstructed from code)

## Context

Building a real funding pipeline requires PSP accounts, KYC, and organizational bank rails that a demo cannot obtain. However, the *shape* of the payment flow (contracts, signatures, consent, transaction records) is the thing being demonstrated. The system therefore needs believable payment semantics without real money movement.

## Options considered

1. **Integrate a real PSP (e.g., Stripe) in test mode** — realistic but requires accounts and network access, and still does not deliver money to African NGOs.
2. **Simulate the whole payment layer in-tool, keeping protocol-shaped records** (chosen) — the tool fabricates a PaymentMandate, a payment token (`simulated_funding_token_AFRICA_TECH`) and a transaction record with `"simulation": true`.
3. **Stop after the CartMandate** — safest, but the demo never shows the completed chain.

## Decision

`create_payment_mandate` simulates the transfer: it validates the cart, builds an AP2 `PaymentMandate` with a simulated `PaymentResponse`, generates a `txn_<hash16>` transaction ID, and writes both mandate and result to state with an explicit `simulation: true` flag. "Signatures" are SHA-256 hashes over canonical JSON (`SIG_<hash16>`), not asymmetric cryptography. User consent is obtained by the Credentials Provider's two-turn conversational pattern in its instruction, but the tool hardcodes `consent_granted = True` and assumes the agent followed its instruction. A mock Credentials Provider (`agent_mock.py`) exists for automated tests and skips confirmation entirely.

## Consequences

- **Positive**: the full three-credential chain is demonstrable end to end with zero external payment dependencies; transaction records are shaped like real ones, easing a future swap to a real processor.
- **Positive**: the `simulation: true` flag makes fabricated transactions self-identifying in state.
- **Negative**: consent enforcement is prompt-level only — any path that reaches `create_payment_mandate` (a misbehaving model, a prompt injection, the mock agent) executes a "transfer" with no code-level consent check (Q-02).
- **Negative**: hash-based "signatures" provide tamper *detection* at best (any party can recompute them); they are not authenticating anyone.
- **Negative**: the mock agent is currently broken (imports from a non-existent `charity_advisor` package), so the no-confirmation test path is dead code (Q-07).
