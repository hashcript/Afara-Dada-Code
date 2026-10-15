---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "README.md: mission statement (verify and aggregate credible female tech empowerment organisations, let donors fund them, process donations securely) and Quick Start (Google Cloud, GOOGLE_API_KEY in .env)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: root orchestrator AfaraTechAdvisor with the two-phase workflow (discovery, then FundingProcessingPipeline)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py and tools/femtechorgs_tools.py: region search, donation validation, IntentMandate creation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/merchant_agent/agent.py and tools/merchant_tools.py: CartMandate creation, 15-minute expiry, simulated signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py and tools/payment_tools.py: consent prompt, PaymentMandate, simulated transfer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py: in-code directory of 5 vetted initiatives in 3 regions"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py: open-web Google Search 'before' demo agent"
    - "requirements.txt: google-adk 1.17.0, google-cloud-aiplatform[adk,agent-engines], AP2 from git main, google-genai, python-dotenv"
  guesses:
    - "The system is a demo/prototype; payments and signatures are intentionally simulated rather than unfinished production features (see Q-02)"
    - "The donor talks to the root agent through the ADK developer tooling (adk web / adk run) or Vertex AI Agent Engine; no UI or API code exists in the repo (see Q-05)"
    - "Only organisations in the vetted directory are meant to be fundable, although the code does not enforce it (see Q-01)"
---

# Afara Dada Code – Requirements (reconstructed)

Afara Dada Code is a conversational, multi-agent donation advisor built on Google ADK and Gemini. It helps a
donor find vetted African female tech empowerment organisations and then runs a simulated AP2
(Agent Payments Protocol) payment flow. That flow makes three mandates in turn: Intent, then Cart, then Payment.
There is no UI, API server, database or real payment integration in the repository.

Paths below are relative to `afara-dada-code-agents/femtech_empowerment_funding_advisor/` unless stated.

## Functional requirements

| ID | Requirement | Where in code |
|----|-------------|---------------|
| R-01 | A donor talks in natural language to one root agent, "Afara Tech" (`AfaraTechAdvisor`), which runs the conversation in two phases: discovery, then secure execution. | `agent.py:26-88` |
| R-02 | When the donor shows interest in supporting women in tech or Africa, the root agent hands off to `finding_agent`. It moves to the funding pipeline only after an IntentMandate exists, which it detects from the text "IntentMandate created" or "Intent ID: fund_xxx". | `agent.py:35-64` |
| R-03 | The system looks up vetted initiatives by region from a trusted directory, not the open web. The regions are `pan-africa`, `east-africa` and `global-diaspora`, and `africa` returns all of them. | `finding_agent/agent.py:20-23`, `tools/femtechorgs_tools.py:18-50`, `data/femtech_programs.py:6-76` |
| R-04 | Each initiative is shown with its name, HQ, verification source, rating, efficiency (% of funds that go to programmes), impact metrics and mission. | `tools/femtechorgs_tools.py:157-182` |
| R-05 | An unknown region returns a `not_found` status with a friendly message. | `tools/femtechorgs_tools.py:33-38` |
| R-06 | The donor can ask follow-up questions over several turns before choosing an organisation and an amount. | `agent.py:61-63`, `finding_agent/agent.py:25-28` |
| R-07 | When the donor picks an organisation and amount, the system checks that the name is not empty and that 0 < amount ≤ USD 1,000,000. | `tools/femtechorgs_tools.py:53-76` |
| R-08 | A valid choice produces an AP2 `IntentMandate` (cart confirmation required, not refundable, 1-hour expiry, USD) with an `intent_id` of the form `fund_<REGID>_<epoch>`. It is stored in session state as `intent_mandate`. | `tools/femtechorgs_tools.py:79-154` |
| R-09 | The `FundingProcessingPipeline` runs `merchant_agent`, then `CredentialsProvider`, in a fixed order. | `agent.py:14-21` |
| R-10 | The merchant agent reads `intent_mandate`, validates it against the AP2 model, and refuses to continue if it is missing, malformed or expired. | `tools/merchant_tools.py:26-51`, `tools/merchant_tools.py:89-109` |
| R-11 | The merchant agent builds an AP2 `CartMandate`. It wraps a W3C `PaymentRequest` (CARD via visa/mastercard, debit/credit, USD total), has a 15-minute `cart_expiry` and a `cart_<hash>` ID, and is stored in state as `cart_mandate`. | `tools/merchant_tools.py:111-175` |
| R-12 | The CartMandate carries a `merchant_authorization` "signature": `SIG_` followed by the first 16 hex characters of a SHA-256 hash of the canonical cart-contents JSON. | `tools/merchant_tools.py:54-74` |
| R-13 | Before paying, the credentials provider must show the amount and recipient and ask for explicit confirmation. It must not pay if the donor declines. This rule exists only in the prompt. | `credentials_provider/agent.py:33-39` |
| R-14 | The payment tool reads `cart_mandate`, validates it, and refuses to continue if it is missing, malformed or expired. | `tools/payment_tools.py:18-45`, `tools/payment_tools.py:104-121` |
| R-15 | The payment tool creates an AP2 `PaymentMandate` linked to the cart, with a simulated card token and the fields `user_consent` and `consent_timestamp`. It stores the mandate in state as `payment_mandate`. | `tools/payment_tools.py:48-92`, `tools/payment_tools.py:146` |
| R-16 | The system simulates the fund transfer. It writes a `payment_result` (a `txn_<hash>` ID, status `completed`, amount, currency, recipient, `simulation: true`) and tells the donor the transaction ID. | `tools/payment_tools.py:133-157`, `credentials_provider/agent.py:48-53` |
| R-17 | A separate "Naive Agent" uses Google Search on the open web to show the unverified "before" situation. | `Naive_Agent/agent.py:1-29` |
| R-18 | A developer script runs the merchant agent alone against a pre-seeded IntentMandate and prints the CartMandate it produces. | `../scripts/test_merchant.py:22-136` |
| R-19 | A mock credentials provider that skips confirmation exists for automated tests. It is not wired into any flow and points at a non-existent `charity_advisor` package. | `credentials_provider/agent_mock.py:1-32` |

