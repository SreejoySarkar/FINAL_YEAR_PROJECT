import os
import tempfile
from pathlib import Path

os.environ["DJANGO_DEBUG"] = "True"
os.environ["USE_P1_STUB"] = "True"

from .settings import *  # noqa: E402,F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
PAILLIER_KEY_BITS = 512          # tests only - never below 2048 in production
KEY_STORE_DIR = Path(tempfile.mkdtemp(prefix="evoting-test-keys-"))
ELECTION_KEY_PASSPHRASE = "test-passphrase"
ENABLE_DEMO_ENDPOINTS = True
MIN_RING_SIZE = 3
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"user": "100000/min", "public": "100000/min", "submit": "100000/min"},
}
