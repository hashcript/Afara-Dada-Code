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
    - "agent.py:31-76 — two-phase example flow in the root instruction ('I want to support girls coding in Kenya' → transfer complete)"
    - "tools/femtechorgs_tools.py — find_tech_initiatives, save_user_choice (IntentMandate, 1h expiry)"
    - "tools/merchant_tools.py — create_cart_mandate (expiry validation, W3C PaymentRequest, signature, 15m expiry)"
    - "tools/payment_tools.py — create_payment_mandate (cart expiry validation, PaymentMandate, simulated txn)"
    - "credentials_provider/agent.py:33-39 — explicit two-turn confirmation requirement"
  guesses:
    - "Consent is drawn as a donor message because the agent instruction demands it; the tool itself never receives the answer and hardcodes consent_granted = True (see Q-02)."
    - "Multi-turn comparison questions during discovery are collapsed into one loop frame; Phase 1 may span many turns per the root instruction."
---

# Sequence — Main funding flow (discovery → contract → simulated payment)

```mermaid
sequenceDiagram
    autonumber
    actor D as Donor
    participant R as Root Orchestrator<br/>(AfaraTechAdvisor)
    participant F as Finding Agent
    participant T1 as femtechorgs_tools
    participant DB as Verified Initiatives<br/>Registry (femtech_programs)
    participant P as FundingProcessingPipeline<br/>(SequentialAgent)
    participant M as Merchant Agent
    participant T2 as merchant_tools
    participant C as Credentials Provider
    participant T3 as payment_tools
    participant S as Session State
    participant G as Gemini API

    D->>R: "I want to support girls coding in Kenya"
    R->>G: inference (root turn)
    R->>F: delegate Phase 1 (discovery)
    F->>T1: find_tech_initiatives("east-africa")
    T1->>DB: get_initiatives_by_region(region)
    DB-->>T1: 2 verified organizations + trust metrics
    T1-->>F: formatted initiatives + raw data
    F->>G: inference (presentation turn)
    F-->>D: verified initiatives with rating,<br/>efficiency, verification source

    loop discovery (may span multiple turns)
        D->>F: "Tell me about their impact"
        F-->>D: impact metrics, comparisons
    end

    D->>F: "Okay, fund Pwani Teknowgalz with $100"
    F->>T1: save_user_choice(org_name, amount)
    T1->>T1: validate (positive, ≤ $1,000,000)
    T1->>S: state["intent_mandate"] =<br/>IntentMandate (1h expiry, intent_id)
    T1-->>F: success + intent_id + expiry
    F-->>D: "IntentMandate created (fund_...)"<br/>handing off to Merchant Agent

    R->>G: inference (phase transition)
    R->>P: delegate Phase 2 (execution)
    Note over P: SequentialAgent runs<br/>M then C in order

    P->>M: run merchant step
    M->>T2: create_cart_mandate()
    T2->>S: read intent_mandate
    T2->>T2: validate IntentMandate not expired;<br/>parse AP2 model; build W3C PaymentRequest;<br/>sign contents (SIG_sha256[:16])
    T2->>S: state["cart_mandate"] =<br/>CartMandate (15m expiry, cart_id)
    T2-->>M: success + cart_id + expiry + signature
    M-->>D: signed contract created,<br/>expires in 15 minutes

    P->>C: run payment step
    C->>G: inference (confirmation turn)
    C->>D: "I am ready to transfer $100 to<br/>Pwani Teknowgalz. Proceed?"
    D->>C: "Yes, proceed"
    C->>T3: create_payment_mandate()
    T3->>S: read cart_mandate
    T3->>T3: validate CartMandate not expired;<br/>build PaymentMandate (consent recorded)
    T3->>S: state["payment_mandate"],<br/>state["payment_result"] (txn_id, simulation: true)
    T3-->>C: success + transaction_id
    C-->>D: transfer complete, Transaction ID txn_...

    P-->>R: pipeline finished
    R->>G: inference (summary turn)
    R-->>D: summary: $100 to Pwani Teknowgalz,<br/>transaction ID, credential chain complete
```

## Notes

- **Phase gate.** The root orchestrator only enters Phase 2 after the Finding Agent's response signals a completed IntentMandate ("Intent ID: fund_xxx") — this gate lives entirely in the root agent's prompt instruction (`agent.py:46-48,60-64`), not in code.
- **State as the only bus.** Every handoff (intent → cart → payment) is a write-then-read of the shared ADK session state. No agent calls another agent's tools directly.
- **Two expiry checkpoints.** The intent's 1-hour expiry is re-validated when the cart is created (`merchant_tools._validate_intent_expiry`), and the cart's 15-minute expiry is re-validated at payment time (`payment_tools._validate_cart_expiry`). An expired credential returns an error status the agent narrates back to the donor.
- **Consent asymmetry (risk).** The diagram shows consent as a real donor message, but the tool hardcodes `consent_granted = True` (`payment_tools.py:128`) — the recorded consent is unconditional once the tool is invoked; the confirmation exists only at the conversation layer (Q-02).
- **Simulation.** Step "T3-->>C: success" produces a fabricated `txn_` id and a result record marked `simulation: true`; no payment network is contacted.
- **Model calls.** Each agent turn (root, finding, merchant, credentials) is a separate Gemini inference; the tools themselves are deterministic and make no external calls.
