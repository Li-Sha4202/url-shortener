from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Абстрактная модель для создания других моделей БД"""

    abstract = True
