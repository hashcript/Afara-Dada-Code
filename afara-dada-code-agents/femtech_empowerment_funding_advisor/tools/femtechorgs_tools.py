"""
Tools for the Afara Tech Agent.

This file contains tools for discovering verified African female tech empowerment 
initiatives and for saving the user's funding choice to the shared state.
"""

from typing import Dict, Any
import logging
import re
# Assuming you placed the previous data code in this path
from femtech_empowerment_funding_advisor.data.femtech_programs import get_initiatives_by_region 

logger = logging.getLogger(__name__)


# This tool helps the agent verify credibility—the core value prop of your demo.
async def find_tech_initiatives(region: str) -> Dict[str, Any]:
    """
    Finds vetted female tech empowerment initiatives for a specific African region.

    Args:
        region (str): The region to search. Accepts region keys ('east-africa',
            'west-africa', 'pan-africa', 'global-diaspora'), country or city
            names ('kenya', 'nigeria'), or 'africa' for all initiatives.

    Returns:
        A dictionary containing the search results with verification details.
    """
    logger.info(f"Tool called: Searching for verified initiatives in '{region}'")
    
    # Call the new data function
    initiatives = get_initiatives_by_region(region)

    if not initiatives:
        logger.warning(f"No initiatives found for region: {region}")
        return {
            "status": "not_found",
            "message": f"I could not find any vetted initiatives for the '{region}' region."
        }

    logger.info(f"Found {len(initiatives)} verified initiatives.")

    # Format for display using the new helper function
    formatted_initiatives = [_format_initiative_display(i) for i in initiatives]

    return {
        "status": "success",
        "count": len(initiatives),
        "initiatives": formatted_initiatives,
        "raw_data": initiatives  # Keep raw data for context
    }


def _validate_donation_data(org_name: str, amount: float) -> tuple[bool, str]:
    """
    Validates donation details before saving to state.
    
    Args:
        org_name: Name of the selected organization.
        amount: Donation amount in USD.
        
    Returns:
        (is_valid, error_message)
    """
    # Validate Organization Name
    if not org_name or not org_name.strip():
        return False, "Organization name cannot be empty."
    
    # Validate Amount
    if amount <= 0:
        return False, f"Donation amount must be positive, got: ${amount}"
    
    # Increased cap for institutional donors in your demo scenario
    if amount > 1_000_000:
        return False, f"Donation amount exceeds maximum of $1,000,000: ${amount}"
    
    return True, ""


def _create_intent_mandate(org_name: str, amount: float) -> dict:
    """
    Creates an IntentMandate - AP2's verifiable credential for user intent.
    """
    from datetime import datetime, timedelta, timezone
    from ap2.types.mandate import IntentMandate
    
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Generate a mock unique ID based on the name (since we aren't using US EINs)
    # in a real app, this would come from the DB (e.g., Registration Number)
    mock_reg_id = re.sub(r'\W+', '', org_name).upper()[:10]
    
    intent_mandate_model = IntentMandate(
        user_cart_confirmation_required=True,
        natural_language_description=f"Fund verified initiative: {org_name} with ${amount:.2f}",
        merchants=[org_name],
        skus=None,
        requires_refundability=False,
        intent_expiry=expiry.isoformat()
    )
    
    intent_mandate_dict = intent_mandate_model.model_dump()
    
    timestamp = datetime.now(timezone.utc)
    intent_mandate_dict.update({
        "timestamp": timestamp.isoformat(),
        # Unique intent ID for the transaction
        "intent_id": f"fund_{mock_reg_id}_{int(timestamp.timestamp())}",
        "org_name": org_name,
        "amount": amount,
        "currency": "USD"
    })
    
    return intent_mandate_dict


async def save_user_choice(
    org_name: str,
    amount: float,
    tool_context: Any
) -> Dict[str, Any]:
    """
    Saves the user's final funding choice.
    Prepares the data for secure handoff to the payment agent.

    Args:
        org_name: Name of the selected initiative (e.g., 'She Code Africa')
        amount: Donation amount in USD
        tool_context: ADK tool context providing access to shared state

    Returns:
        Dictionary containing status and confirmation details
    """
    logger.info(f"Tool called: Saving funding choice of '{org_name}' for ${amount}")

    # Validate inputs
    is_valid, error_message = _validate_donation_data(org_name, amount)
    if not is_valid:
        logger.error(f"Validation failed: {error_message}")
        return {"status": "error", "message": error_message}
    
    # Create IntentMandate
    intent_mandate = _create_intent_mandate(org_name, amount)
    
    # Write to shared state
    tool_context.state["intent_mandate"] = intent_mandate
    
    logger.info(f"Successfully created IntentMandate for {org_name}")
    
    return {
        "status": "success",
        "message": f"Prepared funding packet: ${amount:.2f} for {org_name}",
        "intent_id": intent_mandate["intent_id"],
        "expiry": intent_mandate["intent_expiry"]
    }


def _format_initiative_display(initiative: dict) -> str:
    """
    Formats the initiative data to highlight trust and impact metrics.
    """
    name = initiative.get('name', 'Unknown')
    hq = initiative.get('hq', 'Africa')
    mission = initiative.get('mission', 'No mission statement available')
    impact = initiative.get('impact_metrics', 'N/A')
    rating = initiative.get('rating', 0.0)
    # Highlight the verification source for the demo
    verified_by = initiative.get('verification_source', 'Internal Audit')
    efficiency = initiative.get('efficiency', 0.0)
    
    efficiency_pct = int(efficiency * 100)
    
    # New Format focusing on Trust & Impact
    display = f"""
**{name}**
📍 HQ: {hq}
✅ Verified By: {verified_by}
⭐ Rating: {rating}/5.0 | 💰 Efficiency: {efficiency_pct}% to programs
📈 Impact: {impact}
📋 Mission: {mission}
    """.strip()
    
    return display