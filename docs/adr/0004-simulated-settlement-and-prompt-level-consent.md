---
blueprint:
  type: adr
  id: art_0004-simulated-settlement-and-prompt-level-consent
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:54-74: 'simulated merchant signature' = SIG_ + sha256(canonical JSON)[:16]"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:66,128,133-143: token 'simulated_funding_token_AFRICA_TECH', consent_granted = True, payment_result.simulation = True"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39,76-78: two-turn confirmation in the prompt; FunctionTool without require_confirmation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent_mock.py:15: mock uses require_confirmation=False and calls that the 'Only difference'"
  guesses:
    - "Simulation is intentional for a demo or hackathon, not a placeholder someone forgot (see Q-02)"
    - "The real agent was meant to use require_confirmation=True, as the mock's comment implies, but the flag was left off (see Q-03)"
---

# ADR 0004 – Simulated settlement and signatures, with consent enforced by the prompt

Status: accepted (reconstructed from code)

## Context

The project shows a secure, agent-driven donation flow. Real card acquiring, organisation key management and
regulated money movement are out of reach for a prototype. The demo still has to show the steps (signed offer,
explicit consent, transaction ID) end to end.

## Options considered

1. **Integrate a real PSP and real signing.** This is realistic but needs merchant onboarding, PCI scope, key
   management and compliance.
2. **Simulate settlement and signatures in the tools (chosen).** The data shapes stay real (AP2/W3C) and the side
   effects are faked.
3. For consent: **(a)** use ADK tool confirmation (`FunctionTool(..., require_confirmation=True)`), where the
   platform enforces a human-in-the-loop approval; or **(b)** use a conversational confirmation in the agent
   instruction (chosen in practice).

## Decision

- The organisation "signature" is `SIG_` followed by the first 16 hex characters of the SHA-256 of the canonical
  CartContents JSON. It uses no key and nothing verifies it.
- The PaymentMandate uses a fixed simulated card token. The transfer is a `payment_result` dict with
  `status: completed` and `simulation: true`. No network call is made.
- Consent is requested in a two-turn conversation that the CredentialsProvider prompt requires. The tool records
  `user_consent = True` unconditionally.
- A mock agent (`agent_mock.py`) with `require_confirmation=False` is meant for automated tests.

## Consequences

- ✅ The whole flow can be demonstrated without credentials, merchants or regulatory setup.
- ✅ The data structures already match AP2 and W3C, so a real backend could replace the simulated functions.
- ⚠️ **Consent rests on the LLM following its prompt.** A model mistake or a prompt injection can call
  `create_payment_mandate` with no "yes", and the mandate would still claim `user_consent: true`.
- ⚠️ The "signature" proves integrity at most, not authenticity. Anyone can forge it, and it is truncated to
  64 bits.
- ⚠️ Donors are told funds were "transferred successfully". The prompt asks for a "(simulated)" note, but
  nothing in the code guarantees the UI says so, which could mislead users in a public demo.
- ⚠️ The mock imports a non-existent `charity_advisor` package and cannot be imported. The intended test
  path is broken (see Q-10).
