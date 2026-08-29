"""
Shared pytest configuration for the backend test suite.

Sets AUTH_DEV_BYPASS=true before any test module imports app.core.auth (and
therefore before its Firebase Admin SDK init runs), so the existing
route-level tests that exercise real HTTP requests through TestClient(app) -
without overriding the get_current_user dependency - keep authenticating as
the fixed local dev user, exactly as they did before AUTH_DEV_BYPASS became
an explicit opt-in flag (see app/core/auth.py::compute_dev_bypass_enabled).
Top-level code in conftest.py runs before pytest imports any test module, so
this is early enough.

Test-only: a real deployment never sets AUTH_DEV_BYPASS, so every request
there is verified for real (or runs against the Firebase Auth Emulator -
see backend/.env.example).

Also explicitly clears any real Firebase config a developer's local
backend/.env might happen to have (app/core/auth.py now calls
load_dotenv(), so without this the test suite's auth behavior would depend
on whatever's sitting in that file / whether a local emulator happens to be
running - not reproducible). The test suite always exercises the dev-bypass
path, deterministically, regardless of local machine state.
"""
import os

for _leaky_var in ("FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_AUTH_EMULATOR_HOST", "GCLOUD_PROJECT"):
    os.environ.pop(_leaky_var, None)

os.environ.setdefault("AUTH_DEV_BYPASS", "true")
os.environ.setdefault("ENVIRONMENT", "development")
