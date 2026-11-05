import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from jose import JWTError

from src.core.security.jwt_token import create_access_token, decode_access_token


@pytest.fixture
def mock_settings():
    """Мок конфигурации JWT."""
    with patch("src.core.security.jwt_token.settings") as mock:
        mock.jwt.SECRET_KEY = "test_secret_key"
        mock.jwt.ALGORITHM = "HS256"
        mock.jwt.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        yield mock


class TestCreateAccessToken:

    def test_returns_string(self, mock_settings):
        """Токен должен быть строкой."""
        token = create_access_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_id(self, mock_settings):
        """В payload должен быть sub = user_id."""
        token = create_access_token(user_id=42)
        payload = decode_access_token(token)
        assert payload["sub"] == "42"

    def test_token_has_required_claims(self, mock_settings):
        """Токен должен содержать sub, exp, iat, type."""
        token = create_access_token(user_id=1)
        payload = decode_access_token(token)
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "type" in payload

    def test_token_type_is_access(self, mock_settings):
        """type должен быть "access"."""
        token = create_access_token(user_id=1)
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_expiration_is_after_issued(self, mock_settings):
        """exp должен быть позже iat."""
        token = create_access_token(user_id=1)
        payload = decode_access_token(token)
        assert payload["exp"] > payload["iat"]

    def test_default_expiration_is_30_minutes(self, mock_settings):
        """По умолчанию токен живёт 30 минут."""
        token = create_access_token(user_id=1)
        payload = decode_access_token(token)
        delta = payload["exp"] - payload["iat"]
        assert delta == 1800  # 30 минут в секундах

    def test_custom_expire_delta(self, mock_settings):
        """Кастомный expire_delta должен использоваться."""
        delta = timedelta(hours=1)
        token = create_access_token(user_id=1, expire_delta=delta)
        payload = decode_access_token(token)
        diff = payload["exp"] - payload["iat"]
        assert diff == 3600  # 1 час в секундах

    def test_different_tokens_have_different_iat(self, mock_settings):
        """Два токена, созданные в разное время, должны иметь разные iat."""
        token1 = create_access_token(user_id=1)
        import time

        time.sleep(0.1)
        token2 = create_access_token(user_id=1)
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        assert payload1["iat"] != payload2["iat"]

    def test_different_user_ids(self, mock_settings):
        """Токены для разных user_id должны иметь разные sub."""
        token1 = create_access_token(user_id=1)
        token2 = create_access_token(user_id=999)
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        assert payload1["sub"] != payload2["sub"]
        assert payload1["sub"] == "1"
        assert payload2["sub"] == "999"


class TestDecodeAccessToken:

    def test_decodes_valid_token(self, mock_settings):
        """Валидный токен должен успешно декодироваться."""
        token = create_access_token(user_id=1)
        payload = decode_access_token(token)
        assert isinstance(payload, dict)

    def test_raises_on_invalid_token(self, mock_settings):
        """Невалидный токен должен вызывать исключение."""
        with pytest.raises(JWTError):
            decode_access_token("invalid.token.here")

    def test_raises_on_tampered_token(self, mock_settings):
        """Изменённый токен должен вызывать исключение."""
        token = create_access_token(user_id=1)
        # Меняем последний символ
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_raises_with_wrong_secret(self, mock_settings):
        """Токен, созданный с другим секретом, не должен декодироваться."""
        token = create_access_token(user_id=1)
        # Временная замена секретного ключа
        mock_settings.jwt.SECRET_KEY = "wrong_secret_key"
        with pytest.raises(JWTError):
            decode_access_token(token)
