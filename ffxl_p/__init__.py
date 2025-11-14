"""
FFXL-P: Feature Flags Extra Light - Python Implementation

A lightweight, file-based feature flag system for Python applications.
Supports YAML configuration with user-specific feature access control.
"""

import hashlib
import inspect
import json
import logging
import os
import uuid
from datetime import datetime, timezone
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

    def is_feature_enabled(self, feature_name: str, user_id: User = None) -> bool:
        """
        Check if a feature is enabled for the given user and environment.
        """
        if not self.feature_exists(feature_name):
            self._log(f"Feature '{feature_name}' does not exist")
            return False

        feature = self._config["features"][feature_name]
        # Check if flag is disabled globally
        if "enabled" in feature:
            is_enabled = feature.get("enabled", False)
            if is_enabled is False:
                self._log(f"Feature '{feature_name}' is globally disabled")
                return False

        # Check if feature has an enabledFrom and/or enabledUntil date restriction
        if ("enabledFrom" in feature and feature["enabledFrom"]) or (
            "enabledUntil" in feature and feature["enabledUntil"]
        ):
            # Parse ISO 8601 datetime string
            try:
                enabled_from_str = feature.get("enabledFrom")
                enabled_until_str = feature.get("enabledUntil")
                current_time = datetime.now(timezone.utc)

                # Check enabledFrom if present
                if enabled_from_str:
                    enabled_from = datetime.fromisoformat(enabled_from_str.replace("Z", "+00:00"))
                    if current_time < enabled_from:
                        self._log(
                            f"Feature '{feature_name}' is not enabled yet. "
                            f"Will be enabled from {enabled_from_str} (current time: {current_time.isoformat()})"
                        )
                        return False

                # Check enabledUntil if present
                if enabled_until_str:
                    enabled_until = datetime.fromisoformat(enabled_until_str.replace("Z", "+00:00"))
                    if current_time > enabled_until:
                        self._log(
                            f"Feature '{feature_name}' is no longer enabled. "
                            f"Was enabled until {enabled_until_str} (current time: {current_time.isoformat()})"
                        )
                        return False

            except (ValueError, AttributeError) as e:
                self._log(
                    f"Feature '{feature_name}' has invalid enabledFrom/enabledUntil value. "
                    f"Error: {e}"
                )
                return False

            self._log(
                f"Feature '{feature_name}' time window check passed "
                f"(enabledFrom: {enabled_from_str or 'not set'}, enabledUntil: {enabled_until_str or 'not set'})"
            )

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
                   to 'feature-flags.yaml' in the caller's directory
        environment: Current environment (e.g., 'dev', 'staging', 'production').
                    If not provided, checks FFXL_ENV or ENV environment variables.

    Returns:
        Parsed configuration dictionary
    """
    global _global_config

    if file_path is None:
        file_path = os.getenv("FFXL_FILE") or os.getenv("FEATURE_FLAGS_FILE")
        if file_path is None:
            # Get the directory of the calling script
            caller_frame = inspect.stack()[1]
            caller_dir = os.path.dirname(os.path.abspath(caller_frame.filename))
            file_path = os.path.join(caller_dir, "feature-flags.yaml")

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
        logger.warning(f"Feature flags file not found: {file_path}. Using empty configuration.")
        config = {"features": {}}
        _global_config = FeatureFlagConfig(config, environment)
        return config

    with open(file_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
        _validate_config(config)

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


class ConfigValidationError(Exception): ...


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the feature flag configuration structure.
    """
    if not isinstance(config, dict):
        raise ConfigValidationError("Configuration must be a dictionary")

    if "features" not in config:
        raise ConfigValidationError("Configuration must have a 'features' key")

    features = config["features"]
    if not isinstance(features, dict):
        raise ConfigValidationError("'features' must be a dictionary")

    for feature_name, feature_config in features.items():
        if not isinstance(feature_name, str):
            raise ConfigValidationError(f"Feature name must be a string, got: {type(feature_name)}")

        if not isinstance(feature_config, dict):
            raise ConfigValidationError(
                f"Feature '{feature_name}' configuration must be a dictionary, "
                f"got: {type(feature_config)}"
            )

        # Validate 'enabled' field
        if "enabled" in feature_config:
            enabled_value = feature_config["enabled"]
            if not isinstance(enabled_value, bool):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'enabled' must be a boolean (true/false), "
                    f"got: {enabled_value} ({type(enabled_value).__name__})"
                )

        # Validate 'environments' field
        if "environments" in feature_config:
            environments = feature_config["environments"]
            if not isinstance(environments, list):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'environments' must be a list, "
                    f"got: {type(environments).__name__}"
                )
            for env in environments:
                if not isinstance(env, str):
                    raise ConfigValidationError(
                        f"Feature '{feature_name}': all environment values must be strings, "
                        f"got: {env} ({type(env).__name__})"
                    )

        # Validate 'onlyForUserIds' field
        if "onlyForUserIds" in feature_config:
            user_ids = feature_config["onlyForUserIds"]
            if not isinstance(user_ids, list):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'onlyForUserIds' must be a list, "
                    f"got: {type(user_ids).__name__}"
                )
            # User IDs can be strings, ints, or UUIDs - no strict validation needed
            # They'll be compared with the user parameter at runtime

        # Validate 'rollout' field
        if "rollout" in feature_config:
            rollout = feature_config["rollout"]
            if not isinstance(rollout, dict):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'rollout' must be a dictionary, "
                    f"got: {type(rollout).__name__}"
                )
            for env, percentage in rollout.items():
                if not isinstance(env, str):
                    raise ConfigValidationError(
                        f"Feature '{feature_name}': rollout environment keys must be strings, "
                        f"got: {env} ({type(env).__name__})"
                    )
                if not isinstance(percentage, (int, float)):
                    raise ConfigValidationError(
                        f"Feature '{feature_name}': rollout percentage for environment '{env}' "
                        f"must be a number, got: {percentage} ({type(percentage).__name__})"
                    )
                if not (0 <= percentage <= 100):
                    raise ConfigValidationError(
                        f"Feature '{feature_name}': rollout percentage for environment '{env}' "
                        f"must be between 0 and 100, got: {percentage}"
                    )

        # Validate 'enabledFrom' field
        if "enabledFrom" in feature_config:
            enabled_from = feature_config["enabledFrom"]
            if not isinstance(enabled_from, str):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'enabledFrom' must be a string (ISO 8601 datetime), "
                    f"got: {type(enabled_from).__name__}"
                )
            # Try to parse the datetime to ensure it's valid
            try:
                datetime.fromisoformat(enabled_from.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'enabledFrom' must be a valid ISO 8601 datetime string, "
                    f"got: '{enabled_from}'. Error: {e}"
                ) from None

        # Validate 'enabledUntil' field
        if "enabledUntil" in feature_config:
            enabled_until = feature_config["enabledUntil"]
            if not isinstance(enabled_until, str):
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'enabledUntil' must be a string (ISO 8601 datetime), "
                    f"got: {type(enabled_until).__name__}"
                )
            # Try to parse the datetime to ensure it's valid
            try:
                datetime.fromisoformat(enabled_until.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ConfigValidationError(
                    f"Feature '{feature_name}': 'enabledUntil' must be a valid ISO 8601 datetime string, "
                    f"got: '{enabled_until}'. Error: {e}"
                ) from None


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
