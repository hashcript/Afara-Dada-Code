---
blueprint:
  type: sequence
  id: art_seq-donor-funding-flow
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:31-82: two-phase workflow and example flow in root instruction"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:18-154: find_tech_initiatives, _validate_donation_data, _create_intent_mandate, save_user_choice"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175: create_cart_mandate steps 1-8"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157: create_payment_mandate steps 1-7"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39: two-turn confirmation"
  guesses:
    - "After the donor answers 'yes', ADK sends that turn back into the CredentialsProvider. Whether it does so directly or through the root re-entering the pipeline (which would re-run the merchant step) is not determined by the code (see Q-03)"
    - "The LLM turns the donor's phrasing (e.g. 'Kenya', 'East Africa') into a registry key such as 'east-africa' (see Q-05)"
---

# Sequence: donor discovers an initiative and funds it (main flow)

```mermaid
sequenceDiagram
    autonumber
    actor D as Donor
    participant R as ADK Runner / Session
    participant A as AfaraTechAdvisor (root)
    participant F as finding_agent
    participant T1 as femtechorgs_tools
    participant DB as Org Registry
    participant M as merchant_agent
    participant T2 as merchant_tools
    participant C as CredentialsProvider
    participant T3 as payment_tools
    participant S as Session State
    participant G as Gemini (every LLM step)

    Note over A,G: Every agent box below calls Gemini to decide its next action (omitted for clarity)

    rect rgb(240,235,250)
    Note over D,DB: PHASE 1 — Discovery & Trust (may span many turns)
    D->>R: "I want to support girls coding in Kenya"
    R->>A: turn
    A->>F: transfer_to_agent(finding_agent)
    F->>T1: find_tech_initiatives(region="east-africa")
    T1->>DB: get_initiatives_by_region("east-africa")
    DB-->>T1: [Pwani Teknowgalz, Tambua Women in Tech]
    T1-->>F: {status: success, count, initiatives (formatted), raw_data}
    F-->>D: Present orgs with Verified By / Rating / Efficiency / Impact
    D->>F: "Tell me about their impact" (follow-up turns)
    F-->>D: Answers from returned data
    D->>F: "Fund Pwani Teknowgalz with $100"
    F->>T1: save_user_choice(org_name, amount=100.0)
    T1->>T1: _validate_donation_data (non-empty, 0 < amt ≤ 1,000,000)
    alt invalid
        T1-->>F: {status: error, message}
        F-->>D: Explain error
    else valid
        T1->>T1: _create_intent_mandate (AP2 IntentMandate, expiry now+1h, intent_id fund_REGID_epoch)
        T1->>S: state["intent_mandate"] = {...}
        T1-->>F: {status: success, intent_id, expiry}
        F-->>D: "IntentMandate created (ID: fund_…), handing off"
    end
    end

    rect rgb(235,245,240)
    Note over A,S: PHASE 2 — Secure Execution (FundingProcessingPipeline, sequential)
    A->>M: transfer_to_agent(FundingProcessingPipeline) → merchant_agent runs first
    M->>T2: create_cart_mandate()
    T2->>S: get "intent_mandate"
    alt missing / schema-invalid / expired
        T2-->>M: {status: error}
    else ok
        T2->>T2: build PaymentRequest (CARD, USD, amount) + CartContents (cart_id, expiry now+15m)
        T2->>T2: signature = "SIG_" + sha256(canonical JSON)[:16]
        T2->>S: state["cart_mandate"] = {..., merchant_authorization}
        T2-->>M: {status: success, cart_id, cart_expiry, signature}
    end
    M-->>D: "Signed funding contract cart_… (expires in 15 min)"
    M->>C: SequentialAgent continues → CredentialsProvider
    C->>S: (reads cart via conversation/state context)
    C-->>D: "I am ready to transfer $100 to Pwani Teknowgalz. Proceed?"
    Note over D,C: Turn ends. Consent is enforced ONLY by the LLM prompt (no require_confirmation)
    D->>R: "Yes, proceed"
    R->>C: turn routed back (mechanism unverified, see B-09)
    C->>T3: create_payment_mandate()
    T3->>S: get "cart_mandate"
    alt missing / schema-invalid / expired
        T3-->>C: {status: error}
    else ok
        T3->>T3: consent_granted = True (hard-coded)
        T3->>T3: build PaymentMandate (PaymentResponse token "simulated_funding_token_AFRICA_TECH")
        T3->>T3: transaction_id = "txn_" + sha256(cart_id+now)[:16], status completed, simulation true
        T3->>S: state["payment_mandate"], state["payment_result"]
        T3-->>C: {status: success, transaction_id, payment_mandate_id}
    end
    C-->>A: transfer complete
    A-->>D: "Done! Your funding has been transferred. Transaction ID: txn_…"
    end
```

## Notes

- **Why this flow.** It is the system's only business flow, and the root instruction (`agent.py:66-76`) states it as the canonical example. Every other component, including the Naive agent and the test script, exists to support or demo it.
- **Where checks happen.** Deterministic checks live only in the tools: donation validation, schema validation through the AP2 models, and expiry checks. Routing, choosing the region key, deciding the user has "selected" an org, and consent are all made by the LLM.
- **Where data comes from.** The amount reaches the cart from the intent dict's extension field `amount` (`merchant_tools.py:114`), not from a validated model field. If it is missing, it silently defaults to `0.0`.
- **What can fail.** Any step can return `{status: error}`. No step retries or rolls back, and the earlier mandates stay in state. Expired intents or carts cause errors, but the code has no path to re-issue them other than the LLM calling the tool again.
- **Consent turn (steps after "Proceed?").** ADK's SequentialAgent does not natively pause for user input. How the donor's "yes" reaches the CredentialsProvider (directly, or by the root re-delegating to the pipeline, which would make a new cart first) is not shown in the code. See NFR B-09 and Q-03.
