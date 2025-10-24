import os
import tempfile

import pytest

import ffxl_p
from ffxl_p import (
    FeatureFlagConfig,
)


@pytest.fixture
def sample_config() -> dict:
    """Sample configuration for testing."""
    return {
        "features": {
            "enabled_feature": {"enabled": True, "comment": "Always enabled"},
            "disabled_feature": {"enabled": False, "comment": "Always disabled"},
            "user_specific": {
                "onlyForUserIds": ["user-1", "user-2"],
                "comment": "Only for specific users",
            },
            "combined_feature": {
                "enabled": True,
                "onlyForUserIds": ["user-3"],
                "comment": "Enabled but restricted to user-3",
            },
            "empty_user_list": {"onlyForUserIds": [], "comment": "Empty user list"},
        }
    }


@pytest.fixture
def temp_yaml_file(sample_config):
    """Create a temporary YAML file with sample configuration."""
    import yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def reset_global_config():
    """Reset global config before and after each test."""
    ffxl_p._global_config = None
    yield
    ffxl_p._global_config = None


@pytest.fixture
def feature_config(sample_config):
    """Create a FeatureFlagConfig instance."""
    return FeatureFlagConfig(sample_config)


@pytest.fixture
def rollout_config():
    """Configuration with percentage rollout features."""
    return {
        "features": {
            "gradual_feature": {
                "rollout": {
                    "dev": 100,
                    "staging": 50,
                    "production": 10,
                },
                "comment": "Gradual rollout across environments",
            },
            "dev_rollout": {
                "rollout": {
                    "dev": 25,
                },
                "comment": "25% rollout in dev only",
            },
            "zero_percent": {
                "rollout": {
                    "production": 0,
                },
                "comment": "0% rollout",
            },
            "full_rollout": {
                "rollout": {
                    "production": 100,
                },
                "comment": "100% rollout",
            },
            "combined_rollout_and_env": {
                "environments": ["staging", "production"],
                "rollout": {
                    "staging": 50,
                    "production": 10,
                },
                "comment": "Rollout with environment restrictions",
            },
        }
    }
