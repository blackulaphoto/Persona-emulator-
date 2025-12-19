"""
Feature Flags for Persona Evolution Simulator

Enables/disables features without code changes. Set in .env as FEATURE_X=true/false
This allows safe rollout of new features and instant rollback if issues arise.

Usage:
    from app.core.feature_flags import FeatureFlags
    
    if FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES):
        # new feature code here
    else:
        # existing stable behavior
"""
import os
from typing import Dict, List


class FeatureFlags:
    """
    Centralized feature flag definitions.
    
    To add a new feature:
    1. Add constant here (e.g., NEW_FEATURE = "new_feature")
    2. Add to .env.example: FEATURE_NEW_FEATURE=false
    3. Use in code: if FeatureFlags.is_enabled(FeatureFlags.NEW_FEATURE):
    """
    
    # Feature flag names (keep in sync with .env)
    CLINICAL_TEMPLATES = "clinical_templates"
    REMIX_TIMELINE = "remix_timeline"
    COMPARE_PERSONAS = "compare_personas"
    EXPORT_TIMELINE = "export_timeline"
    AI_RECOMMENDATIONS = "ai_recommendations"
    
    @staticmethod
    def is_enabled(feature_name: str) -> bool:
        """
        Check if a feature is enabled via environment variable.
        
        Args:
            feature_name: Feature flag name (use constants above)
            
        Returns:
            True if FEATURE_{name}=true in environment, False otherwise
            
        Example:
            >>> os.environ["FEATURE_CLINICAL_TEMPLATES"] = "true"
            >>> FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES)
            True
        """
        env_var = f"FEATURE_{feature_name.upper()}"
        value = os.getenv(env_var, "false").lower()
        return value in ("true", "1", "yes", "on")
    
    @staticmethod
    def get_all_flags() -> Dict[str, bool]:
        """
        Get status of all defined feature flags.
        
        Returns:
            Dictionary mapping feature names to their enabled status
            
        Example:
            >>> FeatureFlags.get_all_flags()
            {
                "clinical_templates": True,
                "remix_timeline": False,
                ...
            }
        """
        flags = [
            FeatureFlags.CLINICAL_TEMPLATES,
            FeatureFlags.REMIX_TIMELINE,
            FeatureFlags.COMPARE_PERSONAS,
            FeatureFlags.EXPORT_TIMELINE,
            FeatureFlags.AI_RECOMMENDATIONS,
        ]
        
        return {flag: FeatureFlags.is_enabled(flag) for flag in flags}
    
    @staticmethod
    def require_flag(feature_name: str) -> None:
        """
        Raise exception if feature is not enabled.
        
        Use this in endpoints that should be completely disabled when flag is off.
        
        Args:
            feature_name: Feature flag name
            
        Raises:
            FeatureNotEnabledException if flag is not enabled
            
        Example:
            @app.get("/api/v1/templates")
            def list_templates():
                FeatureFlags.require_flag(FeatureFlags.CLINICAL_TEMPLATES)
                # ... rest of endpoint code
        """
        if not FeatureFlags.is_enabled(feature_name):
            raise FeatureNotEnabledException(
                f"Feature '{feature_name}' is not enabled. "
                f"Set FEATURE_{feature_name.upper()}=true to enable."
            )


class FeatureNotEnabledException(Exception):
    """Raised when attempting to use a disabled feature"""
    pass
