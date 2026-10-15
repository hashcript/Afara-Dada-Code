---
blueprint:
  type: adr
  id: art_0001-adk-multi-agent-orchestration
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: root Agent with sub_agents [finding_agent, SequentialAgent(merchant_agent, credentials_provider)]"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/*/agent.py: four LlmAgents, all model gemini-3-pro-preview, each with narrow IMPORTANT BOUNDARIES"
    - "requirements.txt: google-adk==1.17.0, google-genai==1.52.0"
    - "README.md:7: Google AI badge; README.md:38-40 Google Cloud setup"
  guesses:
    - "Google ADK + Gemini were chosen because the project targets the Google AP2/ADK ecosystem (likely a Google-sponsored hackathon or codelab) rather than after a framework comparison (see Q-05)"
    - "Splitting into separate agents was driven by AP2's role model (shopping agent / merchant / credentials provider) and least privilege (see Q-02)"
---

# ADR 0001: Hierarchical multi-agent design on Google ADK and Gemini

Status: accepted (reconstructed from code)

## Context

The advisor has to hold an open-ended conversation (discovery, comparing organisations, building trust) and then run a strict, ordered transaction (offer, consent, payment). The two halves need different behaviour. Discovery should be flexible and take several turns. Execution should be deterministic and limited to the right roles. AP2 already defines separate roles for the user-facing agent, the merchant and the credentials provider, and README and `requirements.txt` show the project is built in the Google ecosystem.

## Options considered

1. **A single LLM agent with every tool.** Simplest. But one prompt would hold both discovery and payment power, so nothing structural keeps the agent from paying before an intent exists.
2. **Hierarchical ADK agents: an LLM root that delegates, plus a SequentialAgent for execution.** Each agent sees only its own tools. Execution order is fixed by the framework.
3. **A hand-written state machine around plain LLM calls**, or another framework such as LangGraph. More control, but more code, and no built-in fit with AP2 or Gemini.

## Decision

Use **Google ADK 1.17.0** with **Gemini `gemini-3-pro-preview`** for every agent, arranged as:

- `AfaraTechAdvisor` (root LlmAgent): the conversation and the switch between phases, done by LLM delegation (`agent.py:26-88`).
- `finding_agent` (LlmAgent): discovery and the IntentMandate. Its tools are `find_tech_initiatives` and `save_user_choice`.
- `FundingProcessingPipeline` (SequentialAgent): runs `merchant_agent` (CartMandate) and then `CredentialsProvider` (PaymentMandate) in a fixed order.

Every agent's instruction lists hard boundaries ("You do NOT process payments", and so on), and each sub-package exports `root_agent` so it can be tested alone.

## Consequences

- ✅ Tool exposure follows least privilege. Only the Credentials Provider can call `create_payment_mandate`.
- ✅ Merchant runs before payment by framework construction, not by prompt.
- ✅ Each agent can be run and tested on its own (`scripts/test_merchant.py`).
- ⚠️ The move from Phase 1 to Phase 2 is decided by the root LLM from text cues ("IntentMandate created"), so it is not deterministic.
- ⚠️ A `SequentialAgent` cannot pause for user input in the middle. The Credentials Provider's two-turn consent works against this, and the pipeline may run again on the next turn (see NFR T-07).
- ⚠️ Four LLM agents mean several Gemini calls per turn, which adds latency and cost. All of them use a *preview* model hard-coded in five places.
- ⚠️ The system depends on one vendor for both framework and model (Google ADK + Gemini).