## Non-functional requirements

| ID | Requirement | Where in code |
|----|-------------|---------------|
| R-20 | All agents use the Gemini model `gemini-3-pro-preview`. | `agent.py:28`, `finding_agent/agent.py:13`, `merchant_agent/agent.py:12`, `credentials_provider/agent.py:13`, `Naive_Agent/agent.py:19` |
| R-21 | Each agent has a narrow role with explicit "IMPORTANT BOUNDARIES": the finding agent never handles payment, and the merchant never sees credentials. | `finding_agent/agent.py:46-58`, `merchant_agent/agent.py:41-47`, `credentials_provider/agent.py:55-60` |
| R-22 | Agents pass state only through ADK session state keys (`intent_mandate`, `cart_mandate`, `payment_mandate`, `payment_result`) as JSON-serialisable dicts. | `tools/femtechorgs_tools.py:145`, `tools/merchant_tools.py:165`, `tools/payment_tools.py:146-147` |
| R-23 | Each mandate expires (intent after 1 hour, cart after 15 minutes), and expiry is checked before the next step. | `tools/femtechorgs_tools.py:86`, `tools/merchant_tools.py:120`, `tools/payment_tools.py:117-121` |
| R-24 | Mandate data structures follow the AP2 Pydantic types and the W3C PaymentRequest types. | `tools/merchant_tools.py:13-21`, `tools/payment_tools.py:12-13`, `requirements.txt:3` |
| R-25 | Tools log their key actions (searches, validation failures, created IDs) through Python `logging`. | `tools/*.py` (`logger.info/error`) |
| R-26 | Credentials (`GOOGLE_API_KEY`) come from a git-ignored `.env` file. The target platform is Google Cloud (Vertex AI, Secret Manager and Cloud Trace APIs enabled in the README). | `README.md:38-44`, `.gitignore:1-2`, `../scripts/test_merchant.py:11-13` |
| R-27 | The code is installable as the Python package `afara_dada_code_agents` 0.1.0 and needs Python 3.9 or later (it uses PEP 585 `tuple[...]` hints). | `setup.py:1-7`, `tools/merchant_tools.py:26` |
