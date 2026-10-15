---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "README.md: product purpose (connect donors to verified African female-tech organisations, agentic donation flow), setup steps and GOOGLE_API_KEY in .env"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: root agent AfaraTechAdvisor, two-phase instruction, FundingProcessingPipeline (SequentialAgent)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py and tools/femtechorgs_tools.py: discovery, validation and IntentMandate creation"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py: hard-coded vetted initiative database by region"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/merchant_agent/agent.py and tools/merchant_tools.py: CartMandate creation, expiry check, simulated signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py and tools/payment_tools.py: consent prompt, PaymentMandate, simulated transfer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py: open-web google_search baseline agent"
    - "afara-dada-code-agents/scripts/test_merchant.py and credentials_provider/agent_mock.py: test harnesses"
    - "requirements.txt and afara-dada-code-agents/setup.py: dependency and packaging constraints"
  guesses:
    - "The system is a demo/prototype; payments and organisation signatures are intentionally simulated rather than a production feature (see Q-01)"
    - "Only organisations in the vetted database are meant to be fundable, although the code accepts any name (see Q-02)"
    - "Donor consent is meant to be a hard gate, although it is only enforced by the LLM prompt (see Q-03)"
    - "The README promise of real-time updates on fund usage is future scope, since no code implements it (see Q-08)"
---

# Requirements: Afara Dada Code (FemTech Empowerment Funding Advisor)

Afara Dada Code is a conversational, multi-agent donation advisor built on Google ADK and Gemini. It helps a donor
find vetted African female-in-tech organisations, records the donor's choice as an AP2 *IntentMandate*, turns it
into a signed *CartMandate*, and after the donor confirms, creates a *PaymentMandate* and simulates the funds
transfer. A second, stand-alone "Naive" agent shows the unverified open-web approach for contrast.

Paths below are relative to `afara-dada-code-agents/femtech_empowerment_funding_advisor/` unless they start with
`README.md`, `requirements.txt` or `afara-dada-code-agents/`.

## Functional requirements

| ID | Requirement | Where in the code |
|----|-------------|-------------------|
| R-01 | The system provides one conversational entry point, the root agent "AfaraTechAdvisor" ("Afara Tech"), that runs a two-phase workflow: Discovery & Trust, then Secure Execution. | `agent.py:26-88` |
| R-02 | When a donor shows interest in supporting women in tech or mentions Africa, the root agent hands the conversation to `finding_agent`. | `agent.py:35-44` |
| R-03 | The finding agent looks up vetted initiatives by region (`pan-africa`, `east-africa`, `global-diaspora`; `africa` returns all five, matched case-insensitively). Any other region returns `not_found`. | `tools/femtechorgs_tools.py:18-50`, `data/femtech_programs.py:6-76` |
| R-04 | Each initiative is shown with HQ, verification source, rating out of 5, efficiency (% of funds going to programmes), impact metrics and mission. | `tools/femtechorgs_tools.py:157-182` |
| R-05 | The finding agent must only use the trusted lookup tool and must not search the open web. | `finding_agent/agent.py:20-23` |
| R-06 | The finding agent stays in the conversation over several turns, answering questions until the donor picks an organisation and an amount. | `agent.py:61-63`, `finding_agent/agent.py:25-31` |
| R-07 | When the donor chooses, `save_user_choice` checks that the organisation name is not empty and that 0 < amount ≤ 1,000,000 USD, and returns an error otherwise. | `tools/femtechorgs_tools.py:53-76`, `116-139` |
| R-08 | A valid choice creates an AP2 IntentMandate (cart confirmation required, not refundable, expires in 1 hour). It also gets the extra fields `intent_id` = `fund_<REGID>_<epoch>`, `org_name`, `amount` and `currency`=USD, and is saved as session state `intent_mandate`. | `tools/femtechorgs_tools.py:79-113`, `145` |
| R-09 | The finding agent tells the donor the Intent ID and expiry, then hands off. It must not take payments, build carts or ask for card details. | `finding_agent/agent.py:39-51` |
| R-10 | The root agent starts the FundingProcessingPipeline only after a valid IntentMandate exists. This is checked by the LLM spotting "IntentMandate created" / "Intent ID: fund_xxx" in the reply. | `agent.py:46-64` |
| R-11 | The FundingProcessingPipeline runs `merchant_agent` and then `credentials_provider`, one after the other. | `agent.py:14-21` |
| R-12 | The merchant tool reads `intent_mandate` from state. It returns an error if the mandate is missing, has an invalid structure, or has expired. | `tools/merchant_tools.py:26-51`, `89-109` |
| R-13 | The merchant tool builds a CartMandate in W3C PaymentRequest form for the first merchant in the intent: method CARD (visa/mastercard, debit/credit), USD total, `cart_<hash12>` ID, `order_<cart_id>` details ID, expiry 15 minutes, no shipping. | `tools/merchant_tools.py:111-150` |
| R-14 | The merchant tool "signs" the cart as `SIG_<first 16 hex of SHA-256>` over its canonical JSON contents, and saves the result as session state `cart_mandate`. | `tools/merchant_tools.py:54-74`, `152-165` |
| R-15 | The merchant agent tells the donor the Cart ID and 15-minute expiry, then hands off to the payment step. | `merchant_agent/agent.py:34-39` |
| R-16 | Before paying, the credentials provider must show the funding details, ask for explicit confirmation ("Do you want to proceed…"), and must not call the payment tool if the donor declines. | `credentials_provider/agent.py:33-39`, `55-60` |
| R-17 | The payment tool reads `cart_mandate` from state. It returns an error if the cart is missing, has an invalid structure, or has expired. | `tools/payment_tools.py:18-45`, `104-121` |
| R-18 | The payment tool creates an AP2 PaymentMandate linked to the cart ID, with a simulated card token, the merchant name, the total, a consent flag and timestamp, and `agent_present`=true. | `tools/payment_tools.py:48-92`, `130-131` |
| R-19 | The payment tool simulates the transfer: it creates `txn_<hash16>` with status `completed` and `simulation: true`, and saves `payment_mandate` and `payment_result` to state. | `tools/payment_tools.py:133-147` |
| R-20 | When finished, the donor is told the transaction ID, the amount and the recipient, with the note that the transfer is simulated. | `credentials_provider/agent.py:48-53`, `agent.py:58`, `tools/payment_tools.py:151-157` |
| R-21 | A separate "Naive_Agent" researches initiatives on the open web with `google_search` and returns unverified summaries, as the "before" baseline. | `Naive_Agent/agent.py:1-29` |
| R-22 | A mock credentials provider exists for automated testing. It approves without confirmation (but currently fails to import). | `credentials_provider/agent_mock.py:1-32` |
| R-23 | A manual test script seeds a simulated IntentMandate into an in-memory session, runs the merchant agent and prints the resulting CartMandate. | `afara-dada-code-agents/scripts/test_merchant.py:22-132` |
| R-24 | Each sub-agent (finding, merchant, credentials) exposes `root_agent` so it can also be run on its own. | `finding_agent/__init__.py`, `merchant_agent/__init__.py`, `credentials_provider/__init__.py` |

