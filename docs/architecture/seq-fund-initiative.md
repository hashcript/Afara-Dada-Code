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
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/agent.py:31-76: two-phase instruction and example flow (discover, ask, select, IntentMandate, pipeline, consent, payment, summary)"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:18-50,116-154: find_tech_initiatives and save_user_choice"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:77-175: create_cart_mandate steps 1-8"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:95-157: create_payment_mandate steps 1-7"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:33-39: two-turn confirmation pattern"
  guesses:
    - "After the finding agent saves the intent, control reaches the pipeline either by the finding agent transferring to its peer or by a transfer back to the root agent. The prompts allow both, and the code does not fix one path (see Q-10)"
    - "The donor's 'yes' on the confirmation turn reaches the CredentialsProvider. With ADK 1.17 routing it may instead return to the root agent and re-run the whole pipeline, which would create a new cart before consent is asked again (see Q-10)"
    - "Every agent turn involves at least one Gemini call. Those calls are omitted from the diagram for readability"
---

# Sequence: Donor funds a vetted initiative (discover → intent → cart → consent → payment)

```mermaid
sequenceDiagram
    autonumber
    actor D as Donor
    participant R as AfaraTechAdvisor (root LLM)
    participant F as finding_agent (LLM)
    participant FT as femtechorgs_tools
    participant DB as femtech_programs (data)
    participant S as Session state
    participant P as FundingProcessingPipeline
    participant M as merchant_agent (LLM)
    participant MT as merchant_tools
    participant C as CredentialsProvider (LLM)
    participant PT as payment_tools

    Note over R,C: Every LLM step is a Gemini (gemini-3-pro-preview) call, not shown

    rect rgb(240,235,250)
    Note over D,DB: PHASE 1: Discovery & Trust
    D->>R: "I want to support girls coding in Kenya"
    R->>F: transfer_to_agent(finding_agent)
    F->>FT: find_tech_initiatives(region="east-africa")
    FT->>DB: get_initiatives_by_region("east-africa")
    DB-->>FT: [Pwani Teknowgalz, Tambua Women in Tech]
    FT-->>F: {status: success, count, initiatives (formatted), raw_data}
    F-->>D: Lists orgs with Verified By / Rating / Efficiency / Impact
    loop zero or more Q&A turns
        D->>F: "Tell me about their impact"
        F-->>D: Answer from tool results (no web search)
    end
    D->>F: "Fund Pwani Teknowgalz with $100"
    F->>FT: save_user_choice(org_name, amount=100.0)
    FT->>FT: _validate_donation_data (name non-empty, amount in (0, 1,000,000])
    alt invalid
        FT-->>F: {status: error, message}
        F-->>D: Explains error
    else valid
        FT->>FT: _create_intent_mandate (AP2 IntentMandate, expiry now+1h, intent_id fund_REGID_epoch)
        FT->>S: state["intent_mandate"] = dict
        FT-->>F: {status: success, intent_id, expiry}
        F-->>D: "IntentMandate created (ID fund_...), handing off"
    end
    end

    rect rgb(235,245,240)
    Note over R,PT: PHASE 2: Secure Execution
    F->>P: transfer (directly to peer, or via root) [see Q-10]
    P->>M: run sub-agent 1
    M->>MT: create_cart_mandate()
    MT->>S: read state["intent_mandate"]
    alt missing / invalid / expired
        MT-->>M: {status: error}
        M-->>D: Reports failure
    else ok
        MT->>MT: build PaymentRequest (CARD, USD total), CartContents (cart_id, expiry now+15m)
        MT->>MT: signature = "SIG_" + sha256(canonical JSON)[:16]
        MT->>S: state["cart_mandate"] = dict
        MT-->>M: {status: success, cart_id, cart_expiry, signature}
        M-->>D: "Signed contract cart_..., expires in 15 min"
    end
    P->>C: run sub-agent 2
    C-->>D: "I am ready to transfer $100 to Pwani Teknowgalz. Proceed?"
    Note over D,C: Turn ends. Consent is enforced only by the prompt
    D->>C: "Yes" (routing of this turn: see Q-10)
    alt donor declines
        C-->>D: Cancels, tool not called
    else donor confirms
        C->>PT: create_payment_mandate()
        PT->>S: read state["cart_mandate"]
        PT->>PT: validate structure + cart expiry
        PT->>PT: build PaymentMandate (simulated card token, consent_granted = True hard-coded)
        PT->>PT: simulate transfer: txn_id, status "completed", simulation true
        PT->>S: state["payment_mandate"], state["payment_result"]
        PT-->>C: {status: success, transaction_id, payment_mandate_id}
        C-->>D: "Funding transferred (simulated). Transaction ID txn_..."
    end
    R-->>D: Summary of the transaction
    end
```

## Notes

1. **Why this flow.** It is the product's only end-to-end business flow. Every other part of the repo (the Naive agent,
   the test script, the mock) supports or contrasts with it.
2. **Gates are mostly probabilistic.** Three conditions are checked by code: amount/name validity (step "validate"),
   intent expiry and cart expiry. Three are only asked for in prompts: "only proceed to Phase 2 after a valid
   IntentMandate", "only call the payment tool after explicit confirmation", and "do not search the open web".
   An LLM slip or a prompt injection can skip any of the prompt-only gates.
3. **Region mapping is done by the LLM.** "Kenya" works only if Gemini picks `east-africa`. The tool does exact key
   matching (`femtech_programs.py:70-76`).
4. **State hand-off.** Each tool re-validates the previous mandate with its AP2 Pydantic model. The cart amount,
   however, comes from the *extension* field `intent_mandate["amount"]` (`merchant_tools.py:114`), not from a signed or
   validated field.
5. **Timing budget.** Once the cart exists the donor has 15 minutes to confirm, or the payment tool returns
   "expired". The intent allows 1 hour between choice and cart creation.
6. **Possible re-run on confirmation (to verify).** `credentials_provider` sits under a SequentialAgent. If ADK sends
   the next user message back to the root agent, which is likely because a SequentialAgent is not an LLM agent that
   can take a transfer, the root may start the pipeline again. The merchant would then overwrite `cart_mandate` and
   the consent question would repeat. This flow should be tested end to end (Q-10).
