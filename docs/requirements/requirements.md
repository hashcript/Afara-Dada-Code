---
blueprint:
  type: requirements
  id: art_requirements
  version: 1
  status: in_review
  inputs:
    artifacts: []
  evidence:
    - "README.md: problem statement (donors funding verified African female tech initiatives), Quick Start (venv, GOOGLE_API_KEY, gcloud APIs)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py: root orchestrator AfaraTechAdvisor and FundingProcessingPipeline (SequentialAgent)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/finding_agent/agent.py, merchant_agent/agent.py, credentials_provider/agent.py: agent instructions and tool bindings"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py, merchant_tools.py, payment_tools.py: tool logic (validation, mandates, simulated payment)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py: hard-coded registry of 5 vetted organisations in 3 regions"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/Naive_Agent/agent.py: open-web baseline agent"
    - "requirements.txt: pinned google-adk 1.17.0, google-genai 1.52.0, AP2 from git main"
  guesses:
    - "The system is a demo/prototype; payment simulation is intentional and real money movement is a future requirement (see Q-01)"
    - "Explicit donor consent is meant to be a hard requirement, even though the code only enforces it through the LLM prompt (see Q-03)"
    - "Only organisations from the vetted registry are meant to be fundable, although save_user_choice accepts any name (see Q-04)"
---

# Requirements: Afara Dada Code (FemTech Empowerment Funding Advisor)

Afara Dada Code is a conversational, multi-agent AI advisor built on Google ADK and Gemini. It helps donors (individuals, corporates, DAOs; README.md:15) find vetted African female tech empowerment organisations, record a funding intent, and go through a **simulated** AP2 (Agent Payments Protocol) mandate chain: IntentMandate → CartMandate → PaymentMandate. Unless noted, paths below are relative to `afara-dada-code-agents/femtech_empowerment_funding_advisor/`.

## Functional requirements

| ID | Requirement | Where in code |
|----|-------------|---------------|
| R-01 | The system provides one conversational entry agent ("AfaraTechAdvisor", persona "Afara Tech") that runs a two-phase workflow: Discovery & Trust, then Secure Execution. | `agent.py:26-88` |
| R-02 | When a donor shows interest in supporting women in tech or mentions Africa, the root agent hands off to `finding_agent`. Phase 1 can take several turns. | `agent.py:35-48`, `agent.py:60-64` |
| R-03 | The root agent moves to Phase 2 only after an IntentMandate exists. It detects this from the finding agent's reply text ("IntentMandate created" / "Intent ID: fund_xxx"). | `agent.py:46-48`, `agent.py:62` |
| R-04 | The system finds vetted initiatives by region from a curated registry. Regions are `pan-africa`, `east-africa` and `global-diaspora`; the value `africa` returns all of them. Matching ignores case. | `data/femtech_programs.py:6-76`, `tools/femtechorgs_tools.py:18-50` |
| R-05 | If a region has no initiatives, the system returns `status: not_found` with a message. | `tools/femtechorgs_tools.py:33-38` |
| R-06 | Initiatives are shown with trust metrics: HQ, verification source, rating out of 5, efficiency (% of funds going to programmes), impact and mission. The raw records are also returned to the LLM. | `tools/femtechorgs_tools.py:43-49`, `tools/femtechorgs_tools.py:157-182` |
| R-07 | The finding agent must not search the open web; it may only use the trusted registry tool. | `finding_agent/agent.py:20-23`, `finding_agent/agent.py:61-64` |
| R-08 | A donation choice is validated before it is recorded: the organisation name must not be empty, and the amount must be > 0 and ≤ 1,000,000 USD. | `tools/femtechorgs_tools.py:53-76` |
| R-09 | When the donor picks an organisation and an amount, the system creates an AP2 IntentMandate. It expires after 1 hour, has `intent_id = fund_<REGID>_<epoch>`, is in USD, and is saved to session state key `intent_mandate`. | `tools/femtechorgs_tools.py:79-113`, `tools/femtechorgs_tools.py:116-154` |
| R-10 | After the intent is created, the root agent hands off to `FundingProcessingPipeline`, which runs MerchantAgent and then CredentialsProvider in sequence. | `agent.py:14-21`, `agent.py:50-58` |
| R-11 | The merchant step reads `intent_mandate` from state, checks it against the AP2 schema and rejects it if it is missing, malformed or expired. | `tools/merchant_tools.py:89-109`, `tools/merchant_tools.py:26-51` |
| R-12 | The merchant step builds a CartMandate based on the W3C PaymentRequest. It has: method CARD (visa/mastercard, debit/credit), currency USD, `cart_<sha256[:12]>` id, a 15-minute expiry, and no shipping. It is saved to state key `cart_mandate`. | `tools/merchant_tools.py:111-177` |
| R-13 | The CartMandate carries a simulated organisation signature, `SIG_<sha256(canonical cart JSON)[:16]>`, in the `merchant_authorization` field. | `tools/merchant_tools.py:54-74`, `tools/merchant_tools.py:152-159` |
| R-14 | Before paying, the credentials provider must show the amount and recipient and wait for the donor's explicit "yes". If the donor says "no"/"cancel", the payment tool must not be called. | `credentials_provider/agent.py:33-39`, `credentials_provider/agent.py:55-60` |
| R-15 | The payment step reads `cart_mandate` from state, checks it against the schema and rejects it if it is missing, malformed or expired. | `tools/payment_tools.py:104-121`, `tools/payment_tools.py:18-45` |
| R-16 | The payment step creates an AP2 PaymentMandate linked to the cart id. It includes a simulated card token, the amount total, the recipient name, `user_consent`, `consent_timestamp` and `agent_present`. | `tools/payment_tools.py:48-92` |
| R-17 | The payment step simulates the transfer: `txn_<sha256[:16]>`, status `completed`, `simulation: true`. It writes `payment_mandate` and `payment_result` to state and returns the transaction id. | `tools/payment_tools.py:130-157` |
| R-18 | After the pipeline finishes, the root agent summarises the transaction (amount, recipient, transaction id) for the donor. | `agent.py:58`, `agent.py:76`, `credentials_provider/agent.py:48-53` |
| R-19 | Each agent stays within its role: the finding agent never takes payments, card details or makes offers; the merchant never sees donor credentials; the credentials provider never discovers organisations or makes offers. | `finding_agent/agent.py:46-58`, `merchant_agent/agent.py:41-47`, `credentials_provider/agent.py:55-60` |
| R-20 | A separate "Naive" baseline agent answers the same questions from open-web Google Search. It shows the "before" state, with no trust layer. | `Naive_Agent/agent.py:1-29` |
| R-21 | Each sub-agent package exports `root_agent`, so it can be run on its own (for example in ADK dev tooling). | `finding_agent/__init__.py`, `merchant_agent/__init__.py`, `credentials_provider/__init__.py` |
| R-22 | A manual script runs the merchant agent against a pre-filled IntentMandate and prints the resulting CartMandate. | `afara-dada-code-agents/scripts/test_merchant.py:22-132` |
| R-23 | A mock credentials provider is meant to skip confirmation for automated testing. It cannot load at present (see NFR B-01). | `credentials_provider/agent_mock.py:1-31` |

