---
blueprint:
  type: adr
  id: art_0002-ap2-mandate-chain-via-shared-session-state
  version: 1
  status: in_review
  inputs:
    artifacts:
      - { id: art_c4-container, version: 1 }
      - { id: art_domain, version: 1 }
  evidence:
    - "requirements.txt:3: AP2 installed from git+https://github.com/google-agentic-commerce/AP2.git@main"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/femtechorgs_tools.py:79-113,145: IntentMandate built and written to state['intent_mandate']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/merchant_tools.py:89-165: reads intent, validates, builds CartMandate/PaymentRequest, writes state['cart_mandate']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/tools/payment_tools.py:104-147: reads cart, validates, builds PaymentMandate, writes state['payment_mandate'] and state['payment_result']"
    - "afara-dada-code-agents/femtech_empowerment_funding_advisor/credentials_provider/agent.py:69-74: 'THE COMPLETE AP2 CREDENTIAL CHAIN'"
  guesses:
    - "AP2 was adopted to show standards-based agentic payments, not because a payment partner requires it (see Q-01, Q-09)"
---

# ADR 0002: Model the funding transaction as an AP2 Intent → Cart → Payment mandate chain passed through ADK session state

Status: accepted (reconstructed from code)

## Context

Donors need to trust that "the money goes exactly where it was intended" (`credentials_provider/agent.py:74`). The flow crosses three agents. Each one needs a structured, machine-checkable record of what the previous one decided, and the record must be time-limited so a stale decision cannot be executed later.

## Options considered

1. **Free-text handoff.** Agents read the conversation and infer the amount and recipient. Fragile and not auditable.
2. **Custom JSON/dataclass records** for intent, offer and payment.
3. **AP2 mandates** *(chosen)*. Use the Agent Payments Protocol Pydantic types (IntentMandate, CartMandate with a W3C PaymentRequest, PaymentMandate with a W3C PaymentResponse) and store them as dicts in ADK `tool_context.state`.
4. Pass records as tool arguments chosen by the LLM. This lets the model change values in transit.

## Decision

- **Credential 1 – IntentMandate.** `save_user_choice` builds it, sets a 1-hour expiry, adds extension fields (`intent_id`, `org_name`, `amount`, `currency`, `timestamp`) and stores it at `state["intent_mandate"]`.
- **Credential 2 – CartMandate.** `create_cart_mandate` re-validates the intent with `IntentMandate.model_validate`, checks expiry, builds a PaymentRequest (CARD, USD), sets a 15-minute cart expiry, attaches a merchant signature and stores it at `state["cart_mandate"]`.
- **Credential 3 – PaymentMandate.** `create_payment_mandate` re-validates the cart with `CartMandate.model_validate`, checks expiry, builds the PaymentMandate (adding `user_consent`, `consent_timestamp` and `agent_present`) and stores it, together with `payment_result`, in state.
- Tools that execute (cart, payment) read their inputs **from state, not from LLM-supplied arguments**. `create_cart_mandate` and `create_payment_mandate` take only `tool_context`.

## Consequences

- ✅ The LLM cannot change the amount or recipient between steps. Values flow tool → state → tool.
- ✅ Each step validates against a schema and checks expiry, which limits how long an approved intent or offer can be acted on.
- ✅ The vocabulary (mandates, W3C PaymentRequest) matches an emerging standard, which makes future integration easier.
- ⚠️ Mandates are not cryptographically chained. The cart does not contain the intent id or hash. The payment step does not verify `merchant_authorization` and does not check that the cart matches an intent.
- ⚠️ Mandates are never marked as consumed. A valid intent or cart left in state can be run again before it expires, creating a new cart or transaction each time (NFR B-08).
- ⚠️ Key fields live outside the AP2 schema (`amount` in the intent, consent fields in the payment). They are therefore not validated by the models. If `amount` is missing, the cart silently uses 0.0 (`merchant_tools.py:114`).
- ⚠️ The audit trail lasts only as long as the session store (in-memory by default). Nothing is written to a ledger (Q-07, Q-10).
- ⚠️ AP2 is installed from git `main` without a pin, so a breaking schema change upstream would break all three tools (Q-09).
