"""Configuration commune aux tests Flask."""

import os

os.environ["SECRET_KEY"] = "test-only-secret-key-not-for-production"
os.environ.pop("RENDER", None)
