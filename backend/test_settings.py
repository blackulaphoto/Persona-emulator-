"""Quick test script to check settings loading"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.core.config import settings
    from app.core.feature_flags import FeatureFlags
    
    print("=" * 60)
    print("SETTINGS DIAGNOSTIC TEST")
    print("=" * 60)
    print()
    
    # Check env vars directly
    print("1. Environment Variables (from os.getenv):")
    print(f"   FEATURE_CLINICAL_TEMPLATES = {repr(os.getenv('FEATURE_CLINICAL_TEMPLATES'))}")
    print(f"   FEATURE_REMIX_TIMELINE = {repr(os.getenv('FEATURE_REMIX_TIMELINE'))}")
    print()
    
    # Check settings object
    print("2. Settings Object Values:")
    print(f"   settings.feature_clinical_templates = {settings.feature_clinical_templates} (type: {type(settings.feature_clinical_templates).__name__})")
    print(f"   settings.feature_remix_timeline = {settings.feature_remix_timeline} (type: {type(settings.feature_remix_timeline).__name__})")
    print()
    
    # Check feature flags
    print("3. Feature Flag Checks:")
    print(f"   FeatureFlags.is_enabled('feature_clinical_templates') = {FeatureFlags.is_enabled('feature_clinical_templates')}")
    print(f"   FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES) = {FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES)}")
    print()
    
    # Check .env file location
    env_path = Path(__file__).parent / ".env"
    print("4. .env File:")
    print(f"   Path: {env_path}")
    print(f"   Exists: {env_path.exists()}")
    if env_path.exists():
        print("   Contents (FEATURE lines only):")
        with open(env_path, 'r') as f:
            for line in f:
                if 'FEATURE' in line:
                    print(f"     {line.strip()}")
    print()
    
    print("=" * 60)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()


