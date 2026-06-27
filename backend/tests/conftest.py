import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-please-change")
os.environ.setdefault("POSTGRES_USER", "upwork")
os.environ.setdefault("POSTGRES_PASSWORD", "upwork")
os.environ.setdefault("POSTGRES_DB", "upwork_intel_test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("ENVIRONMENT", "test")
