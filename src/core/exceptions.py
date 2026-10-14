from fastapi import HTTPException, status


def err_400_user_already_exists(message: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Пользователь с почтой {message} уже существует [ID-1]",
    )
