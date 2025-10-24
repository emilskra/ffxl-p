"""
FFXL-P: Feature Flags Extra Light - Python Implementation

A lightweight, file-based feature flag system for Python applications.
Supports YAML configuration with user-specific feature access control.
"""

import hashlib
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Union

User = Union[int, str, uuid.UUID]

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required. Install with: pip install pyyaml") from None

logger = logging.getLogger(__name__)


class FeatureFlagConfig:
    """Feature flag configuration container."""

    def __init__(self, config: Dict[str, Any], environment: Optional[str] = None):
        self._config = config
        self._environment = environment or os.getenv("FFXL_ENV") or os.getenv("ENV")
        self._dev_mode = os.getenv("FFXL_DEV_MODE", "").lower() in ("true", "1", "yes")

    def _log(self, message: str) -> None:
        """Log message in development mode."""
        if self._dev_mode:
            logger.info(f"[FFXL] {message}")

    def _get_user_percentage(self, feature_name: str, user_id: User) -> int:
        """
        Calculate a consistent percentage (0-100) for a user and feature.

        Uses SHA256 hash of feature_name + user_id to ensure:
        - Same user gets same percentage for same feature (consistency)
        - Different features have different distributions (independence)
        - Even distribution across 0-100 range
        """
        # Combine feature name and user ID for consistent hashing
        hash_input = f"{feature_name}:{user_id}".encode()

        h = hashlib.sha256(hash_input).digest()

        # Take first 8 bytes as unsigned 64-bit int; map to [0,1)
        n = int.from_bytes(h[:8], "big", signed=False)
        return (n / 2**64) * 100

    def is_feature_enabled(self, feature_name: str, user_id: User = None) -> bool:
        """
        Check if a feature is enabled for the given user and environment.
        """
        if not self.feature_exists(feature_name):
            self._log(f"Feature '{feature_name}' does not exist")
            return False

        feature = self._config["features"][feature_name]

        # Check environment restrictions first
        if "environments" in feature and feature["environments"]:
            allowed_envs = feature["environments"]
            if self._environment is None:
                self._log(
                    f"Feature '{feature_name}' has environment restrictions {allowed_envs} "
                    f"but no environment is set"
                )
                return False
            if self._environment not in allowed_envs:
                self._log(
                    f"Feature '{feature_name}' is not enabled for environment "
                    f"'{self._environment}' (allowed: {allowed_envs})"
                )
                return False
            self._log(
                f"Feature '{feature_name}' environment check passed for '{self._environment}'"
            )

        # Check percentage rollout
        if "rollout" in feature and feature["rollout"]:
            rollout_config = feature["rollout"]

            # Check if there's a percentage for current environment
            if self._environment and self._environment in rollout_config:
                target_percentage = rollout_config[self._environment]

                # Percentage rollout requires a user
                if user_id is None:
                    self._log(
                        f"Feature '{feature_name}' has percentage rollout but no user provided"
                    )
                    return False

                # Calculate user's bucket (0-100)
                user_percentage = self._get_user_percentage(feature_name, user_id)
                is_enabled = user_percentage <= target_percentage

                self._log(
                    f"Feature '{feature_name}' rollout check: "
                    f"user_percentage={user_percentage}, "
                    f"target={target_percentage}, "
                    f"result={is_enabled}"
                )
                return is_enabled
            else:
                # No rollout config for this environment, treat as 0%
                self._log(
                    f"Feature '{feature_name}' has rollout config but no percentage "
                    f"for environment '{self._environment}'"
                )
                return False

        # Check user-specific access list
        if "onlyForUserIds" in feature and feature["onlyForUserIds"]:
            only_for_users = feature["onlyForUserIds"]
            is_enabled = user_id in only_for_users
            self._log(
                f"Feature '{feature_name}' is user-specific: {is_enabled} for user '{user_id}'"
            )
            return is_enabled

        # Check global enabled flag
        is_enabled = feature.get("enabled", False)
        self._log(f"Feature '{feature_name}' is globally {'enabled' if is_enabled else 'disabled'}")
        return is_enabled

    def is_any_feature_enabled(
        self,
        feature_names: List[str],
        user: Optional[User] = None,
    ) -> bool:
        """
        Check if any of the given features are enabled.
        """
        return any(self.is_feature_enabled(name, user) for name in feature_names)

    def are_all_features_enabled(
        self,
        feature_names: List[str],
        user: Optional[User] = None,
    ) -> bool:
        """
        Check if all of the given features are enabled.
        """
        return all(self.is_feature_enabled(name, user) for name in feature_names)

    def get_enabled_features(self, user: Optional[User] = None) -> List[str]:
        """
        Get list of all enabled features for the given user.
        """
        return [
            name for name in self.get_all_feature_names() if self.is_feature_enabled(name, user)
        ]

    def get_feature_flags(
        self,
        feature_names: List[str],
        user: Optional[User] = None,
    ) -> Dict[str, bool]:
        """
        Get enabled status for multiple features as a dictionary.
        """
        return {name: self.is_feature_enabled(name, user) for name in feature_names}

    def feature_exists(self, feature_name: str) -> bool:
        """
        Check if a feature exists in the configuration.
        """
        return feature_name in self._config.get("features", {})

    def get_all_feature_names(self) -> List[str]:
        """
        Get list of all feature names defined in the configuration.

        Returns:
            List of all feature names
        """
        return list(self._config.get("features", {}).keys())

    def get_feature_config(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the raw configuration for a specific feature.
        """
        return self._config.get("features", {}).get(feature_name)


# Global configuration instance
_global_config: Optional[FeatureFlagConfig] = None


def load_feature_flags(
    file_path: Optional[str] = None, environment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load feature flags from YAML file.

    Args:
        file_path: Path to YAML file. If not provided, checks environment
                   variables FFXL_FILE or FEATURE_FLAGS_FILE, or defaults
                   to './feature-flags.yaml'
        environment: Current environment (e.g., 'dev', 'staging', 'production').
                    If not provided, checks FFXL_ENV or ENV environment variables.

    Returns:
        Parsed configuration dictionary
    """
    global _global_config

    if file_path is None:
        file_path = (
            os.getenv("FFXL_FILE") or os.getenv("FEATURE_FLAGS_FILE") or "./feature-flags.yaml"
        )

    # Check if config is provided via environment variable
    env_config = os.getenv("FFXL_CONFIG")
    if env_config:
        try:
            config = json.loads(env_config)
            _global_config = FeatureFlagConfig(config, environment)
            return config
        except json.JSONDecodeError:
            pass

    # Load from file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feature flags file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _global_config = FeatureFlagConfig(config, environment)
    return config


def load_feature_flags_as_string(
    file_path: Optional[str] = None, environment: Optional[str] = None
) -> str:
    """
    Load feature flags and return as JSON string.
    Useful for passing configuration to other processes or environments.

    Args:
        file_path: Path to YAML file (optional)
        environment: Current environment (optional)

    Returns:
        JSON string representation of the configuration
    """
    config = load_feature_flags(file_path, environment)
    return json.dumps(config)


def _get_config() -> FeatureFlagConfig:
    """Get the global configuration instance, loading it if necessary."""
    global _global_config

    if _global_config is None:
        load_feature_flags()

    return _global_config


def is_feature_enabled(feature_name: str, user: Optional[User] = None) -> bool:
    """
    Check if a feature is enabled for the given user.

    Args:
        feature_name: Name of the feature to check
        user: User unique identificator

    Returns:
        True if feature is enabled, False otherwise
    """
    return _get_config().is_feature_enabled(feature_name, user)


def is_any_feature_enabled(feature_names: List[str], user: Optional[User] = None) -> bool:
    """
    Check if any of the given features are enabled.
    """
    return _get_config().is_any_feature_enabled(feature_names, user)


def are_all_features_enabled(feature_names: List[str], user: Optional[User] = None) -> bool:
    """
    Check if all of the given features are enabled.
    """
    return _get_config().are_all_features_enabled(feature_names, user)


def get_enabled_features(user: Optional[User] = None) -> List[str]:
    """
    Get list of all enabled features for the given user.
    """
    return _get_config().get_enabled_features(user)


def get_feature_flags(feature_names: List[str], user: Optional[User] = None) -> Dict[str, bool]:
    """
    Get enabled status for multiple features as a dictionary.
    """
    return _get_config().get_feature_flags(feature_names, user)


def feature_exists(feature_name: str) -> bool:
    """
    Check if a feature exists in the configuration.
    """
    return _get_config().feature_exists(feature_name)


def get_all_feature_names() -> List[str]:
    """
    Get list of all feature names defined in the configuration.

    Returns:
        List of all feature names
    """
    return _get_config().get_all_feature_names()


def get_feature_config(feature_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the raw configuration for a specific feature.
    """
    return _get_config().get_feature_config(feature_name)
