"""
Tests for app/core/config.py's fail-closed production database requirement.

Root cause this guards against, confirmed live in production: a real
Postgres service was provisioned in the Railway project but never actually
referenced by the backend service (no DATABASE_URL variable at all), so
Settings() silently fell back to its old hardcoded default,
"sqlite:///./dev.db" - a file on the deploy container's own ephemeral
filesystem, with no persistent volume. Every redeploy silently lost all
production data. This was never surfaced as an error anywhere - the app
started up fine, served requests fine, and just quietly used a database
that could vanish on the next deploy.

_resolve_database_url's job: DEVELOPMENT/TEST may still fall back to local
SQLite when DATABASE_URL is unset (unchanged local-dev behavior). PRODUCTION
must fail application startup loudly and immediately when DATABASE_URL is
unset, rather than silently defaulting to that same ephemeral SQLite path.
"""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(**overrides) -> Settings:
    # _env_file=None: never read a local backend/.env in these tests - the
    # whole point is to control DATABASE_URL/ENVIRONMENT explicitly and
    # deterministically, regardless of what a developer's machine has.
    return Settings(_env_file=None, **overrides)


class TestDevelopmentAndTestFallBackToSqlite:
    def test_development_without_database_url_uses_sqlite(self):
        settings = _settings(environment="development", database_url=None)
        assert settings.database_url == "sqlite:///./dev.db"

    def test_test_environment_without_database_url_uses_sqlite(self):
        settings = _settings(environment="test", database_url=None)
        assert settings.database_url == "sqlite:///./dev.db"

    def test_development_with_explicit_database_url_is_unchanged(self):
        # An explicit override (e.g. a developer pointing local dev at a
        # real Postgres instance) is never silently replaced.
        settings = _settings(environment="development", database_url="postgresql://localhost/dev")
        assert settings.database_url == "postgresql://localhost/dev"


class TestProductionFailsClosedWithoutDatabaseUrl:
    def test_production_without_database_url_raises_at_construction(self):
        with pytest.raises(ValidationError) as exc:
            _settings(environment="production", database_url=None)
        assert "DATABASE_URL is required when ENVIRONMENT=production" in str(exc.value)

    def test_production_error_names_the_ephemeral_sqlite_risk(self):
        # The error message itself must explain *why*, not just fail
        # silently with a generic validation error - this is the thing a
        # future engineer sees in a crashed deploy's logs.
        with pytest.raises(ValidationError) as exc:
            _settings(environment="production", database_url=None)
        assert "sqlite:///./dev.db" in str(exc.value)
        assert "ephemeral" in str(exc.value)

    def test_production_case_and_whitespace_insensitive(self):
        # ENVIRONMENT is a free-text env var in practice - don't let a
        # trailing space or different case silently bypass the guard.
        with pytest.raises(ValidationError):
            _settings(environment=" Production ", database_url=None)

    def test_production_with_empty_string_database_url_also_fails(self):
        # An explicitly-set-but-empty DATABASE_URL (e.g. a misconfigured
        # reference variable resolving to "") must be treated the same as
        # unset - never coerced into truthy "looks configured".
        with pytest.raises(ValidationError):
            _settings(environment="production", database_url="")


class TestProductionWithRealDatabaseUrlSucceeds:
    def test_production_with_postgres_database_url_succeeds(self):
        settings = _settings(
            environment="production",
            database_url="postgresql://user:pass@host:5432/railway",
        )
        assert settings.database_url == "postgresql://user:pass@host:5432/railway"

    def test_production_database_url_is_never_silently_replaced_with_sqlite(self):
        settings = _settings(
            environment="production",
            database_url="postgresql://user:pass@host:5432/railway",
        )
        assert "sqlite" not in settings.database_url


class TestDatabaseEngineNeverSilentlyDefaultsProductionToSqlite:
    def test_database_module_import_fails_when_production_env_vars_are_set_and_database_url_is_missing(self, monkeypatch):
        # End-to-end proof at the actual import boundary app/core/database.py
        # relies on: constructing the real module-level Settings() the app
        # boots with, under production env vars and no DATABASE_URL, must
        # raise - not silently produce a sqlite engine.
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
