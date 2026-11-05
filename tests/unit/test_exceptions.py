import pytest
from unittest.mock import patch

from fastapi import HTTPException

from src.core.exceptions import (
    err_400_user_already_exists,
    err_401_not_authentificated,
    err_401_not_validate_credentials,
    err_400_requied_current_password,
    err_400_invalid_password,
    err_400_bad_req_exp_link,
    err_400_reserved_codes,
    err_400_code_exists_in_db,
    err_404_link_not_found,
    err_403_not_admin,
)


class TestExceptions:
    """Тесты подготовленных ошибок"""

    def test_err_401_not_validate_credentials(self):
        """Тест 401 ошибки на валидацию данных"""
        with pytest.raises(HTTPException) as exc_info:
            err_401_not_validate_credentials()

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
        assert exc_info.value.headers.get("WWW-Authenticate") == "Bearer"  # type: ignore

    def test_err_404_link_not_found(self):
        """Тест 404 ошибки - ссылка не найдена"""
        with pytest.raises(HTTPException) as exc_info:
            err_404_link_not_found("abc123")

        assert exc_info.value.status_code == 404
        assert (
            f'Короткая ссылка - "{"abc123"}" - которую вы пытались открыть, не найдена'
            in exc_info.value.detail
        )

    def test_err_400_bad_req_exp_link(self):
        """Тест 400 ошибки - срок жизни ссылки закончилось"""
        with pytest.raises(HTTPException) as exc_info:
            err_400_bad_req_exp_link()

        assert exc_info.value.status_code == 400
        assert "Срок ссылки истечён [ID-6]" in exc_info.value.detail

    def test_err_400_code_exists_in_db(self):
        """Тест 400 ошибки - Ссылка {Код ссылки} уже используется"""
        with pytest.raises(HTTPException) as exc_info:
            err_400_code_exists_in_db("abc123")

        assert exc_info.value.status_code == 400
        assert "abc123 - код занят [ID-8]" in exc_info.value.detail

    def test_err_400_requied_current_password(self):
        """Тест 400 ошибки - при обновлении данных пользователя должен быть указан текущий пароль"""
        with pytest.raises(HTTPException) as exc_info:
            err_400_requied_current_password()

        assert exc_info.value.status_code == 400
        assert (
            "Требуется ввести пароль для обновления почты [ID-4]"
            in exc_info.value.detail
        )

    def test_err_403_not_admin(self):
        """Тест 403 ошибки - Пользователь должен быть админом"""
        with pytest.raises(HTTPException) as exc_info:
            err_403_not_admin()

        assert exc_info.value.status_code == 403
        assert "Отсутствуют права администратора" in exc_info.value.detail
