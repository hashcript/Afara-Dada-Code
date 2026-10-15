---
blueprint:
  type: adr
  id: art_0001-google-adk-multi-agent-orchestration
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: LLM root Agent with sub_agents [finding_agent, SequentialAgent(merchant_agent, credentials_provider)]"
    - "Each agent.py: separate Agent with its own instruction, 'IMPORTANT BOUNDARIES' and one or two FunctionTools"
    - "requirements.txt: google-adk==1.17.0, google-genai==1.52.0, google-cloud-aiplatform[adk,agent-engines]"
    - "README.md: Google AI badge, gcloud setup for aiplatform"
  guesses:
    - "Google ADK and Gemini were chosen partly because of the Google ecosystem or event context (README badge, Google Cloud setup), not after a formal comparison (see Q-05)"
---

# ADR 0001 – Google ADK multi-agent hierarchy with an LLM router and a fixed payment pipeline

Status: accepted (reconstructed from code)

## Context

The product has to hold an open-ended, trust-building conversation with a donor: discovery, comparison and
questions. It then has to run a strict, ordered payment procedure. The two halves have different needs. Discovery
is flexible and takes several turns. Execution is ordered and must respect role boundaries (the merchant never
sees credentials, the finder never pays). The project targets Google Cloud and Gemini.

## Options considered

1. **One LLM agent with every tool.** This is the simplest option, but role separation would rest entirely on one
   prompt, and the model could call payment tools during discovery.
2. **Plain code orchestration (a state machine) calling an LLM only for chat.** The order would be deterministic,
   but you lose the agentic, conversational handoff the demo is trying to show.
3. **A Google ADK agent hierarchy (chosen).** An LLM root (`AfaraTechAdvisor`) routes between a conversational
   `finding_agent` and a `SequentialAgent` (`FundingProcessingPipeline`) that always runs `merchant_agent` and
   then `CredentialsProvider`. Each sub-agent owns only the tools for its role.
4. Another framework, such as LangGraph or CrewAI. None of these appear in the code.

## Decision

Use Google ADK (1.17.0) with Gemini `gemini-3-pro-preview` for every agent. The structure is:

- one LLM root agent that hands off by `transfer_to_agent`, using the sub-agents' descriptions and a two-phase
  instruction;
- one specialist LLM agent for each AP2 role (Finding, Merchant, Credentials Provider), each holding only its own
  `FunctionTool`s;
- a `SequentialAgent` that fixes the order of the execution phase;
- each sub-package exports `root_agent`, so it can be run alone through ADK tooling.

## Consequences

- ✅ Each agent can call only its own tools, which gives clear separation of duties.
- ✅ The pipeline order (cart before payment) is deterministic, not left to the model.
- ✅ The design fits Vertex AI Agent Engine (`agent-engines` extra) and `adk web` for demos.
- ⚠️ When Phase 1 hands over to Phase 2 is still an LLM decision. It relies on spotting text such as
  "IntentMandate created" (`agent.py:46-48`), not on checking `state["intent_mandate"]`.
- ⚠️ Running a conversational, two-turn consent step inside a `SequentialAgent` relies on how ADK routes the next
  user turn. That behaviour is implicit and untested (see Q-03).
- ⚠️ Four Gemini calls or more per flow on a *preview* model. Latency, cost and model availability are outside
  the project's control.
- ⚠️ Lock-in to the ADK and Gemini APIs (`tool_context.state`, `FunctionTool`, `SequentialAgent`).