## Non-functional requirements

| ID | Requirement | Where in code |
|----|-------------|---------------|
| R-24 | Every LLM agent uses the Gemini model `gemini-3-pro-preview`. | `agent.py:28`, `finding_agent/agent.py:13`, `merchant_agent/agent.py:12`, `credentials_provider/agent.py:13`, `Naive_Agent/agent.py:19` |
| R-25 | Gemini credentials come from `GOOGLE_API_KEY` in a local `.env` file, which git ignores. | `README.md:42-43`, `.gitignore:2`, `scripts/test_merchant.py:11-13` |
| R-26 | Credentials expire: an IntentMandate after 1 hour and a CartMandate after 15 minutes. Timestamps are UTC ISO-8601 and are checked before each next step. | `tools/femtechorgs_tools.py:86`, `tools/merchant_tools.py:120`, `tools/merchant_tools.py:105-109`, `tools/payment_tools.py:117-121` |
| R-27 | Auditability: the full mandate chain is kept in session state, and every tool call is logged through Python `logging`. | `tools/*.py` (logger.info/error calls), `tools/payment_tools.py:145-147` |
| R-28 | Mandate data structures follow the AP2 Pydantic models (`ap2.types.mandate`, `ap2.types.payment_request`). | `tools/merchant_tools.py:13-21`, `tools/payment_tools.py:12-13`, `tools/femtechorgs_tools.py:84` |
| R-29 | No real money moves. Payment, signature and card token are all simulated. | `tools/payment_tools.py:65-66`, `tools/payment_tools.py:128-143`, `credentials_provider/agent.py:45` |
| R-30 | Runtime is Python with pinned `google-adk==1.17.0`, `google-genai==1.52.0` and `python-dotenv==1.2.1`. AP2 is installed from git `main` (not pinned). The package is installed with `pip install -e .`. | `requirements.txt:1-5`, `afara-dada-code-agents/setup.py` |
| R-31 | The deployment target is Google Cloud (Vertex AI / Agent Engines). The README also enables the Secret Manager and Cloud Trace APIs, but the code does not use them. | `README.md:38-40`, `requirements.txt:2` |
| R-32 | There is no database. The organisation registry is a Python literal, and transaction records exist only in the ADK session state. | `data/femtech_programs.py:10-67`, `tools/payment_tools.py:145-147` |
| R-33 | Amounts are in USD only. | `tools/femtechorgs_tools.py:110`, `tools/merchant_tools.py:134-138` |
