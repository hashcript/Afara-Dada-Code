---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "README.md: problem statement (funding gap for African female-led tech), vision of verifying organisations and letting donors fund them, quick-start setup"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: root orchestrator AfaraTechAdvisor and FundingProcessingPipeline (SequentialAgent)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py and tools/femtechorgs_tools.py: discovery tool, donation validation, IntentMandate creation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/merchant_agent/agent.py and tools/merchant_tools.py: CartMandate creation, expiry check, simulated signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py and tools/payment_tools.py: consent prompt, PaymentMandate, simulated transfer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py: hard-coded registry of 5 vetted organisations in 3 regions"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py: open-web google_search baseline agent"
    - "requirements.txt, setup.py, .gitignore, afara-dada-code-agents/scripts/test_merchant.py: dependencies, packaging, config, manual test harness"
  guesses:
    - "The product is currently a demo/hackathon prototype; payments are intentionally simulated rather than a missing feature (see Q-01)"
    - "Explicit donor consent is intended to be a hard requirement even though only the LLM prompt enforces it (see Q-02)"
    - "Only organisations in the vetted registry are meant to be fundable, although the code accepts any name (see Q-03)"
    - "README's 'real-time updates on how funds are used' is a vision item, not a current requirement (see Q-09)"
---

# Requirements: Afara Dada Code (Femtech Empowerment Funding Advisor)

Afara Dada Code is a conversational, multi-agent advisor built on Google ADK and Gemini. It helps donors (individuals, corporates, DAOs) find vetted African female tech-empowerment organisations and fund them through an AP2 (Agent Payments Protocol) credential chain: IntentMandate, then CartMandate, then PaymentMandate. The payment step is **simulated**: no real money moves.

Paths are relative to `afara-dada-code-agents/femtech_empowerment_funding_advisor/` unless they start with a top-level name.

## Functional requirements

| ID | Requirement | Where in the code |
|----|-------------|-------------------|
| R-01 | A root conversational agent ("AfaraTechAdvisor" / "Afara Tech") talks to the donor and runs two phases: Discovery & Trust, then Secure Execution. | `agent.py:26-88` |
| R-02 | The root agent sends discovery to `finding_agent`. It moves to the funding pipeline only once an IntentMandate exists, which it detects from text such as "IntentMandate created" or "Intent ID: fund_xxx". | `agent.py:35-64` |
| R-03 | The system lists vetted initiatives for a region key (`pan-africa`, `east-africa`, `global-diaspora`). The value `africa` returns every initiative. Matching ignores case. | `data/femtech_programs.py:6-76`, `tools/femtechorgs_tools.py:18-50` |
| R-04 | An unknown region returns `status: not_found` and a readable message, not an error. | `tools/femtechorgs_tools.py:33-38` |
| R-05 | Each initiative is shown with name, HQ, verification source, rating out of 5, efficiency as a percentage of funds going to programmes, impact metrics and mission. Raw records are returned alongside. | `tools/femtechorgs_tools.py:42-50,157-182` |
| R-06 | The Finding Agent uses only the trusted registry tool. It must not search the open web or ask for card details. | `finding_agent/agent.py:20-51` |
| R-07 | Once the donor picks an organisation and a USD amount, `save_user_choice` records the choice as an AP2 IntentMandate in session state (`intent_mandate`). | `tools/femtechorgs_tools.py:116-154` |
| R-08 | A donation is rejected if the organisation name is empty or blank, the amount is not above 0, or the amount is above USD 1,000,000. | `tools/femtechorgs_tools.py:53-76` |
| R-09 | An IntentMandate expires 1 hour after creation. Its ID is `fund_<first 10 alphanumerics of org name, uppercased>_<epoch seconds>` and its currency is fixed to USD. | `tools/femtechorgs_tools.py:79-113` |
| R-10 | The funding pipeline runs the Merchant Agent and then the Credentials Provider, in that order. | `agent.py:14-21` |
| R-11 | `create_cart_mandate` refuses to build a cart if the IntentMandate is missing, fails AP2 schema validation or has expired. | `tools/merchant_tools.py:26-51,89-109` |
| R-12 | The CartMandate wraps a W3C PaymentRequest: method `CARD` (visa or mastercard, debit or credit), one display item and a total in USD, and no shipping. It is saved to state as `cart_mandate`. | `tools/merchant_tools.py:116-165` |
| R-13 | A CartMandate expires 15 minutes after creation. Its ID is `cart_<12 hex of SHA-256(org name + timestamp)>`. | `tools/merchant_tools.py:117-120` |
| R-14 | The CartMandate carries a "merchant authorization" of the form `SIG_<first 16 hex of SHA-256 of canonical JSON of the cart contents>`. This is a simulated organisation signature. | `tools/merchant_tools.py:54-74,152-159` |
| R-15 | The Credentials Provider shows the funding details and asks the donor for explicit confirmation before it calls `create_payment_mandate`. If the donor says "no" or "cancel" the call must not happen. | `credentials_provider/agent.py:33-39,55-60` |
| R-16 | `create_payment_mandate` refuses to proceed if the CartMandate is missing, fails schema validation or has expired. | `tools/payment_tools.py:18-45,104-121` |
| R-17 | A PaymentMandate links to the cart ID, total and organisation. It records `user_consent`, `consent_timestamp` and `agent_present`, and is saved to state as `payment_mandate`. | `tools/payment_tools.py:48-92,146` |
| R-18 | The transfer is simulated. A `payment_result` with `transaction_id` `txn_<16 hex>`, status `completed`, amount, currency, recipient, timestamp and `simulation: true` is written to state. | `tools/payment_tools.py:133-147` |
| R-19 | After the pipeline finishes, the root agent summarises the transaction for the donor, including the Transaction ID. | `agent.py:58,76` |
| R-20 | A separate "Naive Agent" answers the same questions from open-web Google Search. It is the unverified "before" baseline. | `Naive_Agent/agent.py:1-29` |
| R-21 | Each specialist agent package exports `root_agent`, so the agent can run on its own (for example from the merchant test script). | `finding_agent/__init__.py`, `merchant_agent/__init__.py`, `credentials_provider/__init__.py`, `scripts/test_merchant.py:19` |
| R-22 | A mock Credentials Provider that skips confirmation is provided for automated testing. Its import path is currently broken. | `credentials_provider/agent_mock.py:1-32` |

