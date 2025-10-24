"""
Example usage of FFXL-P Feature Flags
"""

from ffxl_p import (
    are_all_features_enabled,
    feature_exists,
    get_all_feature_names,
    get_enabled_features,
    get_feature_config,
    get_feature_flags,
    is_any_feature_enabled,
    is_feature_enabled,
    load_feature_flags,
)


def main():
    # Load feature flags from YAML file
    print("Loading feature flags...")
    config = load_feature_flags("./feature-flags.yaml")
    print(f"Loaded {len(config['features'])} features\n")

    # Example: Check if a feature is globally enabled
    print("Example: Global feature check")
    print(f"Is 'new_dashboard' enabled? {is_feature_enabled('new_dashboard')}")
    print(f"Is 'beta_feature' enabled? {is_feature_enabled('beta_feature')}")
    print()

    # Example: Check user-specific features
    print("Example: User-specific feature check")
    admin_user = "user-123"
    regular_user = "user-789"

    print(f"Is 'admin_panel' enabled for admin? {is_feature_enabled('admin_panel', admin_user)}")
    print(
        f"Is 'admin_panel' enabled for regular user? {is_feature_enabled('admin_panel', regular_user)}"
    )
    print()

    # Example: Check multiple features
    print("Example: Multiple feature checks")
    features_to_check = ["new_dashboard", "beta_feature", "dark_mode"]
    print(f"Is ANY of {features_to_check} enabled? {is_any_feature_enabled(features_to_check)}")
    print(f"Are ALL of {features_to_check} enabled? {are_all_features_enabled(features_to_check)}")
    print()

    # Example: Get all enabled features for a user
    print("Example: Get enabled features for users")
    print(f"Enabled features (no user): {get_enabled_features()}")
    print(f"Enabled features for admin: {get_enabled_features(admin_user)}")
    print(f"Enabled features for regular user: {get_enabled_features(regular_user)}")
    print()

    # Example: Get feature flags as dict
    print("Example: Get feature flags as dict")
    flags = get_feature_flags(["new_dashboard", "admin_panel", "dark_mode"], admin_user)
    print(f"Feature flags for admin: {flags}")
    print()

    # Example: Utility functions
    print("Example: Utility functions")
    print(f"Does 'new_dashboard' exist? {feature_exists('new_dashboard')}")
    print(f"Does 'nonexistent_feature' exist? {feature_exists('nonexistent_feature')}")
    print(f"All feature names: {get_all_feature_names()}")
    print()

    # Example: Get feature configuration
    print("Example: Get feature configuration")
    config = get_feature_config("admin_panel")
    print(f"Admin panel config: {config}")
    print()

    # Example: Conditional feature usage
    print("Example: Conditional feature rendering")
    current_user = "developer-001"

    if is_feature_enabled("new_dashboard", current_user):
        print("  Rendering new dashboard UI")
    else:
        print("  Rendering old dashboard UI")

    if is_feature_enabled("experimental_api", current_user):
        print("  Enabling experimental API endpoints")
    else:
        print("  Using stable API endpoints")
    print()

    # Example: Development mode logging
    print("Example: Development mode")
    print("Set FFXL_DEV_MODE=true environment variable to see detailed logging")


if __name__ == "__main__":
    main()
