<div align="center">

# 👩🏾‍💻 Afara Dada Code 💜

### *Because Talent is Universal, but Access and Opportunity are Not*

[![Google AI](https://img.shields.io/badge/Google%20AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google/)

---

Despite Africa having the highest rate of female entrepreneurship globally, standing at 26% according to the [Mastercard Index of Women Entrepreneurs](https://www.mastercard.com/news/eemea/en/newsroom/press-releases/en/2021/january/africa-claims-top-three-spots-in-mastercard-index-for-highest-concentration-of-women-businesses-owners-in-the-world/), the technology sector faces a critical "broken rung" in the ladder to success: a massive funding gap. Recent data from [Africa: The Big Deal](https://thebigdeal.substack.com/p/any-seats-for-women-on-that-rocket) reveals that out of billions in venture capital raised by African tech startups, **less than 2%** goes to female-led teams.

This financial disparity is a major driver of the pipeline problem. According to the [Accenture "Resetting Tech Culture" report](https://www.accenture.com/content/dam/accenture/final/a-com-migration/pdf/pdf-134/accenture-a4-gwc-report-final1.pdf), the ratio of women in tech roles has surprisingly declined over the past 35 years, with women currently holding only roughly **14-16% of software engineering roles**. Initiatives like Mentor Match Kenya, She Code Africa, Tambua Women in Tech, Because She Can, Empower Her Community and Pwani Teknowgalz are fighting to reverse this trend by training thousands of girls, but they often struggle to secure the consistent resources needed to scale their impact.

Afara Dada Code is an AI-powered solution built to dismantle this barrier. Acting as an intelligent intermediary, this agent verifies and aggregates credible, certified female empowerment organizations across the continent. It provides donors—whether individuals, corporates, or DAOs—with a frictionless pathway to fund these initiatives directly. By using an agentic workflow, the system can answer questions about each organization's impact, process donations securely, and provide real-time updates on how the funds are being used.

The vision is to propel an Africa where women are equally represented across all career roles in technology. By solving the discovery and funding problem, we are not just building a donation tool; we are building a pipeline. We are ensuring that the 50% of the population that has been significantly underrepresented finally gets the "fuel" they need to drive innovation, closing the gender gap and enriching the African tech ecosystem.

</div>

## 🏗️ Design

Afara Dada Code is a multi-agent system built on the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and the [Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2). Each agent has one job, and they pass data to each other through ADK's shared session state as a chain of three AP2 credentials (mandates). That way every funding transfer can be traced back to a verified organization and to the donor's explicit consent.

```
Donor ──▶ AfaraTechAdvisor (root_agent)
            │
            ├─ Phase 1 ─▶ finding_agent ──────────────▶ state["intent_mandate"]
            │
            └─ Phase 2 ─▶ FundingProcessingPipeline (SequentialAgent)
                            ├─ 2a ─▶ merchant_agent ──▶ state["cart_mandate"]
                            └─ 2b ─▶ CredentialsProvider ──▶ state["payment_mandate"], state["payment_result"]
```

### Phases

| Phase | Agent | Tool(s) | Reads from state | Writes to state | Purpose |
|-------|-------|---------|------------------|-----------------|---------|
| **0. Baseline** *(demo only)* | `Naive_Agent` | `google_search` | – | – | The "before" state: open-web search with no trust layer, so the donor has to do their own due diligence. |
| **1. Discovery & Trust** | `finding_agent` | `find_tech_initiatives`, `save_user_choice` | – | `intent_mandate` | Searches **only** the vetted data layer, presents trust metrics, and records the donor's choice as an **IntentMandate** (valid for 1 hour). |
| **2a. Contract** | `merchant_agent` | `create_cart_mandate` | `intent_mandate` | `cart_mandate` | Checks that the intent hasn't expired, then builds a W3C PaymentRequest **CartMandate** signed by the organization (valid for 15 minutes). |
| **2b. Consent & Execution** | `CredentialsProvider` | `create_payment_mandate` | `cart_mandate` | `payment_mandate`, `payment_result` | Asks the donor for explicit confirmation, checks that the cart hasn't expired, creates the **PaymentMandate** and runs a simulated transfer. |

The root agent, `AfaraTechAdvisor`, stays in Phase 1 for as many turns as the donor needs. It hands off to `FundingProcessingPipeline` only after an IntentMandate exists, and the pipeline then runs Phase 2a and Phase 2b in order.

### The AP2 credential chain

1. **IntentMandate**: the donor's wish to fund a specific vetted organization (`intent_id`, `org_name`, `amount`, `currency`, `intent_expiry`).
2. **CartMandate**: the organization's binding offer (`contents.id`, `contents.merchant_name`, `contents.payment_request.details.total.amount`, `contents.cart_expiry`, `merchant_authorization` signature).
3. **PaymentMandate**: the authorized execution (`payment_mandate_contents.payment_mandate_id`, linked to the cart through `payment_details_id`, with `user_consent` recorded).

### Trusted data layer

The vetted organizations are in [`data/femtech_programs.py`](afara-dada-code-agents/femtech_empowerment_funding_advisor/data/femtech_programs.py). Each record has `name`, `hq`, `mission`, `impact_metrics`, `rating`, `efficiency` (the share of funds that goes to programs) and `verification_source`.

| Region key | Organizations |
|------------|---------------|
| `pan-africa` | She Code Africa, Women in Tech Africa |
| `east-africa` | Pwani Teknowgalz, Tambua Women in Tech |
| `global-diaspora` | Empower Her Community |
| `africa` / `all` | All of the above |

A region lookup ignores case and spacing, so "East Africa", `east_africa` and `east-africa` are treated the same. A country, city or sub-region without its own key (for example "Kenya", "Lagos" or "West Africa") is matched against each organization's HQ. `save_user_choice` rejects any organization that isn't in this list, so an IntentMandate can only be created for a vetted initiative.

### Project structure

```
afara-dada-code-agents/
├── femtech_empowerment_funding_advisor/
│   ├── agent.py                  # root_agent (AfaraTechAdvisor) + FundingProcessingPipeline
│   ├── Naive_Agent/              # Phase 0: open-web baseline for comparison
│   ├── finding_agent/            # Phase 1: discovery & IntentMandate
│   ├── merchant_agent/           # Phase 2a: signed CartMandate
│   ├── credentials_provider/     # Phase 2b: consent & PaymentMandate (+ agent_mock.py for automated tests)
│   ├── tools/                    # femtechorgs_tools, merchant_tools, payment_tools
│   └── data/femtech_programs.py  # Trusted data layer (mock DB of vetted organizations)
├── scripts/test_merchant.py      # Runs Phase 2a against a simulated IntentMandate
└── setup.py
```

> **Note:** Payments are simulated. No real funds move, and signatures are SHA-256 hashes that stand in for real cryptographic signatures.

## ⚡🧑🏾‍💻 Quick Start

```bash
# Fork The Repository 
Fork the repo to make a copy of the code to your own GitHub for the Demo

# Clone repository
git clone https://github.com/mwanyumba7/Afara-Dada-Code.git
cd Afara-Dada-Code
git checkout my-demo  # Placeholder version for learning

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd afara-dada-code-agents
pip install -e .

# Configure Google Cloud
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com secretmanager.googleapis.com cloudtrace.googleapis.com

# Create .env file
`GOOGLE_API_KEY =""`

```


