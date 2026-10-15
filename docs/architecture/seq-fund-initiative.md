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
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:31-82: two-phase instruction and example flow"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:18-154: find_tech_initiatives, _validate_donation_data, _create_intent_mandate, save_user_choice"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175: create_cart_mandate steps 1-8"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157: create_payment_mandate steps 1-7"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39: two-turn confirmation pattern"
  guesses:
    - "The donor's 'yes' after the consent question arrives as a new invocation routed to the root agent, which re-delegates to the pipeline, so merchant_agent may run again and create a second cart (see Q-02)"
    - "The LLM maps free-text regions like 'Kenya' to the key 'east-africa' before calling the tool; nothing in code does this mapping (see Q-08)"
---

# Sequence: Donor funds a verified initiative (end to end)

```mermaid
sequenceDiagram
    autonumber
    actor D as Donor
    participant R as ADK Runner / Session
    participant Root as AfaraTechAdvisor (root)
    participant F as finding_agent
    participant FT as femtechorgs_tools
    participant Reg as Registry (femtech_programs)
    participant P as FundingProcessingPipeline
    participant M as merchant_agent
    participant MT as merchant_tools
    participant C as CredentialsProvider
    participant PT as payment_tools
    participant S as Session state
    participant G as Gemini API

    Note over Root,G: Every LlmAgent step below is a Gemini generateContent call (omitted after first)

    rect rgb(240,235,255)
    Note over D,Reg: Phase 1: Discovery & Trust (may span several turns)
    D->>R: "I want to support girls coding in Kenya"
    R->>Root: run turn
    Root->>G: decide next step
    G-->>Root: transfer_to_agent(finding_agent)
    Root->>F: transfer
    F->>FT: find_tech_initiatives(region="east-africa")
    FT->>Reg: get_initiatives_by_region("east-africa")
    Reg-->>FT: [Pwani Teknowgalz, Tambua Women in Tech]
    FT-->>F: {status: success, count, initiatives (formatted), raw_data}
    F-->>D: Presents HQ, Verified By, Rating, Efficiency %, Impact, Mission
    D->>R: "Tell me about their impact" (optional Q&A turns)
    R->>F: routed to active agent
    F-->>D: answers from tool data
    D->>R: "Fund Pwani Teknowgalz with $100"
    R->>F: run turn
    F->>FT: save_user_choice(org_name, amount=100.0)
    FT->>FT: _validate_donation_data (non-empty, 0 < amount ≤ 1,000,000)
    alt invalid
        FT-->>F: {status: error, message}
        F-->>D: explains problem
    else valid
        FT->>FT: _create_intent_mandate (AP2 IntentMandate, expiry = now + 1h)
        FT->>S: state["intent_mandate"] = {..., intent_id: fund_PWANITEKNO_<epoch>}
        FT-->>F: {status: success, intent_id, expiry}
        F-->>D: "IntentMandate created (ID: fund_…), handing off to Merchant Agent"
    end
    end

    rect rgb(235,248,240)
    Note over Root,PT: Phase 2: Secure Execution (SequentialAgent)
    F->>Root: transfer back to parent (LLM-driven)
    Root-->>D: "Excellent choice. Securing your funding…"
    Root->>P: transfer_to_agent(FundingProcessingPipeline)
    P->>M: run sub-agent 1
    M->>MT: create_cart_mandate()
    MT->>S: read state["intent_mandate"]
    MT->>MT: IntentMandate.model_validate + _validate_intent_expiry
    alt missing / invalid / expired
        MT-->>M: {status: error}
    else ok
        MT->>MT: build PaymentRequest (CARD visa/mastercard, USD total)<br/>CartContents (cart_expiry = now + 15 min)
        MT->>MT: _generate_merchant_signature → SIG_<sha256[:16]>
        MT->>S: state["cart_mandate"] = CartMandate
        MT-->>M: {status: success, cart_id, cart_expiry, signature}
    end
    M-->>D: "Signed funding contract cart_…, expires in 15 min"
    P->>C: run sub-agent 2
    C->>S: (reads cart via LLM context, prompt-guided)
    C-->>D: "I am ready to transfer funding of $100 to Pwani Teknowgalz. Proceed?"
    Note over C,D: Invocation ends here and waits for the donor
    end

    rect rgb(255,243,235)
    Note over D,PT: Consent turn (prompt-enforced only)
    D->>R: "Yes, proceed"
    R->>Root: routed to root (guess: SequentialAgent is not resumable)
    Root->>P: re-delegate (merchant_agent may create a NEW cart, overwriting state)
    P->>C: run CredentialsProvider
    C->>PT: create_payment_mandate()
    PT->>S: read state["cart_mandate"]
    PT->>PT: CartMandate.model_validate + _validate_cart_expiry
    alt missing / invalid / expired
        PT-->>C: {status: error}
        C-->>D: reports failure
    else ok
        PT->>PT: consent_granted = True (hard-coded)<br/>_create_payment_mandate → payment_<sha256[:12]>
        PT->>PT: simulate transfer → txn_<sha256[:16]>, simulation: true
        PT->>S: state["payment_mandate"], state["payment_result"]
        PT-->>C: {status: success, transaction_id, payment_mandate_id}
        C-->>D: "Funding transferred (simulated). Transaction ID txn_…"
    end
    Root-->>D: Summarises transaction
    end
```

## Notes

- **Why this flow.** It is the system's reason to exist, and it touches every agent, every tool and all four state keys.
- **Handoffs go only through state.** No tool gets the previous mandate as an argument. Each one reads it from `tool_context.state`, so a missing key is caught and returned as `{status: error}`.
- **Expiry windows.** The intent lasts 1 hour and the cart 15 minutes. Both are checked in tool code (`merchant_tools.py:26-51`, `payment_tools.py:18-45`), so they do not depend on the LLM.
- **Consent is not enforced in code.** The consent turn depends on the Credentials Provider LLM obeying its instruction. The tool has no `require_confirmation` and always records `user_consent: true`.
- **Phase change is detected from text.** The root agent decides Phase 1 is complete by looking for "IntentMandate created" or "Intent ID: fund_xxx" in the conversation (`agent.py:46-48`). It does not check `state["intent_mandate"]`.
- **Re-entry after consent is a guess.** In ADK, a `SequentialAgent` cannot be resumed partway through a turn. The donor's "yes" therefore most likely reaches the root agent, and running the pipeline again runs `merchant_agent` first. That would regenerate and overwrite `cart_mandate` before payment. Behaviour depends on the LLM, so it must be verified at runtime (see NFR document, T-07).
