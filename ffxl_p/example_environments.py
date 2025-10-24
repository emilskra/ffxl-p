"""
Example usage of FFXL-P Feature Flags with Environment-Based Flags
"""

from ffxl_p import (
    get_enabled_features,
    is_feature_enabled,
    load_feature_flags,
)


def main():
    print("=" * 70)
    print("FFXL-P: Environment-Based Feature Flags Example")
    print("=" * 70)
    print()

    # Example 1: Load with explicit environment
    print("Example 1: Loading with explicit environment")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="dev")
    print("Loaded feature flags for environment: dev")
    print()

    # Check environment-specific features
    print("Environment-specific features (dev):")
    print(f"  debug_mode: {is_feature_enabled('debug_mode')}")
    print(f"  staging_feature: {is_feature_enabled('staging_feature')}")
    print(f"  production_feature: {is_feature_enabled('production_feature')}")
    print()

    # Example 2: Switch to staging environment
    print("Example 2: Switching to staging environment")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="staging")
    print("Loaded feature flags for environment: staging")
    print()

    print("Environment-specific features (staging):")
    print(f"  debug_mode: {is_feature_enabled('debug_mode')}")
    print(f"  staging_feature: {is_feature_enabled('staging_feature')}")
    print(f"  production_feature: {is_feature_enabled('production_feature')}")
    print()

    # Example 3: Production environment
    print("Example 3: Production environment")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="production")
    print("Loaded feature flags for environment: production")
    print()

    print("Environment-specific features (production):")
    print(f"  debug_mode: {is_feature_enabled('debug_mode')}")
    print(f"  staging_feature: {is_feature_enabled('staging_feature')}")
    print(f"  production_feature: {is_feature_enabled('production_feature')}")
    print()

    # Example 4: Combined environment + user restrictions
    print("Example 4: Combined environment + user restrictions")
    print("-" * 70)

    load_feature_flags("./feature-flags.yaml", environment="dev")

    dev_user = "developer-001"
    regular_user = "regular-user"

    print(
        f"Experimental API for developer (dev env): {is_feature_enabled('experimental_api', dev_user)}"
    )
    print(
        f"Experimental API for regular user (dev env): {is_feature_enabled('experimental_api', regular_user)}"
    )
    print()

    # Switch to production - feature restricted by environment
    load_feature_flags("./feature-flags.yaml", environment="production")
    print(
        f"Experimental API for developer (production env): {is_feature_enabled('experimental_api', dev_user)}"
    )
    print()

    # Example 5: Get all enabled features for environment
    print("Example 5: All enabled features by environment")
    print("-" * 70)

    for env in ["dev", "staging", "production"]:
        load_feature_flags("./feature-flags.yaml", environment=env)
        enabled = get_enabled_features()
        print(f"{env}: {', '.join(enabled)}")
    print()

    # Example 6: Using environment variables
    print("Example 6: Using environment variables")
    print("-" * 70)
    print("Set environment via FFXL_ENV or ENV:")
    print("  export FFXL_ENV=production")
    print("  export ENV=staging")
    print()
    print("Then load without explicit environment parameter:")
    print("  load_feature_flags()  # Uses FFXL_ENV or ENV")
    print()

    # Example 7: Real-world scenario
    print("Example 7: Real-world deployment scenario")
    print("-" * 70)

    # Simulate different environments
    scenarios = {
        "dev": "Development - all debugging features enabled",
        "staging": "Staging - test production-ready features",
        "production": "Production - only stable features",
    }

    for env, description in scenarios.items():
        load_feature_flags("./feature-flags.yaml", environment=env)
        enabled = get_enabled_features()
        print(f"\n{env.upper()}: {description}")
        print(f"  Enabled features: {len(enabled)}")
        print(f"  Features: {', '.join(sorted(enabled))}")
    print()

    # Example 8: Development mode logging
    print("Example 8: Development mode with environment checks")
    print("-" * 70)
    print("Run with FFXL_DEV_MODE=true to see detailed logging:")
    print("  FFXL_DEV_MODE=true python example_environments.py")
    print()


if __name__ == "__main__":
    main()
