import json
import os
import tempfile

import pytest

from ffxl_p import (
    FeatureFlagConfig,
    are_all_features_enabled,
    feature_exists,
    get_all_feature_names,
    get_enabled_features,
    get_feature_config,
    get_feature_flags,
    is_any_feature_enabled,
    is_feature_enabled,
    load_feature_flags,
    load_feature_flags_as_string,
)


class TestFeatureFlagConfig:
    """Tests for FeatureFlagConfig class."""

    def test_init(self, sample_config):
        """Test FeatureFlagConfig initialization."""
        config = FeatureFlagConfig(sample_config)
        assert config._config == sample_config

    def test_is_feature_enabled_global_true(self, feature_config):
        """Test globally enabled feature."""
        assert feature_config.is_feature_enabled("enabled_feature") is True

    def test_is_feature_enabled_global_false(self, feature_config):
        """Test globally disabled feature."""
        assert feature_config.is_feature_enabled("disabled_feature") is False

    def test_is_feature_enabled_nonexistent(self, feature_config):
        """Test nonexistent feature returns False."""
        assert feature_config.is_feature_enabled("nonexistent") is False

    def test_is_feature_enabled_user_specific_with_user(self, feature_config):
        """Test user-specific feature with authorized user."""
        user = "user-1"
        assert feature_config.is_feature_enabled("user_specific", user) is True

    def test_is_feature_enabled_user_specific_without_user(self, feature_config):
        """Test user-specific feature without user returns False."""
        assert feature_config.is_feature_enabled("user_specific") is False

    def test_is_feature_enabled_user_specific_unauthorized(self, feature_config):
        """Test user-specific feature with unauthorized user."""
        user = "user-999"
        assert feature_config.is_feature_enabled("user_specific", user) is False

    def test_is_feature_enabled_combined(self, feature_config):
        """Test combined enabled + user-specific (user-specific takes precedence)."""
        # User-3 should have access
        user3 = "user-3"
        assert feature_config.is_feature_enabled("combined_feature", user3) is True

        # User-1 should NOT have access (even though enabled=true)
        user1 = "user-1"
        assert feature_config.is_feature_enabled("combined_feature", user1) is False

    def test_is_feature_enabled_empty_user_list(self, feature_config):
        """Test feature with empty user list."""
        user = "user-1"
        # Empty list should not match any user
        assert feature_config.is_feature_enabled("empty_user_list", user) is False

    def test_is_any_feature_enabled_true(self, feature_config):
        """Test is_any_feature_enabled returns True when at least one is enabled."""
        result = feature_config.is_any_feature_enabled(["enabled_feature", "disabled_feature"])
        assert result is True

    def test_is_any_feature_enabled_false(self, feature_config):
        """Test is_any_feature_enabled returns False when none are enabled."""
        result = feature_config.is_any_feature_enabled(["disabled_feature", "nonexistent"])
        assert result is False

    def test_is_any_feature_enabled_with_user(self, feature_config):
        """Test is_any_feature_enabled with user-specific features."""
        user = "user-1"
        result = feature_config.is_any_feature_enabled(["user_specific", "disabled_feature"], user)
        assert result is True

    def test_are_all_features_enabled_true(self, feature_config):
        """Test are_all_features_enabled returns True when all are enabled."""
        user = "user-1"
        result = feature_config.are_all_features_enabled(["enabled_feature", "user_specific"], user)
        assert result is True

    def test_are_all_features_enabled_false(self, feature_config):
        """Test are_all_features_enabled returns False when not all are enabled."""
        result = feature_config.are_all_features_enabled(["enabled_feature", "disabled_feature"])
        assert result is False

    def test_get_enabled_features_no_user(self, feature_config):
        """Test get_enabled_features without user."""
        enabled = feature_config.get_enabled_features()
        assert "enabled_feature" in enabled
        assert "disabled_feature" not in enabled
        assert "user_specific" not in enabled

    def test_get_enabled_features_with_user(self, feature_config):
        """Test get_enabled_features with user."""
        user = "user-1"
        enabled = feature_config.get_enabled_features(user)
        assert "enabled_feature" in enabled
        assert "user_specific" in enabled
        assert "disabled_feature" not in enabled

    def test_get_feature_flags(self, feature_config):
        """Test get_feature_flags returns dict of feature statuses."""
        user = "user-1"
        flags = feature_config.get_feature_flags(
            ["enabled_feature", "disabled_feature", "user_specific"], user
        )

        assert flags == {
            "enabled_feature": True,
            "disabled_feature": False,
            "user_specific": True,
        }

    def test_feature_exists_true(self, feature_config):
        """Test feature_exists returns True for existing feature."""
        assert feature_config.feature_exists("enabled_feature") is True

    def test_feature_exists_false(self, feature_config):
        """Test feature_exists returns False for nonexistent feature."""
        assert feature_config.feature_exists("nonexistent") is False

    def test_get_all_feature_names(self, feature_config):
        """Test get_all_feature_names returns all feature names."""
        names = feature_config.get_all_feature_names()
        assert "enabled_feature" in names
        assert "disabled_feature" in names
        assert "user_specific" in names
        assert len(names) == 5

    def test_get_feature_config_exists(self, feature_config):
        """Test get_feature_config returns config for existing feature."""
        config = feature_config.get_feature_config("enabled_feature")
        assert config is not None
        assert config["enabled"] is True
        assert "comment" in config

    def test_get_feature_config_nonexistent(self, feature_config):
        """Test get_feature_config returns None for nonexistent feature."""
        config = feature_config.get_feature_config("nonexistent")
        assert config is None