## Non-functional requirements

| ID | Requirement | Where in the code |
|----|-------------|-------------------|
| R-23 | Every LLM agent uses model `gemini-3-pro-preview` on Google ADK `1.17.0`. | `agent.py:28`, `finding_agent/agent.py:13`, `merchant_agent/agent.py:12`, `credentials_provider/agent.py:13`, `Naive_Agent/agent.py:19`, `requirements.txt:1` |
| R-24 | Agent roles are kept apart for least privilege. Finding does no payments. Merchant never sees payment credentials. Credentials Provider does no discovery and creates no offers. | `finding_agent/agent.py:46-51`, `merchant_agent/agent.py:41-47`, `credentials_provider/agent.py:55-60` |
| R-25 | Credentials are configured in a `.env` file (`GOOGLE_API_KEY`), which is git-ignored. | `README.md:42-43`, `.gitignore:1-2`, `scripts/test_merchant.py:11-13` |
| R-26 | Timestamps are UTC ISO-8601. Expiry parsing accepts both the `Z` and `+00:00` suffixes. | `tools/merchant_tools.py:39`, `tools/payment_tools.py:33` |
| R-27 | Auditability: the three AP2 credentials and the payment result stay in session state and form a chain of trust. | `credentials_provider/agent.py:69-74`, `tools/*.py` state writes |
| R-28 | Every tool call and every validation failure is logged with Python `logging`. | `tools/femtechorgs_tools.py:14,28,133`, `tools/merchant_tools.py:23`, `tools/payment_tools.py:15` |
| R-29 | Tool functions are `async` and get shared state through the ADK `tool_context`. | `tools/femtechorgs_tools.py:18,116`, `tools/merchant_tools.py:77`, `tools/payment_tools.py:95` |
| R-30 | The code is packaged as Python package `afara_dada_code_agents` 0.1.0 (setuptools) under the MIT license. AP2 is installed from GitHub `@main`. | `afara-dada-code-agents/setup.py`, `LICENSE`, `requirements.txt:3` |
| R-31 | State lasts only for the session. No database or durable store exists: the registry is in code and the test harness uses `InMemorySessionService`. | `data/femtech_programs.py`, `scripts/test_merchant.py:26` |
