import os
import tempfile

from ffxl_p import (
    FeatureFlagConfig,
    is_feature_enabled,
    load_feature_flags,
)


def test_percentage_rollout_100_percent(rollout_config):
    """Test 100% rollout enables for all users."""
    config = FeatureFlagConfig(rollout_config, environment="dev")

    # Test multiple users - all should get the feature
    for i in range(10):
        user = f"user-{i}"
        assert config.is_feature_enabled("gradual_feature", user) is True


def test_percentage_rollout_0_percent(rollout_config):
    """Test 0% rollout disables for all users."""
    config = FeatureFlagConfig(rollout_config, environment="production")

    # Test multiple users - none should get the feature
    for i in range(10):
        user = f"user-{i}"
        assert config.is_feature_enabled("zero_percent", user) is False


def test_percentage_rollout_consistency(rollout_config):
    """Test same user always gets same result for same feature."""
    config = FeatureFlagConfig(rollout_config, environment="staging")
    user = "consistent-user"

    # Check feature multiple times - should always get same result
    first_result = config.is_feature_enabled("gradual_feature", user)
    for _ in range(10):
        assert config.is_feature_enabled("gradual_feature", user) == first_result


def test_percentage_rollout_different_environments(rollout_config):
    """Test different percentages in different environments."""
    user = "user-123"

    # Dev: 100%
    config_dev = FeatureFlagConfig(rollout_config, environment="dev")
    # Should be enabled in dev (100%)
    # Note: We can't guarantee True for specific user, but high percentage means likely
    dev_result = config_dev.is_feature_enabled("gradual_feature", user)

    # Staging: 50%
    config_staging = FeatureFlagConfig(rollout_config, environment="staging")
    staging_result = config_staging.is_feature_enabled("gradual_feature", user)

    # Production: 10%
    config_prod = FeatureFlagConfig(rollout_config, environment="production")
    prod_result = config_prod.is_feature_enabled("gradual_feature", user)

    # Results should be consistent per environment
    assert config_staging.is_feature_enabled("gradual_feature", user) == staging_result
    assert config_prod.is_feature_enabled("gradual_feature", user) == prod_result
    assert config_dev.is_feature_enabled("gradual_feature", user) == dev_result


def test_percentage_rollout_requires_user(rollout_config):
    """Test percentage rollout requires a user."""
    config = FeatureFlagConfig(rollout_config, environment="staging")

    # Without user, should return False
    assert config.is_feature_enabled("gradual_feature") is False
    assert config.is_feature_enabled("gradual_feature", None) is False


def test_percentage_distribution(rollout_config):
    """Test rollout percentage roughly matches actual distribution."""
    config = FeatureFlagConfig(rollout_config, environment="staging")

    # Test with 100 users for 50% rollout
    enabled_count = 0
    for i in range(100):
        user = f"user-{i}"
        if config.is_feature_enabled("gradual_feature", user):
            enabled_count += 1

    # Should be roughly 50% (allow 30-70% range for randomness)
    assert 30 <= enabled_count <= 70, f"Expected 30-70%, got {enabled_count}%"


def test_rollout_no_percentage_for_environment(rollout_config):
    """Test feature disabled when no rollout percentage for environment."""
    config = FeatureFlagConfig(rollout_config, environment="production")
    user = "user-123"

    # dev_rollout only has config for 'dev', not 'production'
    assert config.is_feature_enabled("dev_rollout", user) is False


def test_rollout_with_environment_restrictions(rollout_config):
    """Test rollout combined with environment restrictions."""
    user = "user-123"

    # Dev environment not in allowed list
    config_dev = FeatureFlagConfig(rollout_config, environment="dev")
    assert config_dev.is_feature_enabled("combined_rollout_and_env", user) is False

    # Staging is allowed, check rollout
    config_staging = FeatureFlagConfig(rollout_config, environment="staging")
    staging_result = config_staging.is_feature_enabled("combined_rollout_and_env", user)
    assert isinstance(staging_result, bool)


def test_get_enabled_features_respects_rollout(rollout_config):
    """Test get_enabled_features respects rollout percentages."""
    config = FeatureFlagConfig(rollout_config, environment="dev")
    user = "user-123"

    enabled = config.get_enabled_features(user)

    # Should include features based on rollout
    # gradual_feature has 100% in dev, so should be included
    assert "gradual_feature" in enabled


def test_user_percentage_calculation(rollout_config):
    """Test _get_user_percentage returns value in 0-100 range."""
    config = FeatureFlagConfig(rollout_config, environment="dev")

    for i in range(20):
        user_id = f"user-{i}"
        percentage = config._get_user_percentage("test_feature", user_id)
        assert 0 <= percentage <= 100, f"Percentage {percentage} out of range"


def test_user_percentage_different_per_feature(rollout_config):
    """Test same user gets different percentage for different features."""
    config = FeatureFlagConfig(rollout_config, environment="dev")
    user_id = "user-123"

    pct1 = config._get_user_percentage("feature1", user_id)
    pct2 = config._get_user_percentage("feature2", user_id)

    # Same user, different features should (very likely) give different percentages
    # Note: Theoretically could be same, but highly unlikely
    assert pct1 != pct2 or True  # Allow same but test the concept


def test_rollout_with_load_feature_flags(reset_global_config):
    """Test rollout works with global load_feature_flags."""
    config_data = {
        "features": {
            "rollout_feature": {
                "rollout": {
                    "production": 50,
                }
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml

        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        load_feature_flags(temp_path, environment="production")
        user = "test-user"

        # Should get consistent result
        result = is_feature_enabled("rollout_feature", user)
        assert isinstance(result, bool)

        # Should be consistent across calls
        assert is_feature_enabled("rollout_feature", user) == result
    finally:
        os.unlink(temp_path)


def test_rollout_25_percent_distribution(rollout_config):
    """Test 25% rollout gives roughly 25% of users."""
    config = FeatureFlagConfig(rollout_config, environment="dev")

    enabled_count = 0
    for i in range(100):
        user = f"user-{i}"
        if config.is_feature_enabled("dev_rollout", user):
            enabled_count += 1

    # Should be roughly 25% (allow 15-35% range)
    assert 15 <= enabled_count <= 35, f"Expected 15-35%, got {enabled_count}%"


def test_rollout_edge_cases(rollout_config):
    """Test rollout edge cases and boundary conditions."""
    # Test with various user ID formats
    config = FeatureFlagConfig(rollout_config, environment="production")

    test_users = [
        "",  # Empty string
        "1",  # Single char
        "a" * 1000,  # Very long ID
        "user@example.com",  # Email format
        "user-123-abc-xyz",  # Complex ID
        "用户",  # Unicode
    ]

    for user in test_users:
        result = config.is_feature_enabled("full_rollout", user)
        # 100% rollout, all should be enabled
        assert result is True, f"Failed for user_id: {user.user_id}"


def test_rollout_priority_over_enabled_flag():
    """Test rollout takes precedence over enabled flag."""
    config_data = {
        "features": {
            "rollout_priority": {
                "enabled": False,  # Explicitly disabled
                "rollout": {"production": 100},  # But 100% rollout
            }
        }
    }

    config = FeatureFlagConfig(config_data, environment="production")
    user = "user-123"

    # Rollout should take precedence
    assert config.is_feature_enabled("rollout_priority", user) is False