class TestLoadingFunctions:
    """Tests for configuration loading functions."""

    def test_load_feature_flags_from_file(self, temp_yaml_file, reset_global_config):
        """Test loading feature flags from YAML file."""
        config = load_feature_flags(temp_yaml_file)

        assert "features" in config
        assert "enabled_feature" in config["features"]

    def test_load_feature_flags_from_env_variable(
        self, sample_config, reset_global_config, monkeypatch
    ):
        """Test loading feature flags from FFXL_CONFIG env variable."""
        monkeypatch.setenv("FFXL_CONFIG", json.dumps(sample_config))

        config = load_feature_flags()
        assert config == sample_config

    def test_load_feature_flags_custom_path_env(
        self, temp_yaml_file, reset_global_config, monkeypatch
    ):
        """Test loading from custom path via FFXL_FILE env variable."""
        monkeypatch.setenv("FFXL_FILE", temp_yaml_file)

        config = load_feature_flags()
        assert "features" in config

    def test_load_feature_flags_file_not_found(self, reset_global_config, caplog):
        """Test loading from nonexistent file logs warning and returns empty config."""
        config = load_feature_flags("/nonexistent/path.yaml")

        # Should return empty config
        assert config == {"features": {}}

        # Should log a warning
        assert "Feature flags file not found" in caplog.text
        assert "/nonexistent/path.yaml" in caplog.text

    def test_load_feature_flags_as_string(self, temp_yaml_file, reset_global_config):
        """Test loading feature flags as JSON string."""
        config_string = load_feature_flags_as_string(temp_yaml_file)

        assert isinstance(config_string, str)
        config = json.loads(config_string)
        assert "features" in config


