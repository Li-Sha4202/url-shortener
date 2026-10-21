from fastapi import HTTPException, status


def err_400_user_already_exists(message: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Пользователь с почтой {message} уже существует [ID-1]",
    )


def err_401_not_authentificated():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверная почта или пароль [ID-2]",
        headers={"WWW-Authenticate": "Bearer"},
    )


def err_401_not_validate_credentials():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials [ID-3]",
        headers={"WWW-Authenticate": "Bearer"},
    )
