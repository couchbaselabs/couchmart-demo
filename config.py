import os
import settings

# Create a class to hold configuration
class Config:
    def __init__(self):
        # Load defaults from settings.py
        for key in dir(settings):
            if key.isupper():
                setattr(self, key, getattr(settings, key))

        # Override with environment variables
        self._override_from_env()

    def _override_from_env(self):
        # List of keys that should be treated as lists (comma separated)
        list_keys = ['AWS_NODES']
        # List of keys that should be treated as booleans
        bool_keys = ['AWS']

        for key in dir(settings):
            if key.isupper():
                env_val = os.getenv(key)
                if env_val is not None:
                    if key in list_keys:
                        setattr(self, key, env_val.split(','))
                    elif key in bool_keys:
                        setattr(self, key, env_val.lower() == 'true')
                    else:
                        setattr(self, key, env_val)

# Instantiate the config
config = Config()

# Expose attributes at module level for easy import (e.g. from config import BUCKET_NAME)
# This allows 'import config as settings' to work seamlessly
import sys
this_module = sys.modules[__name__]
for key in dir(config):
    if key.isupper():
        setattr(this_module, key, getattr(config, key))
