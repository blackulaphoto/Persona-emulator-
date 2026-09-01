from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.preview_access import enforce_preview_persona_limit, is_preview_limit_exempt


def database_with_count(count: int):
    db = MagicMock()
    db.query.return_value.filter.return_value.count.return_value = count
    return db


def test_normal_preview_user_remains_limited(monkeypatch):
    monkeypatch.setattr(settings, "preview_limit_exempt_user_ids_raw", "owner-uid")
    with patch("app.services.preview_access.is_dev_auth_bypass_active", return_value=False):
        with pytest.raises(HTTPException) as error:
            enforce_preview_persona_limit(database_with_count(3), "public-user-uid")

    assert error.value.status_code == 403
    assert "Maximum 3 personas" in error.value.detail


def test_server_allowlisted_owner_is_not_limited(monkeypatch):
    monkeypatch.setattr(settings, "preview_limit_exempt_user_ids_raw", "owner-uid, admin-uid")
    db = database_with_count(50)
    with patch("app.services.preview_access.is_dev_auth_bypass_active", return_value=False):
        enforce_preview_persona_limit(db, "owner-uid")

    db.query.assert_not_called()


def test_frontend_role_text_cannot_grant_bypass(monkeypatch):
    monkeypatch.setattr(settings, "preview_limit_exempt_user_ids_raw", "owner-uid")
    with patch("app.services.preview_access.is_dev_auth_bypass_active", return_value=False):
        assert is_preview_limit_exempt("owner=true&role=admin") is False
        with pytest.raises(HTTPException):
            enforce_preview_persona_limit(database_with_count(3), "owner=true&role=admin")


def test_gated_local_dev_identity_is_exempt(monkeypatch):
    monkeypatch.setattr(settings, "preview_limit_exempt_user_ids_raw", None)
    with patch("app.services.preview_access.is_dev_auth_bypass_active", return_value=True):
        assert is_preview_limit_exempt("dev-local-user") is True
        assert is_preview_limit_exempt("public-user-uid") is False
