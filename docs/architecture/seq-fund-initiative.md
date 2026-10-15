---
blueprint:
  type: sequence
  id: art_seq-fund-initiative
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
  evidence:
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:33-76: two-phase workflow and example flow (discover, ask, choose, IntentMandate, pipeline, CartMandate, consent, payment)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:18-154: find_tech_initiatives and save_user_choice"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175: create_cart_mandate"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157: create_payment_mandate"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39: two-turn confirmation in the prompt"
  guesses:
    - "After CredentialsProvider asks for confirmation, the donor's 'yes' on the next turn reaches CredentialsProvider again, not a fresh pipeline run. ADK routing for this is not configured explicitly (see Q-03)"
    - "The donor speaks in free text and the LLM maps 'Kenya' / 'East Africa' to the key 'east-africa' (see Q-07)"
---

# Sequence – Donor funds a vetted initiative

This is the main end-to-end flow: discovery, then IntentMandate, then CartMandate, then consent, then
PaymentMandate and a simulated transfer.

```mermaid
sequenceDiagram
    autonumber
    actor D as Donor
    participant R as AfaraTechAdvisor (root)
    participant F as finding_agent
    participant FT as femtechorgs_tools
    participant DB as femtech_programs (dict)
    participant M as merchant_agent
    participant MT as merchant_tools
    participant C as CredentialsProvider
    participant PT as payment_tools
    participant S as Session state
    participant G as Gemini

    Note over R,G: Every agent turn = Gemini call deciding the reply / tool / transfer

    rect rgb(235,245,255)
    Note over D,DB: Phase 1 – Discovery & Trust
    D->>R: "I want to support girls coding in Kenya"
    R->>G: reason over instruction
    R->>F: transfer_to_agent(finding_agent)
    F->>FT: find_tech_initiatives(region="east-africa")
    FT->>DB: get_initiatives_by_region("east-africa")
    DB-->>FT: [Pwani Teknowgalz, Tambua Women in Tech]
    FT-->>F: {status: success, count, initiatives (formatted), raw_data}
    F-->>D: list with HQ, Verified By, Rating, Efficiency, Impact
    D->>F: "Tell me about their impact" (0..n turns)
    F-->>D: answers from tool data
    D->>F: "Fund Pwani Teknowgalz with $100"
    F->>FT: save_user_choice(org_name, amount=100.0)
    FT->>FT: _validate_donation_data (non-empty, 0 < amount <= 1,000,000)
    FT->>FT: _create_intent_mandate (AP2 IntentMandate, expiry now+1h, intent_id fund_PWANITEKNO_epoch)
    FT->>S: state["intent_mandate"] = {...}
    FT-->>F: {status: success, intent_id, expiry}
    F-->>D: "IntentMandate created (Intent ID ...), handing off"
    end

    rect rgb(240,255,240)
    Note over D,S: Phase 2 – Secure Execution (FundingProcessingPipeline)
    R->>M: transfer_to_agent(FundingProcessingPipeline) → merchant_agent
    M->>MT: create_cart_mandate()
    MT->>S: get "intent_mandate"
    MT->>MT: IntentMandate.model_validate + check intent_expiry > now
    alt missing / invalid / expired
        MT-->>M: {status: error, message}
        M-->>D: explains error
    else valid
        MT->>MT: build PaymentRequest (CARD visa/mastercard, USD total), CartContents (expiry now+15m)
        MT->>MT: signature = "SIG_" + sha256(canonical JSON)[:16]
        MT->>S: state["cart_mandate"] = {...}
        MT-->>M: {status: success, cart_id, cart_expiry, signature}
        M-->>D: "Signed funding contract cart_..., expires in 15 min"
    end

    M->>C: SequentialAgent → CredentialsProvider
    C->>S: read cart_mandate (via instruction context)
    C-->>D: "I am ready to transfer funding of $100 to Pwani Teknowgalz. Proceed?"
    D->>C: "yes"
    Note right of C: Consent enforced only by prompt; tool hard-codes consent_granted=True
    C->>PT: create_payment_mandate()
    PT->>S: get "cart_mandate"
    PT->>PT: CartMandate.model_validate + check cart_expiry > now
    alt missing / invalid / expired
        PT-->>C: {status: error, message}
    else valid
        PT->>PT: build PaymentMandate (PaymentResponse token=simulated, user_consent=true)
        PT->>PT: simulate transfer → txn_<sha256[:16]>, status completed, simulation=true
        PT->>S: state["payment_mandate"], state["payment_result"]
        PT-->>C: {status: success, transaction_id, payment_mandate_id}
        C-->>D: "Funding transferred (simulated). Transaction ID txn_..."
    end
    end
    R-->>D: summary of the transaction
```

## Notes

- **Each handoff checks only the previous mandate.** The merchant checks that the intent has not expired. The
  payment tool checks that the cart has not expired. Nobody verifies the signature or the organisation name
  against the directory.
- **Transitions are decided by the LLM.** The root agent moves to Phase 2 when it sees "IntentMandate created"
  in the conversation (`agent.py:46-48`). The pipeline order inside Phase 2 is deterministic.
- **The consent step is conversational.** If the donor declines, the prompt tells the agent not to call the tool.
  Nothing records the cancellation, and `cart_mandate` stays in state until it expires.
- **Error paths** return `{status: "error"}` dicts to the LLM, which explains them to the donor. Nothing is
  retried or rolled back.
