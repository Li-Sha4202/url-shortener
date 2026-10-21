from pydantic import BaseModel


class Token(BaseModel):  # зачем?
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None  # как не может быть ID?
