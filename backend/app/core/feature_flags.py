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
from typing import Dict, List
from app.core.config import settings


class FeatureFlags:
    """
    Centralized feature flag definitions.
    
    Feature flags are now defined in Settings (config.py) for type safety and validation.
    This class provides a clean API for checking flags.
    
    To add a new feature:
    1. Add to Settings in config.py: feature_new_feature: bool = False
    2. Add constant here (e.g., NEW_FEATURE = "feature_new_feature")
    3. Use in code: if FeatureFlags.is_enabled(FeatureFlags.NEW_FEATURE):
    """
    
    # Feature flag names (must match Settings attribute names in config.py)
    CLINICAL_TEMPLATES = "feature_clinical_templates"
    REMIX_TIMELINE = "feature_remix_timeline"
    COMPARE_PERSONAS = "compare_personas"  # Not yet in Settings
    EXPORT_TIMELINE = "export_timeline"  # Not yet in Settings
    AI_RECOMMENDATIONS = "ai_recommendations"  # Not yet in Settings
    
    @staticmethod
    def is_enabled(feature_name: str) -> bool:
        """
        Check if a feature is enabled via Settings.
        
        Args:
            feature_name: Feature flag name (use constants above)
            
        Returns:
            True if enabled, False otherwise
            
        Example:
            >>> FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES)
            True
        """
        # Get the value from settings (typed and validated)
        # Falls back to False if attribute doesn't exist
        return getattr(settings, feature_name, False)
    
    @staticmethod
    def get_all_flags() -> Dict[str, bool]:
        """
        Get status of all feature flags.
        
        Returns:
            Dict mapping feature names to enabled status
        """
        return {
            FeatureFlags.CLINICAL_TEMPLATES: FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES),
            FeatureFlags.REMIX_TIMELINE: FeatureFlags.is_enabled(FeatureFlags.REMIX_TIMELINE),
            FeatureFlags.COMPARE_PERSONAS: FeatureFlags.is_enabled(FeatureFlags.COMPARE_PERSONAS),
            FeatureFlags.EXPORT_TIMELINE: FeatureFlags.is_enabled(FeatureFlags.EXPORT_TIMELINE),
            FeatureFlags.AI_RECOMMENDATIONS: FeatureFlags.is_enabled(FeatureFlags.AI_RECOMMENDATIONS),
        }
    
    @staticmethod
    def list_enabled() -> List[str]:
        """
        Get list of currently enabled features.
        
        Returns:
            List of enabled feature names
        """
        return [
            name for name, enabled in FeatureFlags.get_all_flags().items()
            if enabled
        ]