## Non-functional requirements

| ID | Requirement | Where in the code |
|----|-------------|-------------------|
| R-25 | All LLM agents use the Gemini model `gemini-3-pro-preview`. | `agent.py:28`, `finding_agent/agent.py:13`, `merchant_agent/agent.py:12`, `credentials_provider/agent.py:13`, `Naive_Agent/agent.py:19` |
| R-26 | The agents are built on Google ADK 1.17.0 and use AP2 Pydantic types (AP2 git `main`), google-genai 1.52.0 and python-dotenv 1.2.1. | `requirements.txt:1-5` |
| R-27 | Credentials come from a `.env` file (`GOOGLE_API_KEY`), and `.env` is git-ignored. | `README.md:42-44`, `.gitignore:2`, `afara-dada-code-agents/scripts/test_merchant.py:12-13` |
| R-28 | Mandates are time-limited: an intent lasts 1 hour and a cart lasts 15 minutes. Each later step checks the expiry of the earlier one. | `tools/femtechorgs_tools.py:86`, `tools/merchant_tools.py:120`, `106`, `tools/payment_tools.py:118` |
| R-29 | Duties are separated: each agent has a narrow job boundary (discovery / contract / payment), and the merchant agent never sees payment credentials. | `finding_agent/agent.py:46-51`, `merchant_agent/agent.py:41-47`, `credentials_provider/agent.py:55-60` |
| R-30 | Agents pass data only through ADK session state keys (`intent_mandate`, `cart_mandate`, `payment_mandate`, `payment_result`). Nothing is persisted outside the session. | `tools/femtechorgs_tools.py:145`, `tools/merchant_tools.py:165`, `tools/payment_tools.py:146-147` |
| R-31 | Tools log progress and failures through Python `logging` (info/warning/error). | `tools/*.py` (`logger = logging.getLogger(__name__)`) |
| R-32 | The code is packaged as the setuptools distribution `afara_dada_code_agents` 0.1.0 and installed in editable mode. | `afara-dada-code-agents/setup.py:1-7`, `README.md:36` |
| R-33 | The documented setup assumes a Google Cloud project with Vertex AI, Secret Manager and Cloud Trace APIs enabled. The code does not use Secret Manager or Cloud Trace. | `README.md:38-40` |
| R-34 | The project is MIT licensed. | `LICENSE` |

## Stated in docs but not implemented

- The README says the system "verifies and aggregates credible, certified" organisations. In the code, verification is
  a static hard-coded list with free-text `verification_source` strings (`data/femtech_programs.py`).
- The README promises "real-time updates on how the funds are being used". No code implements this (see Q-08).
- The README says it will "process donations securely". All settlement is simulated (`tools/payment_tools.py:128-143`).