class TestGlobalAPIFunctions:
    """Tests for global API functions."""

    def test_is_feature_enabled(self, temp_yaml_file, reset_global_config):
        """Test global is_feature_enabled function."""
        load_feature_flags(temp_yaml_file)

        assert is_feature_enabled("enabled_feature") is True
        assert is_feature_enabled("disabled_feature") is False

    def test_is_feature_enabled_with_user(self, temp_yaml_file, reset_global_config):
        """Test global is_feature_enabled with user."""
        load_feature_flags(temp_yaml_file)
        user = "user-1"

        assert is_feature_enabled("user_specific", user) is True

    def test_is_any_feature_enabled(self, temp_yaml_file, reset_global_config):
        """Test global is_any_feature_enabled function."""
        load_feature_flags(temp_yaml_file)

        assert is_any_feature_enabled(["enabled_feature", "disabled_feature"]) is True

    def test_are_all_features_enabled(self, temp_yaml_file, reset_global_config):
        """Test global are_all_features_enabled function."""
        load_feature_flags(temp_yaml_file)

        assert are_all_features_enabled(["enabled_feature", "disabled_feature"]) is False

    def test_get_enabled_features(self, temp_yaml_file, reset_global_config):
        """Test global get_enabled_features function."""
        load_feature_flags(temp_yaml_file)

        enabled = get_enabled_features()
        assert "enabled_feature" in enabled
        assert "disabled_feature" not in enabled

    def test_get_feature_flags(self, temp_yaml_file, reset_global_config):
        """Test global get_feature_flags function."""
        load_feature_flags(temp_yaml_file)

        flags = get_feature_flags(["enabled_feature", "disabled_feature"])
        assert flags["enabled_feature"] is True
        assert flags["disabled_feature"] is False

    def test_feature_exists(self, temp_yaml_file, reset_global_config):
        """Test global feature_exists function."""
        load_feature_flags(temp_yaml_file)

        assert feature_exists("enabled_feature") is True
        assert feature_exists("nonexistent") is False

    def test_get_all_feature_names(self, temp_yaml_file, reset_global_config):
        """Test global get_all_feature_names function."""
        load_feature_flags(temp_yaml_file)

        names = get_all_feature_names()
        assert "enabled_feature" in names

    def test_get_feature_config(self, temp_yaml_file, reset_global_config):
        """Test global get_feature_config function."""
        load_feature_flags(temp_yaml_file)

        config = get_feature_config("enabled_feature")
        assert config is not None
        assert config["enabled"] is True

    def test_auto_load_on_first_use(self, temp_yaml_file, reset_global_config, monkeypatch):
        """Test that config auto-loads on first API call."""
        # Set default file path
        monkeypatch.setenv("FFXL_FILE", temp_yaml_file)

        # Call API without explicit load
        result = is_feature_enabled("enabled_feature")
        assert result is True


class TestDevelopmentMode:
    """Tests for development mode logging."""

    def test_dev_mode_disabled(self, feature_config, capsys):
        """Test that dev mode doesn't log when disabled."""
        feature_config.is_feature_enabled("enabled_feature")

        captured = capsys.readouterr()
        assert "[FFXL]" not in captured.out


class TestUserObject:
    """Tests for User object handling."""

    def test_user_class(self, feature_config):
        """Test using User class."""
        user = "user-1"
        assert feature_config.is_feature_enabled("user_specific", user) is True

    def test_user_dict(self, feature_config):
        """Test using dict as user."""
        user = "user-1"
        assert feature_config.is_feature_enabled("user_specific", user) is True

    def test_user_dict_missing_user_id(self, feature_config):
        """Test dict without user_id key."""
        user = {"id": "user-1"}
        assert feature_config.is_feature_enabled("user_specific", user) is False

    def test_none_user(self, feature_config):
        """Test None as user."""
        assert feature_config.is_feature_enabled("user_specific", None) is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_config(self):
        """Test with empty configuration."""
        config = FeatureFlagConfig({})
        assert config.get_all_feature_names() == []
        assert config.feature_exists("anything") is False

    def test_missing_features_key(self):
        """Test config without 'features' key."""
        config = FeatureFlagConfig({"other": "data"})
        assert config.get_all_feature_names() == []

    def test_feature_without_enabled_key(self):
        """Test feature without 'enabled' key defaults to False."""
        config = FeatureFlagConfig({"features": {"no_enabled_key": {"comment": "No enabled key"}}})
        assert config.is_feature_enabled("no_enabled_key") is False

    def test_empty_feature_names_list(self, feature_config):
        """Test with empty list of feature names."""
        assert feature_config.is_any_feature_enabled([]) is False
        assert feature_config.are_all_features_enabled([]) is True
        assert feature_config.get_feature_flags([]) == {}

    def test_multiple_users_same_feature(self, feature_config):
        """Test same feature with different users."""
        user1 = "user-1"
        user2 = "user-2"
        user3 = "user-999"

        assert feature_config.is_feature_enabled("user_specific", user1) is True
        assert feature_config.is_feature_enabled("user_specific", user2) is True
        assert feature_config.is_feature_enabled("user_specific", user3) is False


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""

    def test_feature_rollout_scenario(self, feature_config):
        """Test gradual feature rollout scenario."""
        # Beta users get access
        beta_user = "user-3"
        assert feature_config.is_feature_enabled("combined_feature", beta_user) is True

        # Regular users don't
        regular_user = "user-999"
        assert feature_config.is_feature_enabled("combined_feature", regular_user) is False

    def test_admin_feature_scenario(self, feature_config):
        """Test admin-only feature scenario."""
        admin = "user-1"
        regular = "user-999"

        # Admin gets access to special features
        assert feature_config.is_feature_enabled("user_specific", admin) is True
        assert feature_config.is_feature_enabled("user_specific", regular) is False

    def test_get_user_dashboard_features(self, feature_config):
        """Test getting all features for a user dashboard."""
        user = "user-1"
        enabled = feature_config.get_enabled_features(user)

        # User should see globally enabled + their specific features
        assert "enabled_feature" in enabled
        assert "user_specific" in enabled
        assert "disabled_feature" not in enabled


