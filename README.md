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

## 🏗️ Design & Architecture

The project lives in `afara-dada-code-agents/femtech_empowerment_funding_advisor/` and is built on [Google ADK](https://google.github.io/adk-docs/) with the [AP2 agentic commerce protocol](https://github.com/google-agentic-commerce/AP2) providing verifiable-credential mandates for the payment flow.

```
root_agent (AfaraTechAdvisor — orchestrator)
│
├── PHASE 1: finding_agent  ────────────── Discovery & Trust
│     └── tools: find_tech_initiatives, save_user_choice
│             data:  data/femtech_programs.py (verified orgs DB)
│
└── PHASE 2: FundingProcessingPipeline (SequentialAgent)
      ├── merchant_agent ───────────────── Contract Creation
      │     └── tools: create_cart_mandate
      │
      └── credentials_provider ────────── Consent & Settlement
            └── tools: create_payment_mandate

Naive_Agent/ — a baseline "before" agent that searches the open web
with no trust layer, used to demo the value of the verified pipeline.
credentials_provider/agent_mock.py — a mock payment agent that skips
user confirmation, for automated testing.
```

## 🔄 The Two Phases

The root agent (`agent.py`) runs a two-phase workflow and transitions automatically once funding intent is secured.

### Phase 1 — Discovery & Trust (`finding_agent`)
1. The user expresses interest (e.g., *"I want to support girls coding in Kenya"*).
2. The root agent delegates to `finding_agent`, which calls `find_tech_initiatives` against the **verified** database only — never the open web.
3. The agent presents each organization with its trust metrics: rating, efficiency (% of funds reaching programs), impact numbers, and verification source.
4. This phase can span multiple conversation turns while the user compares organizations.
5. When the user picks an organization and an amount, `save_user_choice` validates the input (positive amount, ≤ $1,000,000) and writes an **IntentMandate** to shared state (valid for **1 hour**).

### Phase 2 — Secure Execution (`FundingProcessingPipeline`)
A `SequentialAgent` that runs automatically after the IntentMandate exists:

1. **`merchant_agent` (contract creation)** — reads the IntentMandate from state, validates it hasn't expired, and calls `create_cart_mandate` to produce a W3C PaymentRequest-compliant **CartMandate**: a signed, 15-minute offer from the organization committing to receive the funds.
2. **`credentials_provider` (consent & settlement)** — reads the CartMandate, validates the expiry, presents the funding details, and asks for **explicit user confirmation**. Only after a "yes" does it call `create_payment_mandate` to create the final **PaymentMandate** and simulate the transfer.

Each agent has strict boundaries (the finding agent never touches payments; the merchant agent never sees credentials), so every phase hands off only through verified state.

## 🔗 The AP2 Credential Chain

Every transaction is an auditable chain of three verifiable credentials, ensuring money goes exactly where the donor intended:

| # | Credential | Created by | Meaning | Validity |
|---|------------|-----------|---------|----------|
| 1 | `IntentMandate` | `finding_agent` | The user's desire to fund a specific verified organization | 1 hour |
| 2 | `CartMandate` | `merchant_agent` | The organization's signed, binding offer to receive the funds | 15 minutes |
| 3 | `PaymentMandate` | `credentials_provider` | The user's consent authorizing execution of the transfer | — |

```
User: "Fund Pwani Teknowgalz with $100"
  └─> IntentMandate  (fund_PWANITEKNO_…)   [desire]
        └─> CartMandate  (cart_…)          [signed offer]
              └─> user confirms "yes"
                    └─> PaymentMandate (payment_…) [authorized execution]
                          └─> Transaction (txn_…)   [funds transferred]
```

## 📊 The Verified Data Layer

`data/femtech_programs.py` is the trusted database of vetted organizations. `find_tech_initiatives` accepts region keys (`east-africa`, `west-africa`, `pan-africa`, `global-diaspora`), country or city names (`kenya`, `nigeria`), or `africa` for the full list — the lookup normalizes the input, so natural phrasings resolve to the right region.

| Organization | Region | Impact | Efficiency |
|---|---|---|---|
| She Code Africa | Pan-Africa / West Africa (Lagos) | 62,000+ women trained, 40+ chapters in 20 countries | 95% |
| Women in Tech Africa | Pan-Africa / West Africa (Accra) | Largest female tech group on the continent, 30 countries | 90% |
| Pwani Teknowgalz | East Africa (Mombasa) | 6,800+ girls empowered, 400+ jobs via CodeHack | 92% |
| Tambua Women in Tech | East Africa (Nairobi) | 350+ women celebrated globally | 88% |
| Empower Her Community | Global Diaspora | 5,000+ women empowered, 3,000+ bootcamp graduates | 94% |

## ⚡🧑🏾‍💻 Quick Start

```bash
# Fork The Repository
Fork the repo to make a copy of the code to your own GitHub for the Demo

# Clone repository
git clone https://github.com/mwanyumba7/Afara-Dada-Code.git
cd Afara-Dada-Code

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # installs google-adk, AP2, and friends

# Install the agent package (run from inside afara-dada-code-agents/)
pip install -e ./afara-dada-code-agents

# Configure Google Cloud
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com secretmanager.googleapis.com cloudtrace.googleapis.com

# Create .env file in the repo root with your Google API key
echo 'GOOGLE_API_KEY="your-key-here"' > .env
```

Run the merchant agent test to verify the mandate chain end-to-end:

```bash
python afara-dada-code-agents/scripts/test_merchant.py
```

## 📁 Repository Layout

```
afara-dada-code-agents/
├── setup.py
├── scripts/
│   └── test_merchant.py          # End-to-end test of the CartMandate flow
└── femtech_empowerment_funding_advisor/
    ├── agent.py                  # Root orchestrator + FundingProcessingPipeline
    ├── data/
    │   └── femtech_programs.py   # Verified organizations database (Trusted Data Layer)
    ├── tools/
    │   ├── femtechorgs_tools.py  # Discovery + IntentMandate tools
    │   ├── merchant_tools.py      # CartMandate + signature tools
    │   └── payment_tools.py       # PaymentMandate + transfer tools
    ├── finding_agent/            # Phase 1: Discovery & Trust
    ├── merchant_agent/           # Phase 2a: Contract Creation
    ├── credentials_provider/     # Phase 2b: Consent & Settlement (+ mock for tests)
    └── Naive_Agent/              # Baseline demo (open web, no trust layer)
```
