---
blueprint:
  type: adr
  id: art_adr-0001-multi-agent-separation-of-duties
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:14-21 — SequentialAgent pipeline"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py:46-58 — 'IMPORTANT BOUNDARIES' block"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/merchant_agent/agent.py:41-47 — boundaries"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:55-61 — boundaries"
  guesses:
    - "The boundary text in the instructions is intended as prompt-level policy, since no code-level capability isolation exists (see Q-01)"
---

# ADR-0001: Multi-agent pipeline with separation of duties, coordinated via shared session state

Status: accepted (reconstructed from code)

## Context

The system's core promise is donor trust: money must go exactly where the donor intended, through a verifiable chain. A single monolithic agent could discover, offer, and execute payments in one context, which makes prompt injection or simple confusion capable of skipping verification steps. The funding flow has three natural stages with different trust requirements: discovery (who is credible?), contracting (what exactly is being offered?), and execution (did the user consent?).

## Options considered

1. **Single agent** with all tools (find, save choice, create cart, pay) in one context — simplest, but one prompt injection or hallucinated tool call could move from discovery to payment with no structural barrier.
2. **Multi-agent with direct agent-to-agent calls** — agents invoke each other; tighter control flow but couples agents and duplicates routing logic.
3. **Multi-agent pipeline on Google ADK** (chosen) — a root conversational agent (`AfaraTechAdvisor`) delegating to a Finding Agent and a `SequentialAgent` pipeline (Merchant → Credentials), with all data flowing through ADK session state.

## Decision

Use a pipeline of specialist agents on Google ADK, one per funding stage, each with exactly one or two narrow tools and explicit "boundaries" text in its instruction (e.g., the Finding Agent "does NOT process payments", the Merchant Agent "does NOT see the user's payment methods"). Agents never call each other; the mandate chain (`intent_mandate` → `cart_mandate` → `payment_mandate`) is passed exclusively through `tool_context.state`, and each stage's tool fails loudly if its predecessor's mandate is missing.

## Consequences

- **Positive**: structural separation of duties — an agent that literally lacks payment tools cannot process payments; each stage re-validates the previous mandate (including expiry), producing an auditable chain; each agent's instruction stays small and focused, improving LLM reliability.
- **Positive**: the pipeline order is enforced by ADK's `SequentialAgent`, not by prompt discipline.
- **Negative**: the boundaries are largely *prompt-level* policy — the tool functions themselves are importable and callable by any agent that registers them, so the isolation depends on tool registration choices.
- **Negative**: state-mediated coordination makes the flow harder to follow (state keys are an implicit contract between tools) and the session state must survive across all agent handoffs.
