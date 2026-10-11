FROM python:3.13.2-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --upgrade pip wheel "poetry==2.4.1"
RUN poetry config virtualenvs.create false

COPY pyproject.toml ./
COPY poetry.lock ./

RUN poetry install --no-root

COPY . . 


CMD ["python", "/app/src/main.py"]