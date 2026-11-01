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


def err_400_requied_current_password():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Требуется ввести пароль для обновления почты [ID-4]",
    )


def err_400_invalid_password():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Неверный пароль [ID-5]",
    )


def err_400_bad_req_exp_link():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Срок ссылки истечён [ID-6]",
    )


def err_400_reserved_codes(code_name):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{code_name} уже занят [ID-7]",
    )


def err_400_code_exists_in_db(code_name):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{code_name} - код занят [ID-8]",
    )


def err_404_link_not_found(code_name):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'Короткая ссылка - "{code_name}" - которую вы пытались открыть, не найдена',
    )
