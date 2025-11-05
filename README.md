# FFXL-P: Feature Flags Extra Light - Python

[![PyPI version](https://badge.fury.io/py/ffxl-p.svg)](https://badge.fury.io/py/ffxl-p)
[![Python Versions](https://img.shields.io/pypi/pyversions/ffxl-p.svg)](https://pypi.org/project/ffxl-p/)
[![CI](https://github.com/yourusername/ffxl-p/workflows/CI/badge.svg)](https://github.com/emilskra/ffxl-p/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, file-based feature flag system for Python applications. This is a Python implementation inspired by the [ffxl](https://github.com/57uff3r/ffxl) TypeScript library.

## Features

- **Time-based activation** - Schedule features to be enabled from a specific date/time (UTC)
- **Gradual rollout** - Enable features for a percentage of users (10%, 50%, 100%, etc.)
- **Environment-based control** - Different rollout percentages per environment
- User-specific feature flag access control
- YAML-based configuration stored locally

#### Frequently Asked Questions (FAQ)
Why are feature flags stored in a file instead of a cloud service?
Because simplicity, speed, and control beat dashboards — at least until you really need one.
FFXL-P was designed for teams who prefer version-controlled infrastructure over vendor lock-in.

By storing flags in a YAML file:
- Flags live with your code — you see, review, and deploy them through Git like everything else.
- Every change is auditable — PR history shows who changed what and why.
- No external dependencies — works offline, no API keys or webhooks required.
- Fully deterministic — any commit, any environment, always predictable behavior.

Think of it like infrastructure-as-code, but for product behavior.

#### Do I really need to redeploy every time I toggle a flag?
Not necessarily.
You can use [scheduled activations](#time-based-activation) and [gradual rollouts](#gradual-rollout-percentage-based) to make changes go live automatically, without manual redeploys.

## Installation

Install from PyPI:

```bash
pip install ffxl-p
```

```bash
uv add ffxl-p
```

## Quick Start

### 1. Create a configuration file

Create `feature-flags.yaml`:

```yaml
features:
  new_dashboard:
    enabled: true
    comment: "New dashboard UI"

  beta_feature:
    enabled: false
    comment: "Beta feature - not ready yet"

  admin_panel:
    onlyForUserIds:
      - "user-123"
      - "user-456"
    comment: "Admin panel - restricted access"

  allow_mock_payments:
    enabled: true
    environments: ["dev"]
    comment: "Mock payments only in development"

  experimental_feature:
    rollout:
      dev: 100
      production: 5
    comment: "Cautious rollout - 5% in production"
```

### 2. Use in your code

```python
from ffxl_p import load_feature_flags, is_feature_enabled, User

# Load configuration
load_feature_flags(environment='production') # or get name of your environment from env variables

# Check global feature
if is_feature_enabled('new_dashboard'):
    print("Show new dashboard")

# Check user-specific feature
user = "user-123"
if is_feature_enabled('admin_panel', user):
    print("Show admin panel")

# Or use a dict
if is_feature_enabled('admin_panel', 'user-456'):
    print("Show admin panel")
```

## Configuration Format

### Global Enabled/Disabled
If feature is disabled then its is off regardless other options. It's global parameter.

```yaml
features:
  feature_name:
    enabled: true  # or false
    comment: "Optional description"
```

### User-Specific Access

```yaml
features:
  feature_name:
    onlyForUserIds:
      - "user-1"
      - "user-2"
    comment: "Only for specific users"
```

When `onlyForUserIds` is present and populated, it takes precedence over the `enabled` setting.

### Environment-Based Access

Control which environments a feature is enabled in:

```yaml
features:
  debug_mode:
    enabled: true
    environments: ["dev"]
    comment: "Only in development"

  staging_feature:
    enabled: true
    environments: ["dev", "staging"]
    comment: "Dev and staging only"

  production_feature:
    enabled: true
    environments: ["production"]
    comment: "Production only"
```

### Time-Based Activation

Control when features are enabled using start and/or end dates (UTC):

```yaml
features:
  # Feature enabled from a specific date
  upcoming_feature:
    enabled: true
    enabledFrom: "2025-12-01T00:00:00Z"
    comment: "Will be enabled on December 1st, 2025"

  # Feature enabled until a specific date
  limited_time_offer:
    enabled: true
    enabledUntil: "2025-12-31T23:59:59Z"
    comment: "Holiday promotion ending December 31st"

  # Feature with a time window (both start and end)
  beta_testing:
    enabled: true
    enabledFrom: "2025-11-15T00:00:00Z"
    enabledUntil: "2025-12-15T00:00:00Z"
    comment: "One-month beta testing period"

  # Combine with environment restrictions
  scheduled_production_release:
    enabled: true
    enabledFrom: "2025-11-20T14:30:00+00:00"
    environments: ["production"]
    comment: "Production release scheduled for November 20th at 2:30 PM UTC"
```

**How it works:**
- Accepts ISO 8601 datetime strings in UTC timezone
- `enabledFrom`: Feature is disabled if current time is before this date
- `enabledUntil`: Feature is disabled if current time is after this date
- Both can be used together to create a time window
- Supports both 'Z' suffix and '+00:00' for UTC timezone
- Time checks are evaluated before environment, rollout, and user restrictions

**Example usage:**
```python
from ffxl_p import load_feature_flags, is_feature_enabled

load_feature_flags()

# Will return False before enabledFrom, True after
if is_feature_enabled('upcoming_feature'):
    show_new_feature()

# Will return True before enabledUntil, False after
if is_feature_enabled('limited_time_offer'):
    show_promotion()

# Will return True only within the time window
if is_feature_enabled('beta_testing'):
    enable_beta_features()
```

### Gradual Rollout (Percentage-Based)

Enable features for a percentage of users in each environment:

```yaml
features:
  new_feature:
    rollout:
      dev: 100        # 100% in dev
      staging: 50     # 50% in staging
      production: 10  # 10% in production
    comment: "Gradual rollout - start small, expand carefully"

  experimental_feature:
    rollout:
      dev: 100
      staging: 25
      production: 5
    comment: "Cautious rollout - 5% in production"
```

**How it works:**
- Uses consistent hashing (SHA256) of `feature_name + user_id`
- Same user always gets same result for same feature
- Different features have independent distributions
- **Requires user** - percentage rollout only works when a user is provided

NOTE: 10% won't mean exactly 10 users out of 100 will get feature, it might be 11 or 9, but statistically over a large number of users it will approximate that.

**Example usage:**
```python
from ffxl_p import load_feature_flags, is_feature_enabled, User

load_feature_flags(environment='production') # or get name of your environment from env variables

user = "user-123"
if is_feature_enabled('new_feature', user):
    # This user is in the 10% rollout group
    show_new_feature()
```

### Combined Restrictions

Combine environment restrictions with percentage rollout:

```yaml
features:
  advanced_feature:
    environments: ["staging", "production"]
    rollout:
      staging: 100    # All users in staging
      production: 25  # 25% of users in production
    comment: "Full staging test, then 25% production rollout"
```

**Priority Order:**
1. Global `enabled` flag check (if `enabled: false`, feature is disabled regardless of other settings)
2. Time-based activation check (if `enabledFrom` and/or `enabledUntil` is specified)
3. Environment check (if `environments` is specified)
4. Percentage rollout (if `rollout` is specified, **requires user**)
5. User-specific list (if `onlyForUserIds` is specified)
6. Global `enabled` flag (defaults to `false` if not specified)

## API Reference

### Loading Configuration

```python
# Load from default location (./feature-flags.yaml)
load_feature_flags()

# Load with explicit environment
load_feature_flags(environment='production')

# Load from custom path
load_feature_flags('./config/flags.yaml', environment='staging')

# Load as JSON string (for environment variables)
config_string = load_feature_flags_as_string()
```

### Feature Checks

```python
# Check single feature
is_feature_enabled('feature_name', user)

# Check if ANY features are enabled
is_any_feature_enabled(['feature1', 'feature2'], user)

# Check if ALL features are enabled
are_all_features_enabled(['feature1', 'feature2'], user)
```

### Getting Features

```python
# Get all enabled features for a user
enabled = get_enabled_features(user)  # Returns: ['feature1', 'feature2']

# Get multiple feature flags as dict
flags = get_feature_flags(['feature1', 'feature2'], user)
# Returns: {'feature1': True, 'feature2': False}
```

### Utility Functions

```python
# Check if feature exists
feature_exists('feature_name')

# Get all feature names
get_all_feature_names()

# Get feature configuration
get_feature_config('feature_name')
```

## Environment Variables

### Custom Configuration File

```bash
# Option 1
export FFXL_FILE=./config/flags.yaml

# Option 2
export FEATURE_FLAGS_FILE=./config/flags.yaml
```

### Configuration via Environment

```bash
# Pass configuration as JSON string
export FFXL_CONFIG='{"features": {"feature1": {"enabled": true}}}'
```

### Set Current Environment

```bash
# Option 1: Use FFXL_ENV
export FFXL_ENV=production

# Option 2: Use generic ENV variable
export ENV=staging

# In code (takes precedence over env variables)
load_feature_flags(environment=os.getenv('ENV', 'local'))
```

### Development Mode

Enable detailed logging:

```bash
export FFXL_DEV_MODE=true
```

## Framework Integration

### Flask

```python
from flask import Flask
from ffxl_p import load_feature_flags, is_feature_enabled
import os

app = Flask(__name__)

# Load at startup
load_feature_flags()

@app.route('/')
def index():
    user = session.get('user_id')
    if is_feature_enabled('new_ui', user):
        return render_template('new_index.html')
    return render_template('old_index.html')
```

### Django

```python
# settings.py
from ffxl_p import load_feature_flags

load_feature_flags('./feature-flags.yaml')

# In views or middleware
from django.conf import settings
from ffxl_p import is_feature_enabled

def my_view(request):
    if is_feature_enabled('new_feature', request.user.id):
        # Use new feature
        pass
```

### FastAPI

```python
from fastapi import FastAPI, Depends
from ffxl_p import load_feature_flags, is_feature_enabled

app = FastAPI()

# Load at startup
@app.on_event("startup")
async def startup_event():
    load_feature_flags()

@app.get("/dashboard")
async def dashboard(user_id: str): # it's just an example, validate provided user_id properly in real code
    if is_feature_enabled('new_dashboard', user_id):
        return {"version": "new"}
    return {"version": "old"}
```

## Examples

See [example.py](ffxl_p/example.py)example.py, [example_environments.py](ffxl_p/example_environments.py) and [example_rollout.py](ffxl_p/example_rollout.py) for comprehensive usage examples

## Development

Run with development mode for detailed logging:

```bash
FFXL_DEV_MODE=true python example.py
```

## License

This is a Python port inspired by [ffxl](https://github.com/57uff3r/ffxl). Please check the original repository for license information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
