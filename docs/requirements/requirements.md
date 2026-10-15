---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py — root orchestrator with two-phase (discovery → execution) instruction and FundingProcessingPipeline SequentialAgent"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py — find_tech_initiatives, save_user_choice, _create_intent_mandate, _validate_donation_data"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py — create_cart_mandate, _validate_intent_expiry, _generate_merchant_signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py — create_payment_mandate, _validate_cart_expiry, _create_payment_mandate, simulated transfer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py — curated database of 5 organizations across 3 regions"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py — open-web baseline agent"
    - "requirements.txt / setup.py / README.md — ADK, AP2, Vertex AI Agent Engine dependencies and Google Cloud setup"
  guesses:
    - "The system is currently a demo/prototype: all payment and signature logic is explicitly simulated (see R-24); production requirements are inferred from README intent only (see Q-01)."
    - "No user authentication or persistence requirements are visible in code; assumed out of scope for the demo stage (see Q-07)."
---

# Requirements — Afara Dada Code

## Functional requirements

- **R-01** — Present donors with vetted African female tech empowerment organizations filtered by region, from a curated in-code dataset. (`tools/femtechorgs_tools.py:find_tech_initiatives`, `data/femtech_programs.py:get_initiatives_by_region`)
- **R-02** — For each organization, display trust and impact metrics: HQ, mission, impact metrics, rating, program-efficiency percentage, and verification source. (`tools/femtechorgs_tools.py:_format_initiative_display`)
- **R-03** — Resolve a region query of "africa" to the union of all regions; unknown regions return no results. (`data/femtech_programs.py:70-75`)
- **R-04** — Conduct a two-phase conversation: Phase 1 discovery/selection, Phase 2 secure execution, transitioning only after a valid IntentMandate exists. (`agent.py:31-64` root instruction)
- **R-05** — Accept a donor's selection (organization name + USD amount), validating that the name is non-empty, the amount is positive and at most $1,000,000. (`tools/femtechorgs_tools.py:_validate_donation_data`)
- **R-06** — On a valid selection, create an AP2 `IntentMandate` with a 1-hour expiry and a unique intent ID, and store it in shared session state. (`tools/femtechorgs_tools.py:_create_intent_mandate`, `save_user_choice`)
- **R-07** — Pass credentials between agents through ADK session state keys `intent_mandate`, `cart_mandate`, `payment_mandate`, `payment_result`. (`femtechorgs_tools.py:145`, `merchant_tools.py:165`, `payment_tools.py:146-147`)
- **R-08** — Create a W3C PaymentRequest-compliant `CartMandate` (organization's signed offer, 15-minute expiry, card payment methods, USD total) from a valid IntentMandate. (`tools/merchant_tools.py:create_cart_mandate`)
- **R-09** — Refuse CartMandate creation when no IntentMandate exists in state or the intent has expired. (`merchant_tools.py:90-109`)
- **R-10** — Attach a merchant signature (SHA-256 over canonical JSON of cart contents) to every CartMandate. (`merchant_tools.py:_generate_merchant_signature`)
- **R-11** — Before executing a transfer, present the funding details to the donor and require an explicit conversational confirmation; do not proceed on "no"/"cancel". (`credentials_provider/agent.py:33-39` instruction)
- **R-12** — On confirmation, create an AP2 `PaymentMandate` linking back to the CartMandate, recording consent status and timestamp. (`tools/payment_tools.py:_create_payment_mandate`)
- **R-13** — Refuse payment when no CartMandate exists in state or the cart has expired. (`payment_tools.py:106-121`)
- **R-14** — Simulate the fund transfer, generate a transaction ID, and report amount, currency, recipient and transaction ID back to the donor. (`payment_tools.py:134-156`)
- **R-15** — Orchestrate the merchant and payment steps strictly in sequence after the donor's selection, via an ADK `SequentialAgent`. (`agent.py:14-21` FundingProcessingPipeline)
- **R-16** — Provide a contrast "naive" agent that researches initiatives via open-web Google Search, to demonstrate the value of the curated trust layer. (`Naive_Agent/agent.py`)
- **R-17** — Provide a mock payment agent that auto-approves without confirmation, for automated testing. (`credentials_provider/agent_mock.py`)
- **R-18** — Allow the Merchant Agent to be exercised standalone against a simulated IntentMandate seeded into an in-memory session. (`scripts/test_merchant.py`)

## Non-functional requirements

- **R-19** — All conversational agents run on Google ADK with the `gemini-3-pro-preview` model. (every `agent.py`, model parameter)
- **R-20** — Mandate structures conform to the AP2 protocol types (`IntentMandate`, `CartMandate`, `PaymentMandate`) and W3C PaymentRequest models from the AP2 library. (`requirements.txt` AP2 dep, `merchant_tools.py:13-21`)
- **R-21** — Target deployment is Google Cloud with Vertex AI / Agent Engine, AI Platform, Secret Manager and Cloud Trace enabled. (`requirements.txt` google-cloud-aiplatform[adk,agent-engines], `README.md:39-40`)
- **R-22** — The Google API key is supplied via a `.env` file which is git-ignored. (`README.md:42-43`, `.gitignore`)
- **R-23** — Every tool invocation is logged via Python `logging` with an info/error record. (all three tool modules)
- **R-24** — No real money moves: the payment result is explicitly marked `"simulation": True`, and signatures are hash-based simulations. (`payment_tools.py:142`, `merchant_tools.py:54-74`)
- **R-25** — Intent and cart credentials are time-limited (1 hour and 15 minutes respectively) and re-validated at each handoff. (`femtechorgs_tools.py:86`, `merchant_tools.py:120`, validated in both later tools)
- **R-26** — The agent package is installable as `afara_dada_code_agents` via pip. (`setup.py`)
