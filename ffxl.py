"""
FFXL-P: Feature Flags Extra Light - Python Implementation

A lightweight, file-based feature flag system for Python applications.
Supports YAML configuration with user-specific feature access control.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required. Install with: pip install pyyaml")


@dataclass
class User:
    """User object for feature flag evaluation."""
    user_id: str


class FeatureFlagConfig:
    """Feature flag configuration container."""

    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._dev_mode = os.getenv('FFXL_DEV_MODE', '').lower() in ('true', '1', 'yes')

    def _log(self, message: str) -> None:
        """Log message in development mode."""
        if self._dev_mode:
            print(f"[FFXL] {message}")

    def is_feature_enabled(
        self,
        feature_name: str,
        user: Optional[Union[User, Dict[str, str]]] = None
    ) -> bool:
        """
        Check if a feature is enabled for the given user.

        Args:
            feature_name: Name of the feature to check
            user: User object or dict with 'user_id' key (optional)

        Returns:
            True if feature is enabled, False otherwise
        """
        if not self.feature_exists(feature_name):
            self._log(f"Feature '{feature_name}' does not exist")
            return False

        feature = self._config['features'][feature_name]

        # Extract user_id from user object or dict
        user_id = None
        if user:
            if isinstance(user, User):
                user_id = user.user_id
            elif isinstance(user, dict) and 'user_id' in user:
                user_id = user['user_id']

        # Check user-specific access
        if 'onlyForUserIds' in feature and feature['onlyForUserIds']:
            only_for_users = feature['onlyForUserIds']
            is_enabled = user_id in only_for_users
            self._log(f"Feature '{feature_name}' is user-specific: {is_enabled} for user '{user_id}'")
            return is_enabled

        # Check global enabled flag
        is_enabled = feature.get('enabled', False)
        self._log(f"Feature '{feature_name}' is globally {'enabled' if is_enabled else 'disabled'}")
        return is_enabled

    def is_any_feature_enabled(
        self,
        feature_names: List[str],
        user: Optional[Union[User, Dict[str, str]]] = None
    ) -> bool:
        """
        Check if any of the given features are enabled.

        Args:
            feature_names: List of feature names to check
            user: User object or dict with 'user_id' key (optional)

        Returns:
            True if at least one feature is enabled, False otherwise
        """
        return any(self.is_feature_enabled(name, user) for name in feature_names)

    def are_all_features_enabled(
        self,
        feature_names: List[str],
        user: Optional[Union[User, Dict[str, str]]] = None
    ) -> bool:
        """
        Check if all of the given features are enabled.

        Args:
            feature_names: List of feature names to check
            user: User object or dict with 'user_id' key (optional)

        Returns:
            True if all features are enabled, False otherwise
        """
        return all(self.is_feature_enabled(name, user) for name in feature_names)

    def get_enabled_features(
        self,
        user: Optional[Union[User, Dict[str, str]]] = None
    ) -> List[str]:
        """
        Get list of all enabled features for the given user.

        Args:
            user: User object or dict with 'user_id' key (optional)

        Returns:
            List of enabled feature names
        """
        return [
            name for name in self.get_all_feature_names()
            if self.is_feature_enabled(name, user)
        ]

    def get_feature_flags(
        self,
        feature_names: List[str],
        user: Optional[Union[User, Dict[str, str]]] = None
    ) -> Dict[str, bool]:
        """
        Get enabled status for multiple features as a dictionary.

        Args:
            feature_names: List of feature names to check
            user: User object or dict with 'user_id' key (optional)

        Returns:
            Dictionary mapping feature names to their enabled status
        """
        return {
            name: self.is_feature_enabled(name, user)
            for name in feature_names
        }

    def feature_exists(self, feature_name: str) -> bool:
        """
        Check if a feature exists in the configuration.

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if feature exists, False otherwise
        """
        return feature_name in self._config.get('features', {})

    def get_all_feature_names(self) -> List[str]:
        """
        Get list of all feature names defined in the configuration.

        Returns:
            List of all feature names
        """
        return list(self._config.get('features', {}).keys())

    def get_feature_config(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the raw configuration for a specific feature.

        Args:
            feature_name: Name of the feature

        Returns:
            Feature configuration dict or None if not found
        """
        return self._config.get('features', {}).get(feature_name)