class TestTimeBasedFeatures:
    """Tests for time-based feature activation (enabledFrom)."""

    @pytest.fixture
    def time_config(self):
        """Configuration with time-based features."""
        from datetime import datetime, timedelta, timezone

        # Create dates relative to now
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        return {
            "features": {
                "past_feature": {
                    "enabled": True,
                    "enabledFrom": past_date,
                    "comment": "Enabled in the past",
                },
                "future_feature": {
                    "enabled": True,
                    "enabledFrom": future_date,
                    "comment": "Will be enabled in the future",
                },
                "past_feature_z_format": {
                    "enabled": True,
                    "enabledFrom": past_date.replace("+00:00", "Z"),
                    "comment": "Past date with Z format",
                },
                "disabled_in_past": {
                    "enabled": True,
                    "enabledUntil": past_date,
                    "comment": "Disabled in future",
                },
                "disabled_in_future": {
                    "enabled": True,
                    "enabledUntil": future_date,
                    "comment": "Disabled in future",
                },
                "enabled_time_window": {
                    "enabled": True,
                    "enabledFrom": past_date,
                    "enabledUntil": future_date,
                    "comment": "Enabled feature in time window",
                },
                "disabled_time_window": {
                    "enabled": False,
                    "enabledFrom": past_date,
                    "enabledUntil": future_date,
                    "comment": "Disabled",
                },
                "no_time_restriction": {
                    "enabled": True,
                    "comment": "No time restriction",
                },
            }
        }

    def test_feature_enabled_after_enabledFrom(self, time_config):
        """Test feature is enabled when current time is after enabledFrom."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("past_feature") is True

    def test_feature_disabled_before_enabledFrom(self, time_config):
        """Test feature is disabled when current time is before enabledFrom."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("future_feature") is False

    def test_feature_enabled_with_z_format(self, time_config):
        """Test feature with 'Z' timezone format."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("past_feature_z_format") is True

    def test_feature_without_time_restriction(self, time_config):
        """Test feature without enabledFrom still works normally."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("no_time_restriction") is True

    def test_invalid_datetime_format(self):
        """Test feature with invalid datetime format returns False."""
        config = FeatureFlagConfig(
            {
                "features": {
                    "invalid_date": {
                        "enabled": True,
                        "enabledFrom": "not-a-valid-date",
                    }
                }
            }
        )
        assert config.is_feature_enabled("invalid_date") is False

    def test_time_based_with_environment_restriction(self, time_config):
        """Test time-based feature with environment restrictions."""
        from datetime import datetime, timedelta, timezone

        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        config_data = {
            "features": {
                "timed_env_feature": {
                    "enabled": True,
                    "enabledFrom": past_date,
                    "environments": ["dev"],
                }
            }
        }

        # Feature should be enabled in dev (time passed + correct env)
        config_dev = FeatureFlagConfig(config_data, environment="dev")
        assert config_dev.is_feature_enabled("timed_env_feature") is True

        # Feature should be disabled in production (time passed but wrong env)
        config_prod = FeatureFlagConfig(config_data, environment="production")
        assert config_prod.is_feature_enabled("timed_env_feature") is False

    def test_validation_invalid_datetime_format(self):
        """Test validation rejects invalid datetime format."""
        from ffxl_p import ConfigValidationError, _validate_config

        config = {
            "features": {
                "bad_date": {
                    "enabled": True,
                    "enabledFrom": "not-a-date",
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            _validate_config(config)

        assert "enabledFrom" in str(exc_info.value)
        assert "ISO 8601" in str(exc_info.value)

    def test_validation_enabledFrom_not_string(self):
        """Test validation rejects non-string enabledFrom."""
        from ffxl_p import ConfigValidationError, _validate_config

        config = {
            "features": {
                "bad_type": {
                    "enabled": True,
                    "enabledFrom": 12345,
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            _validate_config(config)

        assert "enabledFrom" in str(exc_info.value)
        assert "must be a string" in str(exc_info.value)

    def test_feature_enabled_until_past(self, time_config):
        """Test feature is disabled when enabledUntil is in the past."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("disabled_in_past") is False

    def test_feature_enabled_until_future(self, time_config):
        """Test feature is enabled when enabledUntil is in the future."""
        config = FeatureFlagConfig(time_config)
        assert config.is_feature_enabled("disabled_in_future") is True

    def test_feature_enabled_time_window(self, time_config):
        """Test feature with both enabledFrom and enabledUntil (time window)."""
        config = FeatureFlagConfig(time_config)
        # Current time is within the window (past_date to future_date)
        assert config.is_feature_enabled("enabled_time_window") is True

    def test_feature_disabled_time_window(self, time_config):
        """Test globally disabled feature in time window stays disabled."""
        config = FeatureFlagConfig(time_config)
        # Even though in time window, enabled=False should keep it disabled
        assert config.is_feature_enabled("disabled_time_window") is False

    def test_feature_outside_time_window_before(self):
        """Test feature is disabled when current time is before enabledFrom."""
        from datetime import datetime, timedelta, timezone

        future_start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        future_end = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

        config = FeatureFlagConfig(
            {
                "features": {
                    "future_window": {
                        "enabled": True,
                        "enabledFrom": future_start,
                        "enabledUntil": future_end,
                    }
                }
            }
        )
        assert config.is_feature_enabled("future_window") is False

    def test_feature_outside_time_window_after(self):
        """Test feature is disabled when current time is after enabledUntil."""
        from datetime import datetime, timedelta, timezone

        past_start = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        past_end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        config = FeatureFlagConfig(
            {
                "features": {
                    "past_window": {
                        "enabled": True,
                        "enabledFrom": past_start,
                        "enabledUntil": past_end,
                    }
                }
            }
        )
        assert config.is_feature_enabled("past_window") is False

    def test_enabled_until_with_environment_restriction(self):
        """Test enabledUntil with environment restrictions."""
        from datetime import datetime, timedelta, timezone

        future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        config_data = {
            "features": {
                "timed_env_feature": {
                    "enabled": True,
                    "enabledUntil": future_date,
                    "environments": ["dev"],
                }
            }
        }

        # Feature should be enabled in dev (time valid + correct env)
        config_dev = FeatureFlagConfig(config_data, environment="dev")
        assert config_dev.is_feature_enabled("timed_env_feature") is True

        # Feature should be disabled in production (time valid but wrong env)
        config_prod = FeatureFlagConfig(config_data, environment="production")
        assert config_prod.is_feature_enabled("timed_env_feature") is False

    def test_validation_invalid_enabledUntil_format(self):
        """Test validation rejects invalid enabledUntil format."""
        from ffxl_p import ConfigValidationError, _validate_config

        config = {
            "features": {
                "bad_date": {
                    "enabled": True,
                    "enabledUntil": "not-a-date",
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            _validate_config(config)

        assert "enabledUntil" in str(exc_info.value)
        assert "ISO 8601" in str(exc_info.value)

    def test_validation_enabledUntil_not_string(self):
        """Test validation rejects non-string enabledUntil."""
        from ffxl_p import ConfigValidationError, _validate_config

        config = {
            "features": {
                "bad_type": {
                    "enabled": True,
                    "enabledUntil": 12345,
                }
            }
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            _validate_config(config)

        assert "enabledUntil" in str(exc_info.value)
        assert "must be a string" in str(exc_info.value)

    def test_enabled_until_with_z_format(self):
        """Test enabledUntil with 'Z' timezone format."""
        from datetime import datetime, timedelta, timezone

        future_date = (
            (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z")
        )

        config = FeatureFlagConfig(
            {
                "features": {
                    "z_format_feature": {
                        "enabled": True,
                        "enabledUntil": future_date,
                    }
                }
            }
        )
        assert config.is_feature_enabled("z_format_feature") is True

    def test_only_enabledUntil_without_enabledFrom(self):
        """Test feature with only enabledUntil (no enabledFrom)."""
        from datetime import datetime, timedelta, timezone

        future_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        config = FeatureFlagConfig(
            {
                "features": {
                    "until_only": {
                        "enabled": True,
                        "enabledUntil": future_date,
                    }
                }
            }
        )
        # Should be enabled since we're before the until date
        assert config.is_feature_enabled("until_only") is True

    def test_invalid_enabledUntil_format_returns_false(self):
        """Test feature with invalid enabledUntil format returns False."""
        config = FeatureFlagConfig(
            {
                "features": {
                    "invalid_until": {
                        "enabled": True,
                        "enabledUntil": "not-a-valid-date",
                    }
                }
            }
        )
        assert config.is_feature_enabled("invalid_until") is False


class TestEnvironmentBasedFeatures:
    """Tests for environment-based feature flags."""

    @pytest.fixture
    def env_config(self):
        """Configuration with environment-based features."""
        return {
            "features": {
                "dev_only": {
                    "enabled": True,
                    "environments": ["dev"],
                    "comment": "Only for development",
                },
                "staging_and_prod": {
                    "enabled": True,
                    "environments": ["staging", "production"],
                    "comment": "Staging and production only",
                },
                "multi_env": {
                    "enabled": True,
                    "environments": ["dev", "staging", "production"],
                    "comment": "All environments",
                },
                "no_env_restriction": {
                    "enabled": True,
                    "comment": "No environment restrictions",
                },
                "env_and_user": {
                    "enabled": True,
                    "environments": ["staging"],
                    "onlyForUserIds": ["user-1"],
                    "comment": "Staging + specific users",
                },
            }
        }

    def test_feature_enabled_in_allowed_environment(self, env_config):
        """Test feature is enabled in allowed environment."""
        config = FeatureFlagConfig(env_config, environment="dev")
        assert config.is_feature_enabled("dev_only") is True

    def test_feature_disabled_in_disallowed_environment(self, env_config):
        """Test feature is disabled when not in allowed environments."""
        config = FeatureFlagConfig(env_config, environment="production")
        assert config.is_feature_enabled("dev_only") is False

    def test_feature_enabled_in_multiple_environments(self, env_config):
        """Test feature enabled in multiple environments."""
        for env in ["staging", "production"]:
            config = FeatureFlagConfig(env_config, environment=env)
            assert config.is_feature_enabled("staging_and_prod") is True

    def test_feature_disabled_when_no_environment_set(self, env_config):
        """Test feature is disabled when environment is required but not set."""
        config = FeatureFlagConfig(env_config, environment=None)
        assert config.is_feature_enabled("dev_only") is False

    def test_feature_with_no_environment_restriction(self, env_config):
        """Test feature without environment restrictions works in any env."""
        for env in ["dev", "staging", "production", None]:
            config = FeatureFlagConfig(env_config, environment=env)
            assert config.is_feature_enabled("no_env_restriction") is True

    def test_environment_and_user_restrictions_combined(self, env_config):
        """Test feature with both environment and user restrictions."""
        user = "user-1"
        wrong_user = "user-999"

        # Right environment, right user
        config_staging = FeatureFlagConfig(env_config, environment="staging")
        assert config_staging.is_feature_enabled("env_and_user", user) is True

        # Right environment, wrong user
        assert config_staging.is_feature_enabled("env_and_user", wrong_user) is False

        # Wrong environment, right user
        config_prod = FeatureFlagConfig(env_config, environment="production")
        assert config_prod.is_feature_enabled("env_and_user", user) is False

    def test_environment_from_env_variable(self, env_config, monkeypatch):
        """Test environment detection from FFXL_ENV variable."""
        monkeypatch.setenv("FFXL_ENV", "dev")
        config = FeatureFlagConfig(env_config)
        assert config.is_feature_enabled("dev_only") is True

    def test_environment_from_generic_env_variable(self, env_config, monkeypatch):
        """Test environment detection from generic ENV variable."""
        monkeypatch.setenv("ENV", "staging")
        config = FeatureFlagConfig(env_config)
        assert config.is_feature_enabled("staging_and_prod") is True

    def test_explicit_environment_overrides_env_variable(self, env_config, monkeypatch):
        """Test explicitly passed environment overrides env variable."""
        monkeypatch.setenv("FFXL_ENV", "production")
        config = FeatureFlagConfig(env_config, environment="dev")
        assert config.is_feature_enabled("dev_only") is True

    def test_load_feature_flags_with_environment(self, reset_global_config):
        """Test loading feature flags with explicit environment."""
        config_data = {
            "features": {
                "test_feature": {
                    "enabled": True,
                    "environments": ["staging"],
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            load_feature_flags(temp_path, environment="staging")
            assert is_feature_enabled("test_feature") is True

            # Reload with different environment
            load_feature_flags(temp_path, environment="production")
            assert is_feature_enabled("test_feature") is False
        finally:
            os.unlink(temp_path)

    def test_empty_environments_list(self, env_config):
        """Test feature with empty environments list."""
        env_config["features"]["empty_envs"] = {
            "enabled": True,
            "environments": [],
        }
        config = FeatureFlagConfig(env_config, environment="dev")
        # Empty list should not match any environment
        assert config.is_feature_enabled("empty_envs") is True

    def test_get_enabled_features_respects_environment(self, env_config):
        """Test get_enabled_features respects environment restrictions."""
        config_dev = FeatureFlagConfig(env_config, environment="dev")
        enabled_dev = config_dev.get_enabled_features()

        assert "dev_only" in enabled_dev
        assert "no_env_restriction" in enabled_dev
        assert "staging_and_prod" not in enabled_dev

        config_staging = FeatureFlagConfig(env_config, environment="staging")
        enabled_staging = config_staging.get_enabled_features()

        assert "dev_only" not in enabled_staging
        assert "staging_and_prod" in enabled_staging
        assert "no_env_restriction" in enabled_staging

    def test_is_any_feature_enabled_with_environments(self, env_config):
        """Test is_any_feature_enabled with environment restrictions."""
        config = FeatureFlagConfig(env_config, environment="dev")
        assert config.is_any_feature_enabled(["dev_only", "staging_and_prod"]) is True

        config_prod = FeatureFlagConfig(env_config, environment="production")
        assert config_prod.is_any_feature_enabled(["dev_only", "staging_and_prod"]) is True

    def test_are_all_features_enabled_with_environments(self, env_config):
        """Test are_all_features_enabled with environment restrictions."""
        config = FeatureFlagConfig(env_config, environment="dev")
        assert config.are_all_features_enabled(["dev_only", "staging_and_prod"]) is False

        config_all = FeatureFlagConfig(env_config, environment="staging")
        assert (
            config_all.are_all_features_enabled(
                ["multi_env", "staging_and_prod", "no_env_restriction"]
            )
            is True
        )
