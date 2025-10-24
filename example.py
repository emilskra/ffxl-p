"""
Example usage of FFXL-P Feature Flags
"""

from ffxl import (
    load_feature_flags,
    is_feature_enabled,
    is_any_feature_enabled,
    are_all_features_enabled,
    get_enabled_features,
    get_feature_flags,
    feature_exists,
    get_all_feature_names,
    get_feature_config,
    User
)


def main():
    # Load feature flags from YAML file
    print("Loading feature flags...")
    config = load_feature_flags('./feature-flags.yaml')
    print(f"Loaded {len(config['features'])} features\n")

    # Example 1: Check if a feature is globally enabled
    print("Example 1: Global feature check")
    print(f"Is 'new_dashboard' enabled? {is_feature_enabled('new_dashboard')}")
    print(f"Is 'beta_feature' enabled? {is_feature_enabled('beta_feature')}")
    print()

    # Example 2: Check user-specific features
    print("Example 2: User-specific feature check")
    admin_user = User(user_id="user-123")
    regular_user = User(user_id="user-789")

    print(f"Is 'admin_panel' enabled for admin? {is_feature_enabled('admin_panel', admin_user)}")
    print(f"Is 'admin_panel' enabled for regular user? {is_feature_enabled('admin_panel', regular_user)}")
    print()

    # Example 3: Using dict instead of User object
    print("Example 3: Using dict for user")
    user_dict = {'user_id': 'user-456'}
    print(f"Is 'admin_panel' enabled for user-456? {is_feature_enabled('admin_panel', user_dict)}")
    print()

    # Example 4: Check multiple features
    print("Example 4: Multiple feature checks")
    features_to_check = ['new_dashboard', 'beta_feature', 'dark_mode']
    print(f"Is ANY of {features_to_check} enabled? {is_any_feature_enabled(features_to_check)}")
    print(f"Are ALL of {features_to_check} enabled? {are_all_features_enabled(features_to_check)}")
    print()

    # Example 5: Get all enabled features for a user
    print("Example 5: Get enabled features for users")
    print(f"Enabled features (no user): {get_enabled_features()}")
    print(f"Enabled features for admin: {get_enabled_features(admin_user)}")
    print(f"Enabled features for regular user: {get_enabled_features(regular_user)}")
    print()

    # Example 6: Get feature flags as dict
    print("Example 6: Get feature flags as dict")
    flags = get_feature_flags(['new_dashboard', 'admin_panel', 'dark_mode'], admin_user)
    print(f"Feature flags for admin: {flags}")
    print()

    # Example 7: Utility functions
    print("Example 7: Utility functions")
    print(f"Does 'new_dashboard' exist? {feature_exists('new_dashboard')}")
    print(f"Does 'nonexistent_feature' exist? {feature_exists('nonexistent_feature')}")
    print(f"All feature names: {get_all_feature_names()}")
    print()

    # Example 8: Get feature configuration
    print("Example 8: Get feature configuration")
    config = get_feature_config('admin_panel')
    print(f"Admin panel config: {config}")
    print()

    # Example 9: Conditional feature usage
    print("Example 9: Conditional feature rendering")
    current_user = User(user_id="developer-001")

    if is_feature_enabled('new_dashboard', current_user):
        print("  Rendering new dashboard UI")
    else:
        print("  Rendering old dashboard UI")

    if is_feature_enabled('experimental_api', current_user):
        print("  Enabling experimental API endpoints")
    else:
        print("  Using stable API endpoints")
    print()

    # Example 10: Development mode logging
    print("Example 10: Development mode")
    print("Set FFXL_DEV_MODE=true environment variable to see detailed logging")


if __name__ == '__main__':
    main()
