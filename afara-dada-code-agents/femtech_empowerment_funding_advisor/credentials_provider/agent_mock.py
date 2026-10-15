"""
Mock Credentials Provider Agent for automated testing (no confirmation required).
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from femtech_empowerment_funding_advisor.tools.payment_tools import create_payment_mandate


credentials_provider_mock = Agent(
    name="CredentialsProviderMock",
    model="gemini-3-pro-preview",
    description="Mock payment processor for testing (auto-approves without confirmation)",
    tools=[
        FunctionTool(func=create_payment_mandate, require_confirmation=False)  # ← Only difference
    ],
    instruction="""You are a payment specialist responsible for securely processing payments.

Your workflow:

1. Read the CartMandate from shared state.
2. Extract payment details from the nested structure.
3. Use the create_payment_mandate tool to:
   - Validate the CartMandate hasn't expired
   - Create a PaymentMandate
   - Simulate payment processing
   - Record the transaction result

4. After processing, inform the user about the successful payment.

NOTE: This is a mock agent for automated testing. Confirmation is bypassed."""
)
