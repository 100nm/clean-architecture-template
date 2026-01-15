ARG PYTHON_VERSION="3.14"

# Python
FROM python:${PYTHON_VERSION}-slim

# Working directory
WORKDIR /app
COPY ./src/ ./src/
COPY ./alembic.ini .
COPY ./main.py .
COPY ./pyproject.toml .
COPY ./uv.lock .

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1
ENV UV_PYTHON_PREFERENCE="only-system"
ENV UVICORN_HOST="0.0.0.0"

# Update system dependencies
RUN apt-get upgrade -y
RUN apt-get update

# Intall dependencies
RUN pip install --no-cache-dir --upgrade pip uv
RUN uv export --frozen --no-default-groups > requirements.txt
RUN uv pip install -r requirements.txt --system

# Cleaning
RUN apt-get autoremove
RUN apt-get clean

EXPOSE ${UVICORN_PORT:-8000}

ENTRYPOINT ["uvicorn", "main:app", "--loop", "uvloop"]
