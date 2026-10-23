from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

# Сам хэшер паролей
ph = PasswordHasher()

# Создаём "пустой" хэш для защиты от timing-атак.
# Он нужен, чтобы время проверки неверного пароля было таким же,
# как и время проверки для несуществующего пользователя.
DUMMY_HASH = ph.hash("dummy_password_for_timing_attack_protection")


def password_hash(password: str) -> str:
    """Возвращает хэшированный пароль"""
    return ph.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """
    Проверяет, соответствует ли пароль хэшу.
    Возвращает True или False.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        return False


def check_needs_rehash(hashed_password) -> bool:
    """
    Проверяет, нужно ли перехэшировать пароль,
    например, если изменили параметры хэшера.
    """
    return ph.check_needs_rehash(hashed_password)
