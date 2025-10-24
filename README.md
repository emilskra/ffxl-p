# FFXL-P: Feature Flags Extra Light - Python

A lightweight, file-based feature flag system for Python applications. This is a Python implementation inspired by the [ffxl](https://github.com/57uff3r/ffxl) TypeScript library.

## Features

- Zero external dependencies (except PyYAML)
- YAML-based configuration stored locally
- User-specific feature flag access control
- Development mode with informative logging
- Simple, intuitive API
- Type hints support

## Installation

Install the required dependency:

```bash
pip install pyyaml
```

Copy `ffxl.py` to your project.

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
```

### 2. Use in your code

```python
from ffxl import load_feature_flags, is_feature_enabled, User

# Load configuration
load_feature_flags()

# Check global feature
if is_feature_enabled('new_dashboard'):
    print("Show new dashboard")

# Check user-specific feature
user = User(user_id="user-123")
if is_feature_enabled('admin_panel', user):
    print("Show admin panel")

# Or use a dict
if is_feature_enabled('admin_panel', {'user_id': 'user-456'}):
    print("Show admin panel")
```

## Configuration Format

### Global Enabled/Disabled

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

## API Reference

### Loading Configuration

```python
# Load from default location (./feature-flags.yaml)
load_feature_flags()

# Load from custom path
load_feature_flags('./config/flags.yaml')

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

### Development Mode

Enable detailed logging:

```bash
export FFXL_DEV_MODE=true
```

## Framework Integration

### Flask

```python
from flask import Flask
from ffxl import load_feature_flags, is_feature_enabled
import os

app = Flask(__name__)

# Load at startup
config = load_feature_flags()
app.config['FFXL_CONFIG'] = config

@app.route('/')
def index():
    user = {'user_id': session.get('user_id')}
    if is_feature_enabled('new_ui', user):
        return render_template('new_index.html')
    return render_template('old_index.html')
```

### Django

```python
# settings.py
from ffxl import load_feature_flags

FEATURE_FLAGS = load_feature_flags('./feature-flags.yaml')

# In views or middleware
from django.conf import settings
from ffxl import is_feature_enabled

def my_view(request):
    user = {'user_id': request.user.id}
    if is_feature_enabled('new_feature', user):
        # Use new feature
        pass
```

### FastAPI

```python
from fastapi import FastAPI, Depends
from ffxl import load_feature_flags, is_feature_enabled

app = FastAPI()

# Load at startup
@app.on_event("startup")
async def startup_event():
    load_feature_flags()

@app.get("/dashboard")
async def dashboard(user_id: str):
    user = {'user_id': user_id}
    if is_feature_enabled('new_dashboard', user):
        return {"version": "new"}
    return {"version": "old"}
```

## User Object

You can pass either a `User` object or a dictionary:

```python
from ffxl import User

# Using User class
user = User(user_id="123")
is_feature_enabled('feature', user)

# Using dict
is_feature_enabled('feature', {'user_id': '123'})
```

## Examples

See `example.py` for comprehensive usage examples:

```bash
python example.py
```

## Development

Run with development mode for detailed logging:

```bash
FFXL_DEV_MODE=true python example.py
```

## Comparison with TypeScript Version

This Python implementation maintains API parity with the original TypeScript [ffxl](https://github.com/57uff3r/ffxl) library:

| Feature | TypeScript | Python |
|---------|-----------|---------|
| YAML Config | Yes | Yes |
| User-specific flags | Yes | Yes |
| Dev mode logging | Yes | Yes |
| Environment config | Yes | Yes |
| Zero dependencies* | Yes | Yes** |

\* Except for runtime (Node.js/Deno) and build tools
\*\* Except PyYAML for YAML parsing

## License

This is a Python port inspired by [ffxl](https://github.com/57uff3r/ffxl). Please check the original repository for license information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
