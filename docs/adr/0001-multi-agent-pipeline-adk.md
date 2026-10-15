---
blueprint:
  type: adr
  id: adr_0001-multi-agent-pipeline-adk
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:14-21,26-88 — SequentialAgent pipeline and root orchestrator with per-phase delegation"
    - "agent instructions in finding_agent/agent.py:46-58, merchant_agent/agent.py:41-47, credentials_provider/agent.py:55-61 — explicit 'you do NOT ...' boundary clauses"
  guesses:
    - "The mock agent's require_confirmation=False flag suggests ADK tool-level confirmation was known as an alternative to prompt-level consent (see Q-02)."
---

# ADR 0001: Specialist multi-agent pipeline on Google ADK

Status: accepted (reconstructed from code)

## Context

The system must take a donor from vague intent ("support girls coding in Kenya") to a confirmed funding transfer, while appearing trustworthy at each step. A single LLM agent with all tools available would mix research, contract creation and payment execution in one context, making it hard to reason about which capability is being exercised when, and easy for the model to leapfrog safety steps.

## Options considered

1. **One monolithic agent** with all five tools — simplest, but no structural separation between discovery and payment, and prompt-injected instructions could trigger payment tools during research.
2. **Specialist agents composed with ADK** — a root orchestrator delegating to a Finding Agent, then to a strict Merchant → Credentials sequence (`SequentialAgent`), each agent holding only its own tools.
3. **Non-LLM workflow code** with an LLM only for the chat surface — most controllable, but abandons ADK's agent delegation and the agentic narrative the project is built on.

## Decision

Use Google ADK multi-agent composition (option 2): a root orchestrator `AfaraTechAdvisor` with two sub-agents — `finding_agent`, and a `FundingProcessingPipeline` `SequentialAgent` that runs `merchant_agent` then `credentials_provider` in fixed order. Each specialist's instruction carries hard boundaries ("You do NOT process payments", "You do NOT see the user's payment methods"), and each agent exposes only the `FunctionTool`s for its stage. Inter-agent data flows exclusively through ADK session state.

## Consequences

- **Positive:** capability boundaries are structural (an agent without the payment tool cannot call it); the discovery phase can span many turns without payment risk; the merchant→payment order is enforced by `SequentialAgent`, not by prompt discipline; each agent is independently testable (`scripts/test_merchant.py` runs the Merchant Agent alone with seeded state).
- **Positive:** the two-phase gate ("only proceed after a valid IntentMandate exists") has a clear, checkable signal in the Finding Agent's output.
- **Negative:** all safety boundaries that are not tool-availability (phase transitions, consent, expiry narration) are enforced only in prompt instructions — an LLM can still deviate; there is no code-level state machine.
- **Negative:** every turn is a separate Gemini inference per agent, adding latency and cost versus a single agent.
- **Negative:** shared-state keys are an implicit contract between agents; renaming a key in one tool silently breaks the next stage.
