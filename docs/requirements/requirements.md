---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py — root orchestrator and sequential funding pipeline"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py — discovery agent instruction"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/merchant_agent/agent.py — contract agent instruction"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py — payment agent instruction"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/*.py — the tool implementations backing every requirement"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py — curated initiative dataset"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py — open-web comparison agent"
    - "README.md — product framing and quick start"
  guesses:
    - "The system is a demo/prototype, not a production payment system (all payments are simulated; see Q-01)"
    - "The intended deployment target is Google ADK locally or Vertex AI Agent Engine (README enables aiplatform/secretmanager; see Q-06)"
---

# Requirements — Afara Dada Code

Afara Dada Code is an AI agent that helps donors (individuals, corporates, DAOs) discover and fund verified African female tech empowerment organizations. It is built as a multi-agent system on Google ADK, using the AP2 (google-agentic-commerce) mandate protocol to structure the funding flow as a chain of three verifiable credentials. All payment execution is simulated in the current code.

## Functional requirements

- R-01: The system shall act as a conversational advisor that orchestrates a two-phase workflow — discovery/trust, then secure execution — via a root agent (`AfaraTechAdvisor`). (`agent.py:26-88`)
- R-02: The system shall let donors discover initiatives by African region via the `find_tech_initiatives` tool, restricted to a curated dataset (no open web search in the main flow). (`tools/femtechorgs_tools.py:18-50`, `finding_agent/agent.py:20-24`)
- R-03: The system shall present trust and impact metrics for each initiative: name, HQ, verification source, rating, efficiency, impact metrics, mission. (`tools/femtechorgs_tools.py:157-181`, `data/femtech_programs.py`)
- R-04: When a donor selects an organization and amount, the system shall record the choice and create an AP2 `IntentMandate` (ID `fund_<NAME>_<unix-ts>`, 1-hour expiry) in shared session state. (`tools/femtechorgs_tools.py:79-154`)
- R-05: The system shall validate donation data before creating an intent: non-empty organization name and amount in (0, 1,000,000] USD. (`tools/femtechorgs_tools.py:53-76`)
- R-06: The system shall convert a valid, unexpired IntentMandate into a W3C PaymentRequest-compliant, signed `CartMandate` (15-minute expiry, hash-based organization signature) via the `create_cart_mandate` tool. (`tools/merchant_tools.py:77-175`)
- R-07: The system shall reject CartMandate creation when no IntentMandate exists in state or the intent has expired. (`tools/merchant_tools.py:26-51, 89-109`)
- R-08: Before executing payment, the system shall present funding details and obtain the donor's explicit confirmation ("yes"/"proceed") in a two-turn conversational pattern. (`credentials_provider/agent.py:33-39`)
- R-09: Upon confirmation, the system shall create an AP2 `PaymentMandate`, simulate the fund transfer, and return a transaction ID (`txn_<hash>`). (`tools/payment_tools.py:95-157`)
- R-10: The system shall execute the merchant and credentials agents strictly in sequence after an initiative is selected (ADK `SequentialAgent`). (`agent.py:14-21`)
- R-11: The system shall keep discovery and payment strictly separated: the finding agent must not process payments or ask for card details; the merchant agent must not see payment credentials; the credentials provider must not discover initiatives. (`finding_agent/agent.py:46-58`, `merchant_agent/agent.py:41-47`, `credentials_provider/agent.py:55-61`)
- R-12: The system shall pass the mandate chain (intent → cart → payment) between agents exclusively through ADK shared session state (`tool_context.state`). (`tools/femtechorgs_tools.py:145`, `tools/merchant_tools.py:165`, `tools/payment_tools.py:146-147`)
- R-13: The system shall provide a "Naive Agent" baseline that researches initiatives via open Google Search, to demonstrate the value of the trust layer. (`Naive_Agent/agent.py`)
- R-14: The system shall provide an automated test harness that simulates a Finding Agent's IntentMandate in state and drives the Merchant Agent end to end. (`scripts/test_merchant.py`)

## Non-functional requirements

- R-15: Trustworthiness — the main flow must only surface curated, verified organizations with an explicit verification source, never open-web results. (`data/femtech_programs.py`, `finding_agent/agent.py:22-23`)
- R-16: Auditability — every funding shall be traceable through the three-credential chain (IntentMandate, CartMandate, PaymentMandate), each with its own ID and timestamp. (`credentials_provider/agent.py:69-73`, all tool files)
- R-17: Protocol compliance — mandate structures shall follow the AP2 types and W3C PaymentRequest standard so a real payment processor can replace the simulation. (`tools/merchant_tools.py:13-21`, `tools/payment_tools.py:12-13`)
- R-18: Expiry safety — intent (1h) and cart (15min) offers shall expire and be re-validated at each stage, so stale authorizations cannot be executed. (`tools/femtechorgs_tools.py:86`, `tools/merchant_tools.py:120`, `tools/payment_tools.py:18-45`)
- R-19: Scope of currency — donations are denominated in USD only. (`tools/femtechorgs_tools.py:110`, `tools/merchant_tools.py:134`)
- R-20: Demo scope — payment execution is simulated (`"simulation": True` in the payment result); no real money moves. (`tools/payment_tools.py:135-143`)
