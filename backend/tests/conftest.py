import os
import tempfile

# Configure a throwaway environment BEFORE the app (and its settings) is imported.
os.environ.setdefault("ENVIRONMENT", "test")
_TMP = tempfile.mkdtemp(prefix="opsledger_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789abcdef"
os.environ["UPLOAD_DIR"] = os.path.join(_TMP, "uploads")
os.environ["CORS_ORIGINS"] = "http://localhost"
