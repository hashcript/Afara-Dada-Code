---
blueprint:
  type: adr
  id: art_0001-multi-agent-orchestration-with-google-adk
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
      - { id: art_requirements, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:5,14-21,26-88: LlmAgent root with sub_agents [finding_agent, SequentialAgent pipeline]"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py, merchant_agent/agent.py, credentials_provider/agent.py: one agent per role, each with only its own tools"
    - "requirements.txt:1,2,5: google-adk==1.17.0, google-cloud-aiplatform[adk,agent-engines], google-genai==1.52.0"
    - "All agent.py files: model gemini-3-pro-preview"
  guesses:
    - "ADK and Gemini were chosen because the project targets Google Cloud / Google AI (README badge, gcloud setup) rather than after comparing frameworks (see Q-10)"
---

# ADR 0001: Split the advisor into role-scoped ADK agents with an LLM root and a sequential payment pipeline

Status: accepted (reconstructed from code)

## Context

The product has to: hold an open-ended conversation with a donor about organisations; turn the donor's decision into a structured funding intent; build an offer; and run a payment that needs explicit consent. These steps need different abilities and different trust levels. The step that moves money should not also be the one doing free-form discovery. The project is built on Google's stack (README badge, `gcloud` setup, `google-cloud-aiplatform[adk,agent-engines]`).

## Options considered

1. **One LLM agent with all tools.** Simplest, but any prompt could reach the payment tool, and one prompt would have to explain every phase.
2. **A hand-written state machine or web backend that calls an LLM only for chat.** Strong control over the flow, but more code and not "agentic", which the README presents as the core idea (README.md:15).
3. **Google ADK multi-agent tree** *(chosen)*. An LLM root that decides when to hand off, a role-specific LlmAgent for each phase, and a `SequentialAgent` that fixes the order Merchant → Credentials Provider.
4. Another agent framework (LangGraph, CrewAI, etc.). Nothing in the repo suggests these were considered.

## Decision

- Use **Google ADK 1.17.0**, with **Gemini `gemini-3-pro-preview`** for every agent.
- The root `AfaraTechAdvisor` (`agent.py:26-88`) has no tools. It routes to `finding_agent` and `FundingProcessingPipeline` using LLM-driven agent transfer, guided by a two-phase instruction.
- `FundingProcessingPipeline` is a `SequentialAgent` over `merchant_agent` and then `credentials_provider` (`agent.py:14-21`).
- **Tools are scoped per agent.** Only the finding agent can query the registry or create intents. Only the merchant can create carts. Only the credentials provider can create payments. Role limits are also stated in each prompt.
- Each sub-package exports `root_agent` so the agent can be run and tested alone (`*/__init__.py`, `scripts/test_merchant.py`).

## Consequences

- ✅ Separation of duties is partly enforced by structure: the discovery agent cannot call the payment tool.
- ✅ Each agent's prompt stays focused, and agents can be tested one at a time.
- ⚠️ When to switch phases is decided by the LLM, based on text such as "IntentMandate created" (`agent.py:46-48`). A model mistake can skip or repeat a phase. The tools' checks (intent present, not expired) are the only deterministic guard.
- ⚠️ A SequentialAgent runs its sub-agents back to back. The credentials provider's two-turn consent needs a pause for user input in the middle of the sequence. How control comes back on the next turn is not explicit and may re-run the merchant step (NFR B-09).
- ⚠️ Four LLM agents, each running a large preview model, means several Gemini calls per turn. This raises latency and cost, and the system depends on a preview model being available (NFR section).
- ⚠️ The code is tied to ADK's APIs (`tool_context.state`, `FunctionTool`, agent loading by `root_agent`) and to Gemini.
