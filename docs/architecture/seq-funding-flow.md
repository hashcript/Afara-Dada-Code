---
blueprint:
  type: sequence
  id: art_seq-funding-flow
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:26-88 — example flow embedded in the root agent instruction"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:79-154 — IntentMandate creation and state write"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175 — CartMandate creation, expiry check, signature"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157 — PaymentMandate creation and simulated transfer"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39 — two-turn confirmation pattern"
  guesses:
    - "The donor's explicit 'yes' is assumed to have been given before create_payment_mandate fires; the tool itself cannot verify it (see Q-02)"
---

# Sequence — Main flow: donor funds a verified initiative

```mermaid
sequenceDiagram
    actor Donor
    participant Root as Root Agent (AfaraTechAdvisor)
    participant Finding as Finding Agent
    participant Merchant as Merchant Agent
    participant Creds as Credentials Provider
    participant State as ADK Session State
    participant Data as Curated Dataset
    participant Gemini as Gemini API

    Note over Donor,Gemini: PHASE 1 — DISCOVERY & TRUST
    Donor->>Root: "I want to support girls coding in Kenya"
    Root->>Finding: delegate (sub-agent)
    Finding->>Gemini: LLM call (tool decision)
    Finding->>Data: find_tech_initiatives("east-africa")
    Data-->>Finding: verified orgs (Pwani Teknowgalz, ...)
    Finding-->>Donor: presentation with trust metrics (verification source, efficiency)

    Donor->>Finding: "Tell me about their impact" (multi-turn allowed)
    Finding-->>Donor: impact details

    Donor->>Finding: "Okay, fund them with $100"
    Finding->>Finding: validate (0 < amount ≤ $1,000,000)
    Note over Finding,State: _create_intent_mandate<br/>(AP2 IntentMandate, 1h expiry)
    Finding->>State: state["intent_mandate"] = intent
    Finding-->>Donor: "IntentMandate created (ID: fund_XXX)"

    Note over Donor,Gemini: PHASE 2 — SECURE EXECUTION (pipeline runs Merchant → Credentials in order)
    Root->>Merchant: delegate (SequentialAgent step 1)
    Merchant->>State: read state["intent_mandate"]
    State-->>Merchant: intent (validated AP2 model)
    Merchant->>Merchant: check intent not expired (security check)
    Merchant->>Merchant: build W3C PaymentRequest,<br/>sign cart (SHA-256), set 15min cart_expiry
    Merchant->>State: state["cart_mandate"] = cart
    Merchant-->>Donor: "Signed funding contract created (Cart ID: cart_XXX)"

    Merchant->>Creds: SequentialAgent step 2
    Creds->>State: read state["cart_mandate"]
    State-->>Creds: cart (validated AP2 model)
    Creds->>Creds: check cart not expired (security check)
    Creds-->>Donor: "Ready to transfer $100 to Pwani Teknowgalz. Proceed?"
    Donor->>Creds: "Yes, confirm"
    Note over Creds: create_payment_mandate:<br/>build PaymentMandate (AP2),<br/>simulate transfer, txn_id = txn_<hash>
    Creds->>State: state["payment_mandate"] + state["payment_result"]
    Creds-->>Donor: "Funding transferred. Transaction ID: txn_XXX"

    Creds-->>Root: pipeline complete
    Root-->>Donor: final summary (org, amount, transaction ID)
```

## Notes

- **Phase gate**: the root agent's instruction (`agent.py:60-64`) forbids entering Phase 2 until a valid IntentMandate exists; the Merchant Agent's tool enforces this in code by failing if `state["intent_mandate"]` is absent (`merchant_tools.py:90-96`).
- **Two expiry gates**: `_validate_intent_expiry` (merchant, `merchant_tools.py:26-51`) and `_validate_cart_expiry` (credentials, `payment_tools.py:18-45`) each re-check freshness, so a stale authorization cannot proceed even if the agents were driven out of order.
- **Consent is conversational, not enforced in code**: the Credentials Provider's instruction mandates the two-turn confirmation pattern, but `create_payment_mandate` hardcodes `consent_granted = True` (`payment_tools.py:128`). This is the single most important gap between the documented protocol and the implementation (see Q-02 and the NFR/threat doc).
- **All agent coordination is via session state**, never agent-to-agent calls; Gemini is called by whichever agent currently holds the conversation.
- The amounts, IDs and names in the diagram follow the exact formats produced by the tools (`fund_<NAME>_<unix-ts>`, `cart_<hash12>`, `txn_<hash16>`).
