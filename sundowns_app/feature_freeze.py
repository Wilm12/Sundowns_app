"""
Centralized feature freeze configuration.

This module defines which features are frozen (temporarily inaccessible).
Frozen features remain in the codebase and database but are not accessible
to users during this product phase.

To unfreeze a feature, simply change its value from True to False.
All implementation code remains intact and recoverable.
"""

# Feature freeze state: True = frozen, False = active
FROZEN_FEATURES = {
    # Supporter domain: membership and branch functionality
    "supporter": True,
    
    # Loyalty domain: points, rewards, redemptions
    "loyalty": True,
    
    # Engagement domain: campaigns, competitions
    "engagement": True,
    
    # Transport: part of Match Day but frozen separately for operational control
    "transport": True,
}


def is_frozen(feature_name: str) -> bool:
    """Check if a feature is frozen.
    
    Args:
        feature_name: The name of the feature to check.
        
    Returns:
        True if the feature is frozen, False otherwise.
    """
    return FROZEN_FEATURES.get(feature_name, False)


def is_active(feature_name: str) -> bool:
    """Check if a feature is active (not frozen).
    
    Args:
        feature_name: The name of the feature to check.
        
    Returns:
        True if the feature is active, False if frozen.
    """
    return not is_frozen(feature_name)