# Global configuration instance
_global_config: Optional[FeatureFlagConfig] = None


def load_feature_flags(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load feature flags from YAML file.

    Args:
        file_path: Path to YAML file. If not provided, checks environment
                   variables FFXL_FILE or FEATURE_FLAGS_FILE, or defaults
                   to './feature-flags.yaml'

    Returns:
        Parsed configuration dictionary
    """
    global _global_config

    if file_path is None:
        file_path = (
            os.getenv('FFXL_FILE') or
            os.getenv('FEATURE_FLAGS_FILE') or
            './feature-flags.yaml'
        )

    # Check if config is provided via environment variable
    env_config = os.getenv('FFXL_CONFIG')
    if env_config:
        try:
            config = json.loads(env_config)
            _global_config = FeatureFlagConfig(config)
            return config
        except json.JSONDecodeError:
            pass

    # Load from file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feature flags file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    _global_config = FeatureFlagConfig(config)
    return config


def load_feature_flags_as_string(file_path: Optional[str] = None) -> str:
    """
    Load feature flags and return as JSON string.
    Useful for passing configuration to other processes or environments.

    Args:
        file_path: Path to YAML file (optional)

    Returns:
        JSON string representation of the configuration
    """
    config = load_feature_flags(file_path)
    return json.dumps(config)


def _get_config() -> FeatureFlagConfig:
    """Get the global configuration instance, loading it if necessary."""
    global _global_config

    if _global_config is None:
        load_feature_flags()

    return _global_config


def is_feature_enabled(
    feature_name: str,
    user: Optional[Union[User, Dict[str, str]]] = None
) -> bool:
    """
    Check if a feature is enabled for the given user.

    Args:
        feature_name: Name of the feature to check
        user: User object or dict with 'user_id' key (optional)

    Returns:
        True if feature is enabled, False otherwise
    """
    return _get_config().is_feature_enabled(feature_name, user)


def is_any_feature_enabled(
    feature_names: List[str],
    user: Optional[Union[User, Dict[str, str]]] = None
) -> bool:
    """
    Check if any of the given features are enabled.

    Args:
        feature_names: List of feature names to check
        user: User object or dict with 'user_id' key (optional)

    Returns:
        True if at least one feature is enabled, False otherwise
    """
    return _get_config().is_any_feature_enabled(feature_names, user)


def are_all_features_enabled(
    feature_names: List[str],
    user: Optional[Union[User, Dict[str, str]]] = None
) -> bool:
    """
    Check if all of the given features are enabled.

    Args:
        feature_names: List of feature names to check
        user: User object or dict with 'user_id' key (optional)

    Returns:
        True if all features are enabled, False otherwise
    """
    return _get_config().are_all_features_enabled(feature_names, user)


def get_enabled_features(
    user: Optional[Union[User, Dict[str, str]]] = None
) -> List[str]:
    """
    Get list of all enabled features for the given user.

    Args:
        user: User object or dict with 'user_id' key (optional)

    Returns:
        List of enabled feature names
    """
    return _get_config().get_enabled_features(user)


def get_feature_flags(
    feature_names: List[str],
    user: Optional[Union[User, Dict[str, str]]] = None
) -> Dict[str, bool]:
    """
    Get enabled status for multiple features as a dictionary.

    Args:
        feature_names: List of feature names to check
        user: User object or dict with 'user_id' key (optional)

    Returns:
        Dictionary mapping feature names to their enabled status
    """
    return _get_config().get_feature_flags(feature_names, user)


def feature_exists(feature_name: str) -> bool:
    """
    Check if a feature exists in the configuration.

    Args:
        feature_name: Name of the feature to check

    Returns:
        True if feature exists, False otherwise
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

    Args:
        feature_name: Name of the feature

    Returns:
        Feature configuration dict or None if not found
    """
    return _get_config().get_feature_config(feature_name)
